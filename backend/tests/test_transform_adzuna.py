import io
import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from datalens.storage import InMemoryObjectStore
from datalens.transforms import transform_adzuna_bronze
from datalens.transforms.adzuna import flatten_pages

FIXTURES = Path(__file__).parent / "fixtures"
INGEST_DATE = date(2026, 6, 10)


def load_fixture_pages() -> list[dict]:
    return [
        json.loads((FIXTURES / name).read_text())
        for name in ("adzuna_page_001.json", "adzuna_page_002.json")
    ]


def seeded_store() -> InMemoryObjectStore:
    store = InMemoryObjectStore()
    for i, name in enumerate(("adzuna_page_001.json", "adzuna_page_002.json"), start=1):
        store.put(
            f"bronze/adzuna/ingest_date={INGEST_DATE.isoformat()}/page_{i:03d}.json",
            (FIXTURES / name).read_bytes(),
        )
    return store


class TestFlattenPages:
    def test_dedupes_and_drops_invalid_dates(self) -> None:
        frame = flatten_pages(load_fixture_pages(), INGEST_DATE)
        # 6 raw records: one duplicate id (5000000001) and one invalid created date dropped
        assert sorted(frame["job_id"]) == [
            "5000000001",
            "5000000002",
            "5000000003",
            "5000000004",
        ]
        # duplicate kept the first occurrence (page 1 description, not the page 2 copy)
        dup = frame.loc[frame["job_id"] == "5000000001"].iloc[0]
        assert "ETL pipelines" in dup["description"]

    def test_nested_fields_flattened(self) -> None:
        frame = flatten_pages(load_fixture_pages(), INGEST_DATE)
        job = frame.loc[frame["job_id"] == "5000000001"].iloc[0]
        assert job["company"] == "Acme Analytics"
        assert job["state"] == "New South Wales"
        assert job["salary_is_predicted"] is False or job["salary_is_predicted"] == False  # noqa: E712

    def test_missing_optionals_are_none(self) -> None:
        frame = flatten_pages(load_fixture_pages(), INGEST_DATE)
        job = frame.loc[frame["job_id"] == "5000000003"].iloc[0]
        assert pd.isna(job["company"])
        assert pd.isna(job["salary_min"])
        assert pd.isna(job["contract_type"])

    def test_empty_pages_give_empty_frame(self) -> None:
        assert flatten_pages([{"results": []}], INGEST_DATE).empty


class TestTransformAdzunaBronze:
    def test_writes_validated_silver_tables(self) -> None:
        store = seeded_store()

        written = transform_adzuna_bronze(store, INGEST_DATE)

        assert written == {
            "job_postings": "silver/adzuna/job_postings/ingest_date=2026-06-10/data.parquet",
            "job_skills": "silver/adzuna/job_skills/ingest_date=2026-06-10/data.parquet",
        }
        postings = pd.read_parquet(io.BytesIO(store.get(written["job_postings"])))
        skills = pd.read_parquet(io.BytesIO(store.get(written["job_skills"])))

        assert len(postings) == 4
        assert postings["job_id"].is_unique

        by_job = skills.groupby("job_id")["skill"].apply(set).to_dict()
        assert {"python", "airflow", "dbt", "aws", "snowflake", "sql", "terraform"} <= by_job[
            "5000000001"
        ]
        assert "go" in by_job["5000000004"]
        # ML job: predicted-salary flag preserved, skills found, no "excel" false positive
        assert "excel" not in by_job["5000000002"]
        assert {"pytorch", "scikit-learn", "mlops", "genai", "rag", "azure"} <= by_job["5000000002"]

    def test_raises_when_bronze_empty(self) -> None:
        with pytest.raises(FileNotFoundError, match="no bronze objects"):
            transform_adzuna_bronze(InMemoryObjectStore(), INGEST_DATE)

    def test_raises_when_pages_have_no_valid_records(self) -> None:
        store = InMemoryObjectStore()
        store.put(
            f"bronze/adzuna/ingest_date={INGEST_DATE.isoformat()}/page_001.json",
            b'{"results": []}',
        )
        with pytest.raises(ValueError, match="no valid job records"):
            transform_adzuna_bronze(store, INGEST_DATE)
