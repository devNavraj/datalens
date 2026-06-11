"""Bronze → silver transform for Adzuna job postings.

Reads raw JSON pages from the bronze layer, flattens them into a typed,
validated, deduplicated DataFrame, extracts skills, and writes two silver
Parquet tables:

    silver/adzuna/job_postings/ingest_date=YYYY-MM-DD/data.parquet
    silver/adzuna/job_skills/ingest_date=YYYY-MM-DD/data.parquet
"""

import io
import json
import logging
from datetime import date
from typing import Any

import pandas as pd
import pandera.pandas as pa
from pandera.engines import pandas_engine

from datalens.skills import extract_skills, skill_category
from datalens.storage.object_store import ObjectStore

logger = logging.getLogger(__name__)

JOB_POSTINGS_SCHEMA = pa.DataFrameSchema(
    {
        "job_id": pa.Column(str, unique=True, nullable=False),
        "title": pa.Column(str, nullable=False),
        "description": pa.Column(str, nullable=False),
        "company": pa.Column(str, nullable=True),
        "location": pa.Column(str, nullable=True),
        "state": pa.Column(str, nullable=True),
        "salary_min": pa.Column(float, pa.Check.ge(0), nullable=True),
        "salary_max": pa.Column(float, pa.Check.ge(0), nullable=True),
        "salary_is_predicted": pa.Column(bool, nullable=False),
        "created_at": pa.Column("datetime64[ns, UTC]", nullable=False),
        "category": pa.Column(str, nullable=True),
        "contract_type": pa.Column(str, nullable=True),
        "contract_time": pa.Column(str, nullable=True),
        "url": pa.Column(str, nullable=True),
        "ingest_date": pa.Column(pandas_engine.Date(), nullable=False),
    },
    coerce=True,
    strict=True,
)

JOB_SKILLS_SCHEMA = pa.DataFrameSchema(
    {
        "job_id": pa.Column(str, nullable=False),
        "skill": pa.Column(str, nullable=False),
        "skill_category": pa.Column(str, nullable=False),
        "ingest_date": pa.Column(pandas_engine.Date(), nullable=False),
    },
    coerce=True,
    strict=True,
)


def _opt_str(value: Any) -> str | None:
    return str(value) if value not in (None, "") else None


def flatten_job(raw: dict[str, Any], ingest_date: date) -> dict[str, Any]:
    location = raw.get("location") or {}
    area = location.get("area") or []
    return {
        "job_id": str(raw["id"]),
        "title": str(raw.get("title") or "").strip(),
        "description": str(raw.get("description") or "").strip(),
        "company": _opt_str((raw.get("company") or {}).get("display_name")),
        "location": _opt_str(location.get("display_name")),
        "state": _opt_str(area[1]) if len(area) > 1 else None,
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "salary_is_predicted": str(raw.get("salary_is_predicted", "0")) == "1",
        "created_at": raw.get("created"),
        "category": _opt_str((raw.get("category") or {}).get("label")),
        "contract_type": _opt_str(raw.get("contract_type")),
        "contract_time": _opt_str(raw.get("contract_time")),
        "url": _opt_str(raw.get("redirect_url")),
        "ingest_date": ingest_date,
    }


def flatten_pages(pages: list[dict[str, Any]], ingest_date: date) -> pd.DataFrame:
    rows = [
        flatten_job(job, ingest_date)
        for page in pages
        for job in page.get("results") or []
        if job.get("id") is not None
    ]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["created_at"] = pd.to_datetime(frame["created_at"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["created_at"])
    # Blank titles pass pandera's str check but are junk records; drop them.
    frame = frame[frame["title"].str.len() > 0]
    # Same job can appear on multiple pages within one run; keep first occurrence.
    frame = frame.drop_duplicates(subset=["job_id"], keep="first").reset_index(drop=True)
    return frame


def extract_job_skills(postings: pd.DataFrame, ingest_date: date) -> pd.DataFrame:
    rows = [
        {
            "job_id": job_id,
            "skill": skill,
            "skill_category": skill_category(skill),
            "ingest_date": ingest_date,
        }
        for job_id, title, description in postings[["job_id", "title", "description"]].itertuples(
            index=False
        )
        for skill in sorted(extract_skills(f"{title}\n{description}"))
    ]
    return pd.DataFrame(rows, columns=["job_id", "skill", "skill_category", "ingest_date"])


def _to_parquet_bytes(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    frame.to_parquet(buffer, index=False)
    return buffer.getvalue()


def transform_adzuna_bronze(store: ObjectStore, ingest_date: date) -> dict[str, str]:
    """Transform one ingest_date of bronze Adzuna pages into silver tables.

    Returns {table_name: silver_key}. Raises if bronze is empty for the date —
    an upstream ingestion problem should fail the pipeline loudly.
    """
    bronze_prefix = f"bronze/adzuna/ingest_date={ingest_date.isoformat()}/"
    keys = store.list(bronze_prefix)
    if not keys:
        raise FileNotFoundError(f"no bronze objects under {bronze_prefix!r}")

    pages = [json.loads(store.get(key)) for key in keys]
    postings = flatten_pages(pages, ingest_date)
    if postings.empty:
        raise ValueError(f"bronze pages under {bronze_prefix!r} contained no valid job records")

    postings = JOB_POSTINGS_SCHEMA.validate(postings)
    job_skills = JOB_SKILLS_SCHEMA.validate(extract_job_skills(postings, ingest_date))

    written: dict[str, str] = {}
    partition = f"ingest_date={ingest_date.isoformat()}"
    for table, frame in (("job_postings", postings), ("job_skills", job_skills)):
        key = f"silver/adzuna/{table}/{partition}/data.parquet"
        store.put(key, _to_parquet_bytes(frame))
        written[table] = key
        logger.info("silver write: %s (%d rows)", key, len(frame))
    return written
