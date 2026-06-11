from datetime import date

from datalens.connectors.base import ExtractBatch
from datalens.storage.object_store import ObjectStore

_EXTENSIONS = {
    "application/json": "json",
    "text/csv": "csv",
}


class BronzeWriter:
    """Writes raw extract batches to the bronze layer using a Hive-style key layout:

    bronze/{source}/ingest_date=YYYY-MM-DD/{batch_name}.{ext}
    """

    def __init__(self, store: ObjectStore) -> None:
        self._store = store

    def write(self, source: str, batch: ExtractBatch, ingest_date: date) -> str:
        ext = _EXTENSIONS.get(batch.content_type, "bin")
        key = f"bronze/{source}/ingest_date={ingest_date.isoformat()}/{batch.name}.{ext}"
        self._store.put(key, batch.payload)
        return key
