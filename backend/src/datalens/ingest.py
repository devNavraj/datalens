"""Ingestion entrypoints — called by Airflow DAGs and the `datalens-ingest` CLI."""

import argparse
import logging
from datetime import date

from datalens.config import Settings
from datalens.connectors import AdzunaConnector, BaseConnector, BronzeWriter
from datalens.storage import ObjectStore, S3ObjectStore
from datalens.transforms import transform_adzuna_bronze

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
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise ValueError(
            "Adzuna credentials not configured — set DATALENS_ADZUNA_APP_ID and "
            "DATALENS_ADZUNA_APP_KEY (free signup at https://developer.adzuna.com/)"
        )
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


def run_adzuna_silver(
    settings: Settings | None = None,
    ingest_date: date | None = None,
) -> dict[str, str]:
    """Bronze → silver for one ingest date. Returns {table: silver_key}."""
    settings = settings or Settings()
    store = S3ObjectStore.from_settings(settings)
    return transform_adzuna_bronze(store, ingest_date or date.today())


def main() -> None:  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Run a DataLens ingestion job")
    parser.add_argument("source", choices=["adzuna"])
    parser.add_argument("--date", type=date.fromisoformat, default=None, dest="ingest_date")
    parser.add_argument("--step", choices=["bronze", "silver", "all"], default="all")
    args = parser.parse_args()
    if args.source != "adzuna":  # argparse choices make this unreachable; guards future wiring
        raise SystemExit(f"no ingest runner wired for source {args.source!r}")
    if args.step in ("bronze", "all"):
        keys = run_adzuna_ingest(ingest_date=args.ingest_date)
        print(f"bronze: wrote {len(keys)} object(s)")
    if args.step in ("silver", "all"):
        written = run_adzuna_silver(ingest_date=args.ingest_date)
        print(f"silver: wrote {', '.join(written.values())}")


if __name__ == "__main__":  # pragma: no cover
    main()
