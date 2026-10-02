"""Our own category tree. Every store's categories are mapped onto these slugs."""

from dataclasses import dataclass
from enum import StrEnum


class TryOn(StrEnum):
    FULL = "full"  # garment try-on models handle these well (tops, bottoms, dresses)
    PREVIEW = "preview"  # approximate only: shoes, watches, draped wear like sarees
    NONE = "none"


@dataclass(frozen=True)
class Category:
    slug: str
    name: str
    parent: str | None
    try_on: TryOn = TryOn.NONE
    # Matched against store category paths and titles, singular form;
    # plurals ("shirts", "dresses") are handled by the matcher.
    keywords: tuple[str, ...] = ()


CATEGORIES: dict[str, Category] = {
    c.slug: c
    for c in [
        Category("fashion", "Fashion", None),
        Category("shirts", "Shirts", "fashion", TryOn.FULL, ("shirt",)),
        Category("tshirts", "T-Shirts", "fashion", TryOn.FULL, ("t-shirt", "tshirt", "tee", "polo")),
        Category("jeans", "Jeans", "fashion", TryOn.FULL, ("jean", "denim")),
        Category(
            "trousers", "Trousers & Pants", "fashion", TryOn.FULL,
            ("trouser", "pant", "chino", "jogger", "track pant", "cargo"),
        ),
        Category("dresses", "Dresses", "fashion", TryOn.FULL, ("dress", "gown")),
        Category("kurtas", "Kurtas & Kurtis", "fashion", TryOn.FULL, ("kurta", "kurti")),
        Category("sarees", "Sarees", "fashion", TryOn.PREVIEW, ("saree", "sari")),
        Category(
            "footwear", "Footwear", "fashion", TryOn.PREVIEW,
            ("shoe", "sneaker", "sandal", "slipper", "loafer", "boot", "heel", "flip flop"),
        ),
        Category("watches", "Watches", "fashion", TryOn.PREVIEW, ("watch", "smartwatch")),
        Category("electronics", "Electronics", None),
        Category("phones", "Mobile Phones", "electronics", keywords=("smartphone", "mobile phone", "iphone")),
        Category("laptops", "Laptops", "electronics", keywords=("laptop", "notebook pc")),
        Category(
            "headphones", "Headphones & Earbuds", "electronics",
            keywords=("headphone", "earphone", "earbud", "neckband"),
        ),
        Category("televisions", "Televisions", "electronics", keywords=("smart tv", "led tv", "television")),
        Category("appliances", "Home Appliances", None),
        Category("washing_machines", "Washing Machines", "appliances", keywords=("washing machine",)),
        Category("refrigerators", "Refrigerators", "appliances", keywords=("refrigerator", "fridge")),
        Category(
            "air_conditioners", "Air Conditioners", "appliances",
            keywords=("air conditioner", "split ac", "window ac", "inverter ac"),
        ),
        Category("other", "Other", None),
    ]
}


def descendants(slug: str) -> set[str]:
    """The category itself plus everything under it."""
    result = {slug}
    for category in CATEGORIES.values():
        if category.parent == slug:
            result |= descendants(category.slug)
    return result


def children(slug: str | None) -> list[Category]:
    return [c for c in CATEGORIES.values() if c.parent == slug]
