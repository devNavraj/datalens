from collections.abc import Iterator
from datetime import date

from datalens.connectors import BaseConnector, ExtractBatch
from datalens.ingest import run_ingest
from datalens.storage import InMemoryObjectStore


class TwoBatchConnector(BaseConnector):
    source_name = "stub"

    def extract(self) -> Iterator[ExtractBatch]:
        yield ExtractBatch(name="page_001", payload=b'{"results": [1]}', record_count=1)
        yield ExtractBatch(name="page_002", payload=b'{"results": [2]}', record_count=1)


def test_run_ingest_writes_every_batch_to_bronze() -> None:
    store = InMemoryObjectStore()

    keys = run_ingest(TwoBatchConnector(), store, ingest_date=date(2026, 6, 10))

    assert keys == [
        "bronze/stub/ingest_date=2026-06-10/page_001.json",
        "bronze/stub/ingest_date=2026-06-10/page_002.json",
    ]
    assert store.list("bronze/stub/") == keys
    assert store.get(keys[1]) == b'{"results": [2]}'


def test_run_ingest_defaults_to_today() -> None:
    store = InMemoryObjectStore()

    keys = run_ingest(TwoBatchConnector(), store)

    assert f"ingest_date={date.today().isoformat()}" in keys[0]
