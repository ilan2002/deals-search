"""Product search over the database.

Uses plain SQL filters so it runs on SQLite and Postgres alike. Once the catalogue
grows, move text search to Meilisearch/Typesense/OpenSearch and keep these filters.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Listing, ListingSize, Product
from app.stores import Store
from app.taxonomy import descendants


class Gender(StrEnum):
    MEN = "men"
    WOMEN = "women"
    KIDS = "kids"
    UNISEX = "unisex"


class SortOrder(StrEnum):
    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    DISCOUNT = "discount"
    RATING = "rating"
    NEWEST = "newest"


@dataclass
class SearchFilters:
    q: str | None = None
    category: str | None = None
    stores: list[Store] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    gender: Gender | None = None
    colors: list[str] = field(default_factory=list)
    sizes: list[str] = field(default_factory=list)
    min_price: int | None = None  # paise
    max_price: int | None = None  # paise
    min_discount: int | None = None
    in_stock_only: bool = True


@dataclass
class SearchHit:
    product: Product
    best_price: int
    best_discount: int


def _contains(column, text: str):
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


def search_products(
    session: Session,
    filters: SearchFilters,
    sort: SortOrder = SortOrder.RELEVANCE,
    page: int = 1,
    page_size: int = 24,
) -> tuple[list[SearchHit], int]:
    # Listing-level filters decide which offers count; a product matches if any offer does.
    listing_conds = []
    if filters.stores:
        listing_conds.append(Listing.store.in_(filters.stores))
    if filters.in_stock_only:
        listing_conds.append(Listing.in_stock.is_(True))
    if filters.min_price is not None:
        listing_conds.append(Listing.price >= filters.min_price)
    if filters.max_price is not None:
        listing_conds.append(Listing.price <= filters.max_price)
    if filters.min_discount is not None:
        listing_conds.append(Listing.discount_pct >= filters.min_discount)
    if filters.sizes:
        listing_conds.append(
            Listing.id.in_(select(ListingSize.listing_id).where(ListingSize.size.in_(filters.sizes)))
        )

    best = (
        select(
            Listing.product_id.label("product_id"),
            func.min(Listing.price).label("best_price"),
            func.max(Listing.discount_pct).label("best_discount"),
            func.max(Listing.rating).label("best_rating"),
        )
        .where(*listing_conds)
        .group_by(Listing.product_id)
        .subquery()
    )

    product_conds = []
    if filters.category:
        product_conds.append(Product.category.in_(descendants(filters.category)))
    if filters.brands:
        product_conds.append(func.lower(Product.brand).in_([b.lower() for b in filters.brands]))
    if filters.gender in (Gender.MEN, Gender.WOMEN):
        product_conds.append(Product.gender.in_([filters.gender, Gender.UNISEX]))
    elif filters.gender:
        product_conds.append(Product.gender == filters.gender)
    if filters.colors:
        product_conds.append(Product.color.in_([c.lower() for c in filters.colors]))
    q = (filters.q or "").strip()
    for token in q.split():
        product_conds.append(or_(_contains(Product.title, token), _contains(Product.brand, token)))

    stmt = (
        select(Product, best.c.best_price, best.c.best_discount)
        .join(best, best.c.product_id == Product.id)
        .where(*product_conds)
    )
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == SortOrder.PRICE_ASC:
        order = [best.c.best_price.asc()]
    elif sort == SortOrder.PRICE_DESC:
        order = [best.c.best_price.desc()]
    elif sort == SortOrder.DISCOUNT:
        order = [best.c.best_discount.desc()]
    elif sort == SortOrder.RATING:
        order = [best.c.best_rating.desc().nulls_last()]
    elif sort == SortOrder.NEWEST:
        order = [Product.created_at.desc()]
    else:
        # Until a real search engine is in place: exact phrase matches first, then biggest discount.
        order = [case((_contains(Product.title, q), 0), else_=1)] if q else []
        order.append(best.c.best_discount.desc())
    order.append(Product.id)

    rows = session.execute(
        stmt.options(selectinload(Product.listings).selectinload(Listing.sizes))
        .order_by(*order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [SearchHit(product, best_price, best_discount) for product, best_price, best_discount in rows], total
