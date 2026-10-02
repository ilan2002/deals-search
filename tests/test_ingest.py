from dataclasses import replace

from sqlalchemy import func, select

from app.ingestion.base import RawListing
from app.ingestion.connectors.sample import SampleFeedConnector
from app.ingestion.service import ingest
from app.models import Listing, PricePoint, Product
from app.stores import Store


def _raw(**overrides) -> RawListing:
    raw = RawListing(
        store=Store.MYNTRA,
        store_product_id="MYN-1",
        title="Urbanthread Men Checked Shirt",
        url="https://example.com/myntra/MYN-1",
        price="₹699",
        mrp="₹1,799",
        brand="Urbanthread",
        sizes=["s", "M", "L"],
    )
    return replace(raw, **overrides)


def test_sample_feed_merges_same_model_across_stores(seeded):
    assert seeded.scalar(select(func.count(Listing.id))) == 18
    assert seeded.scalar(select(func.count(Product.id))) == 16  # phone and AC are on two stores each

    phone = seeded.scalar(select(Product).where(Product.brand == "Nimbus"))
    assert phone.category == "phones"
    assert phone.color == "black"
    assert {l.store for l in phone.listings} == {"amazon", "flipkart"}


def test_new_listing_is_normalised(session, settings):
    stats = ingest(session, [_raw()], settings)
    assert (stats.created, stats.updated, stats.skipped) == (1, 0, 0)

    listing = session.scalar(select(Listing))
    assert listing.price == 69900
    assert listing.mrp == 179900
    assert listing.discount_pct == 61
    assert [s.size for s in listing.sizes] == ["L", "M", "S"]
    assert listing.product.category == "shirts"
    assert listing.product.gender == "men"
    assert [p.price for p in listing.price_history] == [69900]


def test_reingest_updates_price_history_and_sizes(session, settings):
    ingest(session, [_raw()], settings)
    ingest(session, [_raw()], settings)  # unchanged: no new price point
    stats = ingest(session, [_raw(price="₹599", sizes=["M", "XL"], in_stock=False)], settings)

    assert (stats.created, stats.updated, stats.price_changes) == (0, 1, 1)
    listing = session.scalar(select(Listing))
    assert [p.price for p in listing.price_history] == [69900, 59900]
    assert sorted(s.size for s in listing.sizes) == ["M", "XL"]
    assert listing.in_stock is False
    assert session.scalar(select(func.count(PricePoint.id))) == 2


def test_bad_prices_are_skipped(session, settings):
    stats = ingest(session, [_raw(price="call for price"), _raw(store_product_id="MYN-2", price=None)], settings)
    assert stats.skipped == 2
    assert session.scalar(select(func.count(Listing.id))) == 0


def test_sample_connector_reads_every_row():
    rows = list(SampleFeedConnector().fetch())
    assert len(rows) == 18
    assert {r.store for r in rows} == set(Store)
