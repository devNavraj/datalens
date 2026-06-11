import io

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from datalens.storage import InMemoryObjectStore, S3ObjectStore


class TestInMemoryObjectStore:
    def test_put_then_get_roundtrip(self) -> None:
        store = InMemoryObjectStore()
        store.put("bronze/a.json", b'{"x": 1}')
        assert store.get("bronze/a.json") == b'{"x": 1}'

    def test_get_missing_key_raises(self) -> None:
        store = InMemoryObjectStore()
        with pytest.raises(KeyError):
            store.get("nope")

    def test_list_filters_by_prefix_and_sorts(self) -> None:
        store = InMemoryObjectStore()
        store.put("bronze/b.json", b"2")
        store.put("bronze/a.json", b"1")
        store.put("silver/c.parquet", b"3")
        assert store.list("bronze/") == ["bronze/a.json", "bronze/b.json"]
        assert store.list("gold/") == []


@pytest.fixture
def s3_stub() -> tuple[S3ObjectStore, Stubber]:
    client = boto3.client(
        "s3",
        region_name="ap-southeast-2",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    return S3ObjectStore(bucket="datalens", client=client), Stubber(client)


class TestS3ObjectStore:
    def test_put_sends_put_object(self, s3_stub: tuple[S3ObjectStore, Stubber]) -> None:
        store, stub = s3_stub
        stub.add_response(
            "put_object",
            {},
            {"Bucket": "datalens", "Key": "bronze/x.json", "Body": b"data"},
        )
        with stub:
            store.put("bronze/x.json", b"data")
        stub.assert_no_pending_responses()

    def test_get_reads_body_bytes(self, s3_stub: tuple[S3ObjectStore, Stubber]) -> None:
        store, stub = s3_stub
        stub.add_response(
            "get_object",
            {"Body": StreamingBody(io.BytesIO(b"payload"), 7)},
            {"Bucket": "datalens", "Key": "bronze/x.json"},
        )
        with stub:
            assert store.get("bronze/x.json") == b"payload"

    def test_list_raises_on_truncated_response_without_token(
        self, s3_stub: tuple[S3ObjectStore, Stubber]
    ) -> None:
        store, stub = s3_stub
        stub.add_response(
            "list_objects_v2",
            {"Contents": [{"Key": "bronze/a.json"}], "IsTruncated": True},
            {"Bucket": "datalens", "Prefix": "bronze/"},
        )
        with stub, pytest.raises(RuntimeError, match="NextContinuationToken"):
            store.list("bronze/")

    def test_list_paginates_until_not_truncated(
        self, s3_stub: tuple[S3ObjectStore, Stubber]
    ) -> None:
        store, stub = s3_stub
        stub.add_response(
            "list_objects_v2",
            {
                "Contents": [{"Key": "bronze/a.json"}],
                "IsTruncated": True,
                "NextContinuationToken": "tok",
            },
            {"Bucket": "datalens", "Prefix": "bronze/"},
        )
        stub.add_response(
            "list_objects_v2",
            {"Contents": [{"Key": "bronze/b.json"}], "IsTruncated": False},
            {"Bucket": "datalens", "Prefix": "bronze/", "ContinuationToken": "tok"},
        )
        with stub:
            assert store.list("bronze/") == ["bronze/a.json", "bronze/b.json"]
        stub.assert_no_pending_responses()
