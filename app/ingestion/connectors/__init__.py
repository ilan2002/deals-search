from collections.abc import Callable

from app.ingestion.base import Connector
from app.ingestion.connectors.affiliate_network import AffiliateNetworkConnector
from app.ingestion.connectors.amazon import AmazonConnector
from app.ingestion.connectors.flipkart import FlipkartConnector
from app.ingestion.connectors.sample import SampleFeedConnector
from app.stores import Store

CONNECTORS: dict[str, Callable[[], Connector]] = {
    "sample": SampleFeedConnector,
    "amazon": AmazonConnector,
    "flipkart": FlipkartConnector,
    "myntra": lambda: AffiliateNetworkConnector(Store.MYNTRA),
    "ajio": lambda: AffiliateNetworkConnector(Store.AJIO),
}
