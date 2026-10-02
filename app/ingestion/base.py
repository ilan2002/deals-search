from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field

from app.stores import Store


@dataclass
class RawListing:
    """A listing as a store feed gives it, before normalisation."""

    store: Store
    store_product_id: str
    title: str
    url: str
    price: str | int | float  # as the feed has it, e.g. "₹1,299" or 1299
    mrp: str | int | float | None = None
    brand: str | None = None
    category_hint: str | None = None  # the store's own category path
    model_number: str | None = None  # lets the same item on two stores share a product
    color: str | None = None
    image_url: str | None = None
    sizes: list[str] = field(default_factory=list)
    in_stock: bool = True
    rating: float | None = None
    rating_count: int | None = None
    attributes: dict = field(default_factory=dict)


class Connector(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> Iterable[RawListing]: ...
