from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    """A canonical item. The same product sold on several stores shares one row."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Brand + model number when the feed gives one, else "<store>:<store id>".
    match_key: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    gender: Mapped[str | None] = mapped_column(String(16), index=True)
    color: Mapped[str | None] = mapped_column(String(32), index=True)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    listings: Mapped[list["Listing"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="Listing.price"
    )


class Listing(Base):
    """One store's offer for a product. Prices are stored in paise."""

    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("store", "store_product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    store: Mapped[str] = mapped_column(String(16), index=True)
    store_product_id: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(2000))
    affiliate_url: Mapped[str] = mapped_column(String(2000))
    price: Mapped[int] = mapped_column(index=True)
    mrp: Mapped[int | None]
    discount_pct: Mapped[int] = mapped_column(default=0, index=True)
    in_stock: Mapped[bool] = mapped_column(default=True)
    rating: Mapped[float | None]
    rating_count: Mapped[int | None]
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    product: Mapped[Product] = relationship(back_populates="listings")
    sizes: Mapped[list["ListingSize"]] = relationship(cascade="all, delete-orphan")
    price_history: Mapped[list["PricePoint"]] = relationship(
        cascade="all, delete-orphan", order_by="PricePoint.recorded_at"
    )


class ListingSize(Base):
    __tablename__ = "listing_sizes"

    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), primary_key=True)
    size: Mapped[str] = mapped_column(String(16), primary_key=True, index=True)


class PricePoint(Base):
    """Recorded whenever a listing's price changes."""

    __tablename__ = "price_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    price: Mapped[int]
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
