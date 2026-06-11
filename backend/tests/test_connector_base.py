from collections.abc import Iterator

import pytest

import datalens.connectors  # noqa: F401  — triggers built-in connector registration
from datalens.connectors.base import (
    BaseConnector,
    ExtractBatch,
    UnknownConnectorError,
    available_connectors,
    get_connector_class,
    register_connector,
)


def test_builtin_adzuna_connector_is_registered() -> None:
    assert "adzuna" in available_connectors()
    assert get_connector_class("adzuna").source_name == "adzuna"


def test_register_decorator_adds_class_to_registry() -> None:
    @register_connector
    class FakeConnector(BaseConnector):
        source_name = "fake_test_source"

        def extract(self) -> Iterator[ExtractBatch]:
            yield ExtractBatch(name="only", payload=b"{}")

    assert get_connector_class("fake_test_source") is FakeConnector


def test_unknown_connector_raises_with_available_list() -> None:
    with pytest.raises(UnknownConnectorError, match="no_such_source"):
        get_connector_class("no_such_source")
