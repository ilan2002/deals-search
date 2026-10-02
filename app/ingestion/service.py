import logging
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.ingestion.base import RawListing
from app.ingestion.normalize import (
    affiliate_url,
    classify_category,
    detect_color,
    detect_gender,
    discount_pct,
    match_key,
    normalize_size,
    parse_price,
)
from app.models import Listing, ListingSize, PricePoint, Product, utcnow
from app.taxonomy import descendants

logger = logging.getLogger(__name__)

_FASHION = descendants("fashion")


@dataclass
class IngestStats:
    created: int = 0
    updated: int = 0
    price_changes: int = 0
    skipped: int = 0


def _get_or_create_product(session: Session, raw: RawListing) -> Product:
    key = match_key(raw.store, raw.store_product_id, raw.brand, raw.model_number)
    product = session.scalar(select(Product).where(Product.match_key == key))
    if product is not None:
        product.image_url = product.image_url or raw.image_url
        return product

    category = classify_category(raw.title, raw.category_hint)
    gender_text = " ".join(filter(None, [raw.category_hint, raw.title]))
    product = Product(
        match_key=key,
        title=raw.title.strip(),
        brand=raw.brand.strip() if raw.brand else None,
        category=category,
        gender=detect_gender(gender_text) if category in _FASHION else None,
        color=detect_color(raw.color or "") or detect_color(raw.title),
        image_url=raw.image_url,
        attributes=dict(raw.attributes),
    )
    session.add(product)
    return product


def _sync_sizes(listing: Listing, sizes: Iterable[str]) -> None:
    wanted = {normalize_size(s) for s in sizes if s.strip()}
    existing = {s.size: s for s in listing.sizes}
    for size, row in existing.items():
        if size not in wanted:
            listing.sizes.remove(row)
    for size in sorted(wanted - existing.keys()):
        listing.sizes.append(ListingSize(size=size))


def ingest(session: Session, items: Iterable[RawListing], settings: Settings | None = None) -> IngestStats:
    """Upsert listings by (store, store_product_id) and record price changes."""
    settings = settings or get_settings()
    stats = IngestStats()
    now = utcnow()

    for raw in items:
        try:
            price = parse_price(raw.price)
            mrp = parse_price(raw.mrp)
        except ValueError as exc:
            logger.warning("Skipping %s/%s: %s", raw.store, raw.store_product_id, exc)
            stats.skipped += 1
            continue
        if price is None:
            logger.warning("Skipping %s/%s: no price", raw.store, raw.store_product_id)
            stats.skipped += 1
            continue

        listing = session.scalar(
            select(Listing).where(Listing.store == raw.store, Listing.store_product_id == raw.store_product_id)
        )
        if listing is None:
            listing = Listing(
                product=_get_or_create_product(session, raw),
                store=raw.store,
                store_product_id=raw.store_product_id,
            )
            session.add(listing)
            stats.created += 1
        else:
            stats.updated += 1

        if listing.price != price:
            if listing.price is not None:
                stats.price_changes += 1
            listing.price_history.append(PricePoint(price=price, recorded_at=now))

        listing.price = price
        listing.mrp = mrp
        listing.discount_pct = discount_pct(price, mrp)
        listing.url = raw.url
        listing.affiliate_url = affiliate_url(raw.store, raw.url, settings)
        listing.in_stock = raw.in_stock
        listing.rating = raw.rating
        listing.rating_count = raw.rating_count
        listing.last_seen_at = now
        _sync_sizes(listing, raw.sizes)

    session.commit()
    return stats
