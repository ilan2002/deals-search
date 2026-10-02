# Deals Search

One place to find the best deals from **Amazon.in, Flipkart, Myntra and AJIO**:
fashion (shirts, t-shirts, jeans, dresses, kurtas, sarees, footwear, watches),
electronics (phones, TVs, earbuds) and home appliances.

Fashion gets extra help: colour suggestions by skin tone, size recommendations,
and a virtual "fit check" that puts the clothes on the user's own photo.

## Roadmap

| Phase | What | Status |
|---|---|---|
| 1 | Deals backend: store feeds, one category tree, search and filters, affiliate links, price history | **This repo, in progress** |
| 2 | Skin-tone colour matching and size recommendation | Interfaces in `app/personalization/` |
| 3 | Virtual try-on for tops, bottoms, dresses and kurtas, with tap-to-zoom on each item | Interface in `app/personalization/tryon.py` |
| 4 | Footwear, watches, sarees, complete outfits | Planned |

## Running it

Requires Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env              # optional: affiliate IDs, Postgres URL

python -m app.ingestion.run sample   # load the fictional sample listings
uvicorn app.main:app --reload        # http://localhost:8000/docs
pytest
```

SQLite is the default. For Postgres: `pip install -e ".[postgres]"` and set
`DEALS_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/deals`.

## API

| Endpoint | Purpose |
|---|---|
| `GET /products` | Search across all stores |
| `GET /products/{id}` | One product with every store's offer and price history |
| `GET /categories` | Category tree, with whether try-on supports each category |
| `GET /stores` | Supported stores |
| `GET /health` | Health check |

`/products` filters: `q`, `category` (includes sub-categories, e.g. `fashion`),
`store`, `brand`, `gender` (`men`/`women` also include unisex), `color`, `size`,
`min_price`/`max_price` (rupees), `min_discount`, `include_out_of_stock`,
`sort` (`relevance`, `price_asc`, `price_desc`, `discount`, `rating`, `newest`),
`page`, `page_size`. `store`, `brand`, `color` and `size` can be repeated.

```bash
# Today's biggest fashion deals
curl "localhost:8000/products?category=fashion&sort=discount&min_discount=50"
# Men's sneakers in UK 8 under ₹2,000
curl "localhost:8000/products?category=footwear&gender=men&size=UK8&max_price=2000"
```

Each product shows its lowest price and every store's offer, cheapest first.
The `url` on each offer already carries the affiliate ID.

## How it works

```
store feeds ──> connectors ──> normalise ──> Product + Listing rows ──> search API
               (app/ingestion/  (price, category,   (one product,
                connectors/)     gender, colour,     many store offers,
                                 sizes, links)       price history)
```

- **Prices** are stored in paise (integers) and returned in rupees.
- **Categories:** each store's category path, then the title, is mapped onto our own tree (`app/taxonomy.py`).
- **Same item on two stores:** merged into one product only when brand + model number match.
  Title-based matching is left for later because it merges the wrong products too easily.
- **Price history:** a point is recorded every time a listing's price changes.

### Store data sources

| Store | Source | Connector |
|---|---|---|
| Amazon.in | Amazon Associates product API (access usually opens after first qualifying sales) | `amazon.py`, not wired yet |
| Flipkart | Flipkart Affiliate product feed API | `flipkart.py`, not wired yet |
| Myntra, AJIO | No public API. Use an affiliate network feed (Cuelinks, EarnKaro, Admitad, vCommission, INRDeals) | `affiliate_network.py`, not wired yet |

We don't scrape stores: it breaks their terms and gets blocked. Each connector's
docstring lists what is needed to wire it up. `data/sample_listings.json` holds
fictional listings so everything runs before the real feeds are connected.

## Project layout

```
app/
  main.py, api.py, schemas.py   FastAPI app, routes and response models
  models.py, db.py, config.py   Database tables, session, settings (DEALS_* env vars)
  search.py                     Search and filter queries
  taxonomy.py, stores.py        Category tree and store list
  ingestion/                    Connectors, normalisation, upsert service, CLI
  personalization/              Phase 2/3 interfaces: skin tone, sizing, try-on
data/sample_listings.json       Fictional sample feed
tests/
```

## Privacy

User photos and body measurements are sensitive personal data under India's
**DPDP Act 2023**. Before Phase 2 ships: explicit consent, encrypted storage,
a "delete my data" option, and no use for model training without permission.
