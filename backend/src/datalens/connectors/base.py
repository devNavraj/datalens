from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractBatch:
    """One unit of raw extracted data, stored verbatim in the bronze layer."""

    name: str  # unique within a single run, e.g. "page_001"
    payload: bytes  # raw bytes exactly as received from the source
    content_type: str = "application/json"
    record_count: int | None = None


class BaseConnector(ABC):
    """A data source. Implementations yield raw batches; they never transform data."""

    source_name: str

    @abstractmethod
    def extract(self) -> Iterator[ExtractBatch]:
        """Yield raw batches from the source. Must be resumable from scratch (idempotent)."""


class UnknownConnectorError(KeyError):
    pass


_REGISTRY: dict[str, type[BaseConnector]] = {}


def register_connector[T: type[BaseConnector]](cls: T) -> T:
    _REGISTRY[cls.source_name] = cls
    return cls


def get_connector_class(name: str) -> type[BaseConnector]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise UnknownConnectorError(
            f"No connector registered as {name!r}. Available: {available_connectors()}"
        ) from exc


def available_connectors() -> list[str]:
    return sorted(_REGISTRY)
