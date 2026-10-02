from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.ingestion.normalize import normalize_size
from app.models import Listing, Product
from app.schemas import (
    CategoryOut,
    ListingDetailOut,
    ListingOut,
    PricePointOut,
    ProductDetailOut,
    ProductOut,
    SearchResponse,
    StoreOut,
    rupees,
)
from app.search import Gender, SearchFilters, SortOrder, search_products
from app.stores import STORE_NAMES, Store
from app.taxonomy import CATEGORIES, children

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


def _paise(rupees_value: float | None) -> int | None:
    return None if rupees_value is None else round(rupees_value * 100)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/stores", response_model=list[StoreOut])
def list_stores():
    return [StoreOut(id=store, name=name) for store, name in STORE_NAMES.items()]


@router.get("/categories", response_model=list[CategoryOut])
def list_categories():
    def build(slug: str | None) -> list[CategoryOut]:
        return [CategoryOut(slug=c.slug, name=c.name, try_on=c.try_on, children=build(c.slug)) for c in children(slug)]

    return build(None)


@router.get("/products", response_model=SearchResponse)
def search(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=200)] = None,
    category: str | None = None,
    store: Annotated[list[Store] | None, Query()] = None,
    brand: Annotated[list[str] | None, Query()] = None,
    gender: Gender | None = None,
    color: Annotated[list[str] | None, Query()] = None,
    size: Annotated[list[str] | None, Query()] = None,
    min_price: Annotated[float | None, Query(ge=0, description="Rupees")] = None,
    max_price: Annotated[float | None, Query(ge=0, description="Rupees")] = None,
    min_discount: Annotated[int | None, Query(ge=0, le=100)] = None,
    include_out_of_stock: bool = False,
    sort: SortOrder = SortOrder.RELEVANCE,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
):
    """Search products across all stores. For a deals feed: `?sort=discount&min_discount=40`."""
    if category is not None and category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")

    filters = SearchFilters(
        q=q,
        category=category,
        stores=store or [],
        brands=brand or [],
        gender=gender,
        colors=color or [],
        sizes=[normalize_size(s) for s in size or []],
        min_price=_paise(min_price),
        max_price=_paise(max_price),
        min_discount=min_discount,
        in_stock_only=not include_out_of_stock,
    )
    hits, total = search_products(session, filters, sort, page, page_size)
    items = [
        ProductOut.from_model(
            hit.product, hit.best_price, hit.best_discount, [ListingOut.from_model(l) for l in hit.product.listings]
        )
        for hit in hits
    ]
    return SearchResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/products/{product_id}", response_model=ProductDetailOut)
def get_product(product_id: int, session: SessionDep):
    product = session.get(
        Product,
        product_id,
        options=[
            selectinload(Product.listings).selectinload(Listing.sizes),
            selectinload(Product.listings).selectinload(Listing.price_history),
        ],
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    offers = [l for l in product.listings if l.in_stock] or product.listings
    best = min(offers, key=lambda l: l.price)
    listings = [
        ListingDetailOut.from_model(
            l, price_history=[PricePointOut(price=rupees(p.price), recorded_at=p.recorded_at) for p in l.price_history]
        )
        for l in product.listings
    ]
    return ProductDetailOut.from_model(product, best.price, best.discount_pct, listings)
