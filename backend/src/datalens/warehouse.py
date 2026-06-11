"""DuckDB-backed read access to the gold layer.

The warehouse is read-only by construction: it only ever SELECTs from
Parquet files under {lake_uri}/gold/, table names come from a fixed
allowlist, and all user-supplied values are bound parameters.
"""

from collections.abc import Sequence
from typing import Any
from urllib.parse import urlparse

import duckdb

from datalens.config import Settings

GOLD_TABLES = frozenset({"fct_job_postings", "dim_skills", "skill_demand_daily", "salary_by_skill"})


class UnknownTableError(ValueError):
    pass


class Warehouse:
    def __init__(self, settings: Settings) -> None:
        self._lake_uri = settings.lake_uri.rstrip("/")
        self._conn = duckdb.connect(":memory:")
        if self._lake_uri.startswith("s3://"):
            self._configure_s3(settings)

    def _configure_s3(self, settings: Settings) -> None:
        # DuckDB SET cannot bind parameters; these values are config-sourced, not
        # user input, but guard against quote/metachar breakage all the same.
        for value in (
            settings.s3_endpoint_url,
            settings.s3_access_key_id,
            settings.s3_secret_access_key,
            settings.s3_region,
        ):
            if value and ("'" in value or ";" in value):
                raise ValueError(f"unsafe character in S3 config value {value!r}")
        self._conn.execute("INSTALL httpfs; LOAD httpfs;")
        if settings.s3_endpoint_url:
            endpoint = urlparse(settings.s3_endpoint_url)
            use_ssl = "true" if endpoint.scheme == "https" else "false"
            self._conn.execute(f"SET s3_endpoint='{endpoint.netloc}'")
            self._conn.execute(f"SET s3_use_ssl={use_ssl}")
            self._conn.execute("SET s3_url_style='path'")
        if settings.s3_access_key_id and settings.s3_secret_access_key:
            self._conn.execute(f"SET s3_access_key_id='{settings.s3_access_key_id}'")
            self._conn.execute(f"SET s3_secret_access_key='{settings.s3_secret_access_key}'")
        if settings.s3_region:
            self._conn.execute(f"SET s3_region='{settings.s3_region}'")

    def gold_path(self, table: str) -> str:
        if table not in GOLD_TABLES:
            raise UnknownTableError(f"unknown gold table {table!r}")
        return f"{self._lake_uri}/gold/{table}.parquet"

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        cursor = self._conn.execute(sql, list(params))
        columns = [d[0] for d in cursor.description or []]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def table_exists(self, table: str) -> bool:
        try:
            self._conn.execute(f"select 1 from read_parquet('{self.gold_path(table)}') limit 1")
            return True
        except duckdb.Error:
            return False


class JobMarketService:
    def __init__(self, warehouse: Warehouse) -> None:
        self._wh = warehouse

    def top_skills(self, limit: int = 20) -> list[dict[str, Any]]:
        sql = (
            f"select skill, skill_category, postings_count "
            f"from read_parquet('{self._wh.gold_path('dim_skills')}') "
            f"order by postings_count desc, skill limit ?"
        )
        return self._wh.query(sql, (limit,))

    def skill_trend(self, skill: str) -> list[dict[str, Any]]:
        sql = (
            f"select posting_date, postings "
            f"from read_parquet('{self._wh.gold_path('skill_demand_daily')}') "
            f"where skill = ? order by posting_date"
        )
        return self._wh.query(sql, (skill,))

    def salaries(self, limit: int = 20, min_sample_size: int = 1) -> list[dict[str, Any]]:
        sql = (
            f"select skill, skill_category, sample_size, avg_salary, median_salary, "
            f"min_salary, max_salary "
            f"from read_parquet('{self._wh.gold_path('salary_by_skill')}') "
            f"where sample_size >= ? order by median_salary desc limit ?"
        )
        return self._wh.query(sql, (min_sample_size, limit))

    def summary(self) -> dict[str, Any]:
        sql = (
            f"select count(*) as total_postings, "
            f"count(distinct company) as companies, "
            f"min(posting_date) as earliest_posting, "
            f"max(posting_date) as latest_posting "
            f"from read_parquet('{self._wh.gold_path('fct_job_postings')}')"
        )
        rows = self._wh.query(sql)
        if not rows:  # aggregate query always returns one row, but stay defensive
            return {
                "total_postings": 0,
                "companies": 0,
                "earliest_posting": None,
                "latest_posting": None,
            }
        return rows[0]
