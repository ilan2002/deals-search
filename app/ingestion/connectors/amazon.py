from collections.abc import Iterator

from app.ingestion.base import Connector, RawListing


class AmazonConnector(Connector):
    """Amazon.in through the Amazon Associates product API. Not wired yet.

    To implement:
      * Join Amazon Associates India and request API credentials. Access is
        usually granted only after the account makes qualifying sales, and
        Amazon has been changing its product API, so check the current terms.
      * Search per category in app.taxonomy (browse nodes or keywords) and map
        each item to RawListing: ASIN -> store_product_id, offer price -> price,
        list price -> mrp, manufacturer part number -> model_number.
      * Stay within the API's request-rate limits; schedule runs, don't crawl.
    """

    name = "amazon"

    def fetch(self) -> Iterator[RawListing]:
        raise NotImplementedError("Amazon connector is not wired yet; see AmazonConnector docstring.")
