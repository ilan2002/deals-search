from collections.abc import Iterator

from app.ingestion.base import Connector, RawListing


class FlipkartConnector(Connector):
    """Flipkart through the Flipkart Affiliate product feed API. Not wired yet.

    To implement:
      * Register on the Flipkart Affiliate programme (whether it accepts new
        sign-ups varies) to get an affiliate ID and API token.
      * Read the per-category product feeds, then the delta feeds for price and
        stock changes, and map each item to RawListing.
      * Set DEALS_FLIPKART_AFFILIATE_ID so outbound links carry the affiliate ID.
    """

    name = "flipkart"

    def fetch(self) -> Iterator[RawListing]:
        raise NotImplementedError("Flipkart connector is not wired yet; see FlipkartConnector docstring.")
