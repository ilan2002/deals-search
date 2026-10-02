import pytest

from app.config import Settings
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
from app.stores import Store


@pytest.mark.parametrize(
    ("value", "paise"),
    [("₹1,299", 129900), ("Rs. 1,299.50", 129950), (499, 49900), (12.345, 1235), ("  799 ", 79900), (None, None)],
)
def test_parse_price(value, paise):
    assert parse_price(value) == paise


@pytest.mark.parametrize("value", ["free", "₹0", -5, True])
def test_parse_price_rejects_bad_values(value):
    with pytest.raises(ValueError):
        parse_price(value)


def test_discount_pct():
    assert discount_pct(69900, 179900) == 61
    assert discount_pct(1000, None) == 0
    assert discount_pct(1000, 900) == 0  # MRP below price is a feed error, not a discount


def test_normalize_size():
    assert normalize_size(" uk 8 ") == "UK8"
    assert normalize_size("m") == "M"


@pytest.mark.parametrize(
    ("title", "hint", "slug"),
    [
        ("Men Regular Fit Polo T-Shirt", None, "tshirts"),
        ("Men Slim Fit Checked Casual Shirt", None, "shirts"),
        ("Women Floral Print A-Line Shirt Dress", None, "dresses"),
        ("Denimcraft Men Slim Fit Jeans", None, "jeans"),
        ("Women Wide Leg Trousers", None, "trousers"),
        ("Unisex Running Shoes", None, "footwear"),
        ("Nimbus N5 5G (8GB RAM, 128GB)", "Mobiles > Smartphones", "phones"),
        ("1.5 Ton 3 Star Inverter Split AC", None, "air_conditioners"),
        ("7 kg Front Load Washing Machine", None, "washing_machines"),
        ("Something unusual", None, "other"),
        # The store's category path beats words in the title.
        ("Shirt-style Kurta Set", "Women > Ethnic > Kurtas", "kurtas"),
    ],
)
def test_classify_category(title, hint, slug):
    assert classify_category(title, hint) == slug


@pytest.mark.parametrize(
    ("text", "gender"),
    [
        ("Kalpa Women's Cotton Kurta", "women"),
        ("Urbanthread Men Slim Fit Shirt", "men"),
        ("Boys Graphic T-Shirt", "kids"),
        ("Unisex Running Shoes", "unisex"),
        ("Couple Watch for Men and Women", "unisex"),
        ("Analog Watch", None),
    ],
)
def test_detect_gender(text, gender):
    assert detect_gender(text) == gender


def test_detect_color():
    assert detect_color("Midnight Black 128GB") == "black"
    assert detect_color("Navy Blue Polo") == "blue"
    assert detect_color("Maroon") == "red"
    assert detect_color("Plain tee") is None


def test_match_key_merges_only_with_model_number():
    assert match_key(Store.AMAZON, "A1", "Nimbus", "N5-8-128") == match_key(Store.FLIPKART, "F1", "NIMBUS", "n5 8 128")
    assert match_key(Store.AMAZON, "A1", "Nimbus", None) != match_key(Store.FLIPKART, "F1", "Nimbus", None)


def test_affiliate_url():
    settings = Settings(amazon_associate_tag="deals-21", flipkart_affiliate_id="aff1")
    assert affiliate_url(Store.AMAZON, "https://www.amazon.in/dp/X?tag=old&th=1", settings) == (
        "https://www.amazon.in/dp/X?th=1&tag=deals-21"
    )
    assert affiliate_url(Store.FLIPKART, "https://www.flipkart.com/p/itm1", settings) == (
        "https://www.flipkart.com/p/itm1?affid=aff1"
    )
    assert affiliate_url(Store.MYNTRA, "https://network.example/deep/123", settings) == (
        "https://network.example/deep/123"
    )
    assert affiliate_url(Store.AMAZON, "https://www.amazon.in/dp/X", Settings()) == "https://www.amazon.in/dp/X"
