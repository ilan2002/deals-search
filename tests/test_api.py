def _titles(response) -> set[str]:
    assert response.status_code == 200, response.text
    return {item["title"] for item in response.json()["items"]}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_stores_and_categories(client):
    assert [s["id"] for s in client.get("/stores").json()] == ["amazon", "flipkart", "myntra", "ajio"]

    tree = {c["slug"]: c for c in client.get("/categories").json()}
    assert {"fashion", "electronics", "appliances"} <= tree.keys()
    fashion = {c["slug"]: c["try_on"] for c in tree["fashion"]["children"]}
    assert fashion["shirts"] == "full"
    assert fashion["footwear"] == "preview"


def test_category_filter_includes_subcategories(client):
    body = client.get("/products", params={"category": "fashion", "page_size": 100}).json()
    categories = {item["category"] for item in body["items"]}
    assert {"shirts", "tshirts", "dresses", "footwear", "sarees"} <= categories
    assert "phones" not in categories
    assert body["total"] == 10  # the out-of-stock kids t-shirt is hidden


def test_out_of_stock_can_be_included(client):
    body = client.get("/products", params={"category": "tshirts", "include_out_of_stock": True}).json()
    assert body["total"] == 2


def test_store_size_and_gender_filters(client):
    assert _titles(client.get("/products", params={"store": "myntra"})) == {
        "Urbanthread Men Slim Fit Checked Casual Shirt",
        "Kalpa Women Floral Print A-Line Shirt Dress",
        "Kalpa Women Banarasi Silk Saree with Blouse Piece",
    }
    assert _titles(client.get("/products", params={"size": "uk 8"})) == {
        "StrideX Unisex Running Shoes",
        "StrideX Men White Casual Sneakers",
    }
    men = _titles(client.get("/products", params={"gender": "men", "page_size": 100}))
    assert "StrideX Unisex Running Shoes" in men
    assert "Kalpa Women's Cotton Printed Straight Kurta" not in men


def test_price_range_in_rupees(client):
    assert _titles(client.get("/products", params={"min_price": 1000, "max_price": 1500})) == {
        "Denimcraft Women High-Rise Wide Leg Trousers",
        "StrideX Unisex Running Shoes",
        "StrideX Men White Casual Sneakers",
        "Chrono & Co Men Analog Black Dial Watch",
    }


def test_text_search(client):
    titles = _titles(client.get("/products", params={"q": "shirt"}))
    assert titles and all("shirt" in t.lower() for t in titles)
    assert _titles(client.get("/products", params={"q": "nimbus 5g"})) == {
        "Nimbus N5 5G (8GB RAM, 128GB) - Midnight Black"
    }
    assert _titles(client.get("/products", params={"q": "100%"})) == set()


def test_sorting_and_pagination(client):
    items = client.get("/products", params={"sort": "price_asc", "page_size": 100}).json()["items"]
    prices = [item["best_price"] for item in items]
    assert prices == sorted(prices)

    page1 = client.get("/products", params={"sort": "discount", "page_size": 5}).json()
    page2 = client.get("/products", params={"sort": "discount", "page_size": 5, "page": 2}).json()
    assert page1["total"] == 15
    discounts = [i["best_discount_pct"] for i in page1["items"] + page2["items"]]
    assert discounts == sorted(discounts, reverse=True)
    assert not {i["id"] for i in page1["items"]} & {i["id"] for i in page2["items"]}


def test_merged_product_shows_cheapest_store(client):
    item = client.get("/products", params={"category": "phones"}).json()["items"][0]
    assert item["best_price"] == 17499.0
    assert [(l["store"], l["price"]) for l in item["listings"]] == [("flipkart", 17499.0), ("amazon", 17999.0)]
    assert item["listings"][1]["url"].endswith("tag=dealsearch-21")


def test_product_detail(client):
    product_id = client.get("/products", params={"category": "air_conditioners"}).json()["items"][0]["id"]
    detail = client.get(f"/products/{product_id}").json()
    assert detail["best_price"] == 31490.0
    assert detail["try_on"] == "none"
    assert all(len(l["price_history"]) == 1 for l in detail["listings"])

    assert client.get("/products/99999").status_code == 404


def test_validation_errors(client):
    assert client.get("/products", params={"category": "spaceships"}).status_code == 400
    assert client.get("/products", params={"store": "ebay"}).status_code == 422
    assert client.get("/products", params={"page_size": 1000}).status_code == 422
