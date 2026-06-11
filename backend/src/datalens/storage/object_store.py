from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import boto3

from datalens.config import Settings

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


class ObjectStore(Protocol):
    """Minimal object-storage interface so pipeline code never touches boto3 directly."""

    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes: ...

    def list(self, prefix: str) -> list[str]: ...


class InMemoryObjectStore:
    """Dict-backed store for tests and offline development."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put(self, key: str, data: bytes) -> None:
        self._objects[key] = data

    def get(self, key: str) -> bytes:
        return self._objects[key]

    def list(self, prefix: str) -> list[str]:
        return sorted(k for k in self._objects if k.startswith(prefix))


class FilesystemObjectStore:
    """Maps object keys to files under a root directory.

    Used for the CI/dev fixture lake so DuckDB and dbt can read the same
    layout from a plain directory instead of S3.
    """

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)

    def put(self, key: str, data: bytes) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def list(self, prefix: str) -> list[str]:
        if not self._root.is_dir():
            return []
        return sorted(
            str(p.relative_to(self._root))
            for p in self._root.rglob("*")
            if p.is_file() and str(p.relative_to(self._root)).startswith(prefix)
        )

    def _resolve(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root.resolve()):
            raise ValueError(f"key {key!r} escapes store root")
        return path


class S3ObjectStore:
    """S3-compatible store; endpoint_url=None targets AWS S3, otherwise MinIO etc."""

    def __init__(
        self,
        bucket: str,
        *,
        client: "S3Client | None" = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str = "ap-southeast-2",
    ) -> None:
        self._bucket = bucket
        self._client = client or boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "S3ObjectStore":
        return cls(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
            region=settings.s3_region,
        )

    def put(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)

    def get(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return bytes(response["Body"].read())

    def list(self, prefix: str) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kwargs: dict[str, Any] = {"Bucket": self._bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            response = self._client.list_objects_v2(**kwargs)
            keys.extend(obj["Key"] for obj in response.get("Contents", []))
            if not response.get("IsTruncated"):
                return keys
            token = response.get("NextContinuationToken")
            if not token:
                raise RuntimeError(
                    "S3 returned IsTruncated=True without NextContinuationToken; "
                    "aborting to avoid an infinite pagination loop"
                )
