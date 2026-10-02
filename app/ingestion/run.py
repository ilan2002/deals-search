"""python -m app.ingestion.run <source>"""

import argparse
import logging

from app.db import SessionLocal, init_db
from app.ingestion.connectors import CONNECTORS
from app.ingestion.service import ingest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pull listings from a store connector into the database.")
    parser.add_argument("source", choices=sorted(CONNECTORS))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)
    init_db()
    connector = CONNECTORS[args.source]()
    with SessionLocal() as session:
        stats = ingest(session, connector.fetch())
    print(
        f"{connector.name}: {stats.created} new, {stats.updated} updated, "
        f"{stats.price_changes} price changes, {stats.skipped} skipped"
    )


if __name__ == "__main__":
    main()
