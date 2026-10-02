"""Turning messy store data into consistent fields."""

import re
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.config import Settings
from app.stores import Store
from app.taxonomy import CATEGORIES

_AMOUNT_RE = re.compile(r"\d+(?:\.\d+)?")


def parse_price(value: str | int | float | None) -> int | None:
    """Return a price in paise. Accepts 1299, 1299.5, "₹1,299", "Rs. 1,299.00"."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"not a price: {value!r}")
    if isinstance(value, (int, float)):
        amount = Decimal(str(value))
    else:
        match = _AMOUNT_RE.search(value.replace(",", ""))
        if not match:
            raise ValueError(f"no price in {value!r}")
        amount = Decimal(match.group())
    if amount <= 0:
        raise ValueError(f"price must be positive: {value!r}")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def discount_pct(price: int, mrp: int | None) -> int:
    if not mrp or mrp <= price:
        return 0
    return ((mrp - price) * 100 + mrp // 2) // mrp


def normalize_size(size: str) -> str:
    """"uk 8" -> "UK8", "m" -> "M"."""
    return re.sub(r"\s+", "", size).upper()


def _word(pattern: str, plural: bool = False) -> re.Pattern[str]:
    suffix = "(?:e?s)?" if plural else ""
    return re.compile(rf"(?<![a-z]){pattern}{suffix}(?![a-z])")


_CATEGORY_PATTERNS = [
    (_word(re.escape(keyword), plural=True), category.slug, len(keyword))
    for category in CATEGORIES.values()
    for keyword in category.keywords
]


def _match_category(text: str) -> str | None:
    # The product noun usually comes last in Indian store titles ("Women Shirt
    # Dress", "Men Polo T-Shirt"), so prefer the latest match, then the longest.
    best: tuple[int, int, str] | None = None
    lowered = text.lower()
    for pattern, slug, length in _CATEGORY_PATTERNS:
        for match in pattern.finditer(lowered):
            candidate = (match.end(), length, slug)
            if best is None or candidate[:2] > best[:2]:
                best = candidate
    return best[2] if best else None


def classify_category(title: str, hint: str | None = None) -> str:
    """Map a store listing to one of our category slugs. The store's own category path wins."""
    for text in (hint, title):
        if text and (slug := _match_category(text)):
            return slug
    return "other"


_GENDER_PATTERNS = {
    "unisex": _word("unisex"),
    "kids": _word("(?:boys?|girls?|kids?|infants?|baby)"),
    "women": _word("(?:women|womens|woman|ladies|female)"),
    "men": _word("(?:men|mens|man|male|gents)"),
}


def detect_gender(text: str) -> str | None:
    lowered = text.lower()
    found = {gender for gender, pattern in _GENDER_PATTERNS.items() if pattern.search(lowered)}
    if "unisex" in found or {"men", "women"} <= found:
        return "unisex"
    for gender in ("kids", "women", "men"):
        if gender in found:
            return gender
    return None


# Colour word -> colour family. Phase 2 replaces this with colours read from
# the product image, which skin-tone matching needs anyway.
_COLOR_FAMILIES = {
    "black": "black", "white": "white", "ivory": "white",
    "grey": "grey", "gray": "grey", "charcoal": "grey",
    "navy": "blue", "blue": "blue", "teal": "blue", "turquoise": "blue",
    "red": "red", "maroon": "red", "wine": "red", "burgundy": "red",
    "green": "green", "olive": "green", "mint": "green",
    "yellow": "yellow", "mustard": "yellow",
    "orange": "orange", "peach": "orange", "coral": "orange", "rust": "orange",
    "pink": "pink", "magenta": "pink",
    "purple": "purple", "lavender": "purple", "violet": "purple",
    "brown": "brown", "tan": "brown", "khaki": "beige",
    "beige": "beige", "cream": "beige", "off white": "beige",
    "gold": "gold", "silver": "silver",
    "multicolor": "multi", "multicolour": "multi", "multi": "multi",
}
_COLOR_PATTERNS = [(_word(re.escape(word)), family) for word, family in _COLOR_FAMILIES.items()]


def detect_color(text: str) -> str | None:
    """The colour family of the first colour word in the text."""
    lowered = text.lower()
    hits = [(m.start(), family) for pattern, family in _COLOR_PATTERNS if (m := pattern.search(lowered))]
    return min(hits)[1] if hits else None


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def match_key(store: Store, store_product_id: str, brand: str | None, model_number: str | None) -> str:
    """Only merge listings across stores when a brand + model number identifies the item.

    Title-based fuzzy matching is error-prone (sizes, colours, combos), so it is
    left for later rather than merging the wrong products.
    """
    if brand and model_number:
        return f"model:{_slug(brand)}:{_slug(model_number)}"
    return f"{store}:{store_product_id}"


def _with_param(url: str, key: str, value: str) -> str:
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != key]
    query.append((key, value))
    return urlunsplit(parts._replace(query=urlencode(query)))


def affiliate_url(store: Store, url: str, settings: Settings) -> str:
    if store == Store.AMAZON and settings.amazon_associate_tag:
        return _with_param(url, "tag", settings.amazon_associate_tag)
    if store == Store.FLIPKART and settings.flipkart_affiliate_id:
        return _with_param(url, "affid", settings.flipkart_affiliate_id)
    return url
