from enum import StrEnum


class Store(StrEnum):
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    MYNTRA = "myntra"
    AJIO = "ajio"


STORE_NAMES: dict[Store, str] = {
    Store.AMAZON: "Amazon.in",
    Store.FLIPKART: "Flipkart",
    Store.MYNTRA: "Myntra",
    Store.AJIO: "AJIO",
}
