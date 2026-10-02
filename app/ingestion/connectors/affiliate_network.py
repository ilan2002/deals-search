from collections.abc import Iterator

from app.ingestion.base import Connector, RawListing
from app.stores import Store


class AffiliateNetworkConnector(Connector):
    """Myntra and AJIO through an Indian affiliate network. Not wired yet.

    Neither store offers a public product API, and scraping them breaks their
    terms and gets blocked. Networks such as Cuelinks, EarnKaro, Admitad,
    vCommission or INRDeals provide product/deal feeds (CSV, XML or JSON) with
    deep links that are already tracked.

    To implement:
      * Sign up with a network that carries the store, then download its feed.
      * Map each row to RawListing, using the network's tracked link as `url`.
    """

    def __init__(self, store: Store) -> None:
        self.store = store
        self.name = str(store)

    def fetch(self) -> Iterator[RawListing]:
        raise NotImplementedError(
            f"{self.store} feed is not wired yet; see AffiliateNetworkConnector docstring."
        )
