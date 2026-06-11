from pathlib import Path

import pytest

from datalens.storage import FilesystemObjectStore


def test_put_get_list_roundtrip(tmp_path: Path) -> None:
    store = FilesystemObjectStore(tmp_path)
    store.put("silver/adzuna/job_postings/ingest_date=2026-06-10/data.parquet", b"pq")
    store.put("bronze/adzuna/ingest_date=2026-06-10/page_001.json", b"{}")

    assert store.get("bronze/adzuna/ingest_date=2026-06-10/page_001.json") == b"{}"
    assert store.list("silver/") == [
        "silver/adzuna/job_postings/ingest_date=2026-06-10/data.parquet"
    ]
    assert store.list("nope/") == []


def test_list_on_missing_root_is_empty(tmp_path: Path) -> None:
    assert FilesystemObjectStore(tmp_path / "missing").list("") == []


def test_key_escaping_root_rejected(tmp_path: Path) -> None:
    store = FilesystemObjectStore(tmp_path / "lake")
    with pytest.raises(ValueError, match="escapes store root"):
        store.put("../outside.txt", b"x")
