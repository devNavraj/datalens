"""Ingestion entrypoints — called by Airflow DAGs and the `datalens-ingest` CLI."""

import argparse
import logging
from datetime import date

from datalens.config import Settings
from datalens.connectors import AdzunaConnector, BaseConnector, BronzeWriter
from datalens.storage import ObjectStore, S3ObjectStore

logger = logging.getLogger(__name__)


def run_ingest(
    connector: BaseConnector,
    store: ObjectStore,
    ingest_date: date | None = None,
) -> list[str]:
    """Extract all batches from a connector into the bronze layer. Returns written keys."""
    writer = BronzeWriter(store)
    day = ingest_date or date.today()
    keys: list[str] = []
    for batch in connector.extract():
        key = writer.write(connector.source_name, batch, day)
        logger.info("bronze write: %s (%s records)", key, batch.record_count)
        keys.append(key)
    logger.info("ingest complete: source=%s batches=%d", connector.source_name, len(keys))
    return keys


def run_adzuna_ingest(
    settings: Settings | None = None,
    ingest_date: date | None = None,
) -> list[str]:
    settings = settings or Settings()
    connector = AdzunaConnector(
        settings.adzuna_app_id,
        settings.adzuna_app_key,
        country=settings.adzuna_country,
        category=settings.adzuna_category,
        results_per_page=settings.adzuna_results_per_page,
        max_pages=settings.adzuna_max_pages,
    )
    store = S3ObjectStore.from_settings(settings)
    return run_ingest(connector, store, ingest_date)


def main() -> None:  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Run a DataLens ingestion job")
    parser.add_argument("source", choices=["adzuna"])
    parser.add_argument("--date", type=date.fromisoformat, default=None, dest="ingest_date")
    args = parser.parse_args()
    keys = run_adzuna_ingest(ingest_date=args.ingest_date)
    print(f"wrote {len(keys)} bronze object(s)")


if __name__ == "__main__":  # pragma: no cover
    main()
