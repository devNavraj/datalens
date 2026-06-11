"""Daily Adzuna pipeline: bronze ingest → silver transform → dbt gold marts.

The `datalens` package is importable inside the Airflow containers via
PYTHONPATH=/opt/datalens/src; the dbt project is mounted at /opt/datalens/dbt
(see docker/compose.dev.yml).
"""

from datetime import timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

DBT_BUILD_CMD = (
    "dbt build --project-dir /opt/datalens/dbt --profiles-dir /opt/datalens/dbt"
)


@dag(
    dag_id="adzuna_ingest_daily",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2026, 6, 1, tz="Australia/Sydney"),
    catchup=False,
    tags=["ingest", "bronze", "silver", "gold", "adzuna"],
    default_args={"retries": 2},
)
def adzuna_ingest_daily() -> None:
    @task(execution_timeout=timedelta(minutes=10))
    def ingest_to_bronze(ds: str | None = None) -> list[str]:
        from datetime import date

        from datalens.ingest import run_adzuna_ingest

        ingest_date = date.fromisoformat(ds) if ds else None
        return run_adzuna_ingest(ingest_date=ingest_date)

    @task(execution_timeout=timedelta(minutes=10))
    def bronze_to_silver(ds: str | None = None) -> dict[str, str]:
        from datetime import date

        from datalens.ingest import run_adzuna_silver

        ingest_date = date.fromisoformat(ds) if ds else None
        return run_adzuna_silver(ingest_date=ingest_date)

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=DBT_BUILD_CMD,
        execution_timeout=timedelta(minutes=15),
    )

    ingest_to_bronze() >> bronze_to_silver() >> dbt_build  # type: ignore[operator]


adzuna_ingest_daily()
