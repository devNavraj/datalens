"""Daily ingestion of AU tech job postings from Adzuna into the bronze layer.

The `datalens` package is importable inside the Airflow containers via
PYTHONPATH=/opt/datalens/src (see docker/compose.dev.yml).
"""

import pendulum
from airflow.decorators import dag, task


@dag(
    dag_id="adzuna_ingest_daily",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2026, 6, 1, tz="Australia/Sydney"),
    catchup=False,
    tags=["ingest", "bronze", "adzuna"],
    default_args={"retries": 2},
)
def adzuna_ingest_daily() -> None:
    @task
    def ingest_to_bronze(ds: str | None = None) -> list[str]:
        from datetime import date

        from datalens.ingest import run_adzuna_ingest

        ingest_date = date.fromisoformat(ds) if ds else None
        return run_adzuna_ingest(ingest_date=ingest_date)

    ingest_to_bronze()


adzuna_ingest_daily()
