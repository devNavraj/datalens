from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from datalens.api import get_warehouse
from datalens.config import Settings
from datalens.main import app
from datalens.warehouse import UnknownTableError, Warehouse


def write_gold_fixtures(lake: Path) -> None:
    gold = lake / "gold"
    gold.mkdir(parents=True)
    pd.DataFrame(
        {
            "skill": ["python", "aws", "react"],
            "skill_category": ["language", "cloud", "framework"],
            "postings_count": [120, 95, 60],
        }
    ).to_parquet(gold / "dim_skills.parquet", index=False)
    pd.DataFrame(
        {
            "posting_date": [date(2026, 6, 8), date(2026, 6, 9), date(2026, 6, 9)],
            "skill": ["python", "python", "aws"],
            "skill_category": ["language", "language", "cloud"],
            "postings": [10, 14, 9],
        }
    ).to_parquet(gold / "skill_demand_daily.parquet", index=False)
    pd.DataFrame(
        {
            "skill": ["python", "aws"],
            "skill_category": ["language", "cloud"],
            "sample_size": [40, 3],
            "avg_salary": [145000.0, 150000.0],
            "median_salary": [142000.0, 155000.0],
            "min_salary": [110000.0, 130000.0],
            "max_salary": [180000.0, 170000.0],
        }
    ).to_parquet(gold / "salary_by_skill.parquet", index=False)
    pd.DataFrame(
        {
            "job_id": ["1", "2", "3"],
            "company": ["Acme", "Acme", None],
            "posting_date": [date(2026, 6, 8), date(2026, 6, 9), date(2026, 6, 9)],
        }
    ).to_parquet(gold / "fct_job_postings.parquet", index=False)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    write_gold_fixtures(tmp_path)
    warehouse = Warehouse(Settings(lake_uri=str(tmp_path), s3_endpoint_url=None))
    app.dependency_overrides[get_warehouse] = lambda: warehouse
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_datasets_lists_gold_tables(client: TestClient) -> None:
    body = client.get("/api/datasets").json()
    assert body[0]["name"] == "adzuna"
    assert "fct_job_postings" in body[0]["tables"]


def test_top_skills_ordered_with_limit(client: TestClient) -> None:
    body = client.get("/api/job-market/skills/top", params={"limit": 2}).json()
    assert [row["skill"] for row in body] == ["python", "aws"]


def test_skill_trend_returns_time_series(client: TestClient) -> None:
    body = client.get("/api/job-market/skills/python/trend").json()
    assert body == [
        {"posting_date": "2026-06-08", "postings": 10},
        {"posting_date": "2026-06-09", "postings": 14},
    ]


def test_skill_trend_unknown_skill_404(client: TestClient) -> None:
    response = client.get("/api/job-market/skills/cobol/trend")
    assert response.status_code == 404


def test_salaries_filters_small_samples(client: TestClient) -> None:
    body = client.get("/api/job-market/salaries", params={"min_sample_size": 10}).json()
    assert [row["skill"] for row in body] == ["python"]


def test_summary_counts(client: TestClient) -> None:
    body = client.get("/api/job-market/summary").json()
    assert body["total_postings"] == 3
    assert body["companies"] == 1
    assert body["earliest_posting"] == "2026-06-08"


def test_warehouse_rejects_unknown_table(tmp_path: Path) -> None:
    warehouse = Warehouse(Settings(lake_uri=str(tmp_path), s3_endpoint_url=None))
    with pytest.raises(UnknownTableError):
        warehouse.gold_path("users; drop table x")
    assert warehouse.table_exists("dim_skills") is False  # no file written yet
