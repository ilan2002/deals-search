from datetime import datetime

from pydantic import BaseModel

from app.models import Listing, Product
from app.stores import STORE_NAMES, Store
from app.taxonomy import CATEGORIES, TryOn


def rupees(paise: int | None) -> float | None:
    return None if paise is None else paise / 100


class PricePointOut(BaseModel):
    price: float
    recorded_at: datetime


class ListingOut(BaseModel):
    store: Store
    store_name: str
    price: float
    mrp: float | None
    discount_pct: int
    url: str  # affiliate-tagged link to the store
    in_stock: bool
    sizes: list[str]
    rating: float | None
    rating_count: int | None
    last_seen_at: datetime

    @classmethod
    def from_model(cls, listing: Listing, **extra) -> "ListingOut":
        store = Store(listing.store)
        return cls(
            store=store,
            store_name=STORE_NAMES[store],
            price=rupees(listing.price),
            mrp=rupees(listing.mrp),
            discount_pct=listing.discount_pct,
            url=listing.affiliate_url,
            in_stock=listing.in_stock,
            sizes=[s.size for s in listing.sizes],
            rating=listing.rating,
            rating_count=listing.rating_count,
            last_seen_at=listing.last_seen_at,
            **extra,
        )


class ListingDetailOut(ListingOut):
    price_history: list[PricePointOut]


class ProductOut(BaseModel):
    id: int
    title: str
    brand: str | None
    category: str
    category_name: str
    gender: str | None
    color: str | None
    image_url: str | None
    try_on: TryOn  # whether the Phase 3 try-on can show this item
    best_price: float
    best_discount_pct: int
    listings: list[ListingOut]

    @classmethod
    def from_model(cls, product: Product, best_price: int, best_discount: int, listings: list[ListingOut]):
        category = CATEGORIES.get(product.category, CATEGORIES["other"])
        return cls(
            id=product.id,
            title=product.title,
            brand=product.brand,
            category=category.slug,
            category_name=category.name,
            gender=product.gender,
            color=product.color,
            image_url=product.image_url,
            try_on=category.try_on,
            best_price=rupees(best_price),
            best_discount_pct=best_discount,
            listings=listings,
        )


class ProductDetailOut(ProductOut):
    listings: list[ListingDetailOut]


class SearchResponse(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class CategoryOut(BaseModel):
    slug: str
    name: str
    try_on: TryOn
    children: list["CategoryOut"] = []


class StoreOut(BaseModel):
    id: Store
    name: str
