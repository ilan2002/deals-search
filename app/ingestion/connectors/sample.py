import json
from collections.abc import Iterator
from pathlib import Path

from app.ingestion.base import Connector, RawListing
from app.stores import Store

SAMPLE_FILE = Path(__file__).resolve().parents[3] / "data" / "sample_listings.json"


class SampleFeedConnector(Connector):
    """Made-up listings for local development and tests. Brands and links are fictional."""

    name = "sample"

    def __init__(self, path: Path = SAMPLE_FILE) -> None:
        self.path = path

    def fetch(self) -> Iterator[RawListing]:
        for item in json.loads(self.path.read_text(encoding="utf-8")):
            yield RawListing(**{**item, "store": Store(item["store"])})
