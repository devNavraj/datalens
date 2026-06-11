"""Build a small local lake from the test fixtures so dbt can run without S3.

Usage: python scripts/build_fixture_lake.py [lake_dir]   (default: .lake)

Used by CI and local development:
    python scripts/build_fixture_lake.py .lake
    DATALENS_LAKE_URI=$PWD/.lake DBT_TARGET=ci dbt build --project-dir pipelines/dbt --profiles-dir pipelines/dbt
"""

import sys
from datetime import date
from pathlib import Path

from datalens.storage import FilesystemObjectStore
from datalens.transforms import transform_adzuna_bronze

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "backend" / "tests" / "fixtures"


def main() -> None:
    lake_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".lake").resolve()
    store = FilesystemObjectStore(lake_dir)
    # DuckDB's COPY TO (dbt external materialization) won't create parent dirs.
    (lake_dir / "gold").mkdir(parents=True, exist_ok=True)

    # Two ingest dates so cross-day dedupe in stg_job_postings is exercised.
    for ingest_date in (date(2026, 6, 9), date(2026, 6, 10)):
        for i, fixture in enumerate(sorted(FIXTURES.glob("adzuna_page_*.json")), start=1):
            store.put(
                f"bronze/adzuna/ingest_date={ingest_date.isoformat()}/page_{i:03d}.json",
                fixture.read_bytes(),
            )
        written = transform_adzuna_bronze(store, ingest_date)
        print(f"{ingest_date}: {', '.join(written.values())}")

    print(f"fixture lake ready at {lake_dir}")


if __name__ == "__main__":
    main()
