from datetime import date

from datalens.connectors import BronzeWriter, ExtractBatch
from datalens.storage import InMemoryObjectStore


def test_write_uses_hive_style_key_layout_and_stores_payload() -> None:
    store = InMemoryObjectStore()
    writer = BronzeWriter(store)
    batch = ExtractBatch(name="page_001", payload=b'{"results": []}')

    key = writer.write("adzuna", batch, date(2026, 6, 10))

    assert key == "bronze/adzuna/ingest_date=2026-06-10/page_001.json"
    assert store.get(key) == b'{"results": []}'


def test_write_maps_unknown_content_type_to_bin_extension() -> None:
    store = InMemoryObjectStore()
    writer = BronzeWriter(store)
    batch = ExtractBatch(name="blob", payload=b"\x00", content_type="application/octet-stream")

    key = writer.write("upload", batch, date(2026, 6, 10))

    assert key.endswith("/blob.bin")


def test_csv_content_type_gets_csv_extension() -> None:
    store = InMemoryObjectStore()
    writer = BronzeWriter(store)
    batch = ExtractBatch(name="orders", payload=b"a,b\n1,2\n", content_type="text/csv")

    key = writer.write("upload", batch, date(2026, 6, 10))

    assert key == "bronze/upload/ingest_date=2026-06-10/orders.csv"
