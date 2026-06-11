import json
from typing import Any

import httpx
import pytest

from datalens.connectors.adzuna import ADZUNA_BASE_URL, AdzunaConnector


def make_client(handler: Any) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=ADZUNA_BASE_URL)


def page_response(n_results: int) -> httpx.Response:
    return httpx.Response(200, json={"results": [{"id": i} for i in range(n_results)]})


def test_missing_credentials_raise_value_error() -> None:
    with pytest.raises(ValueError, match="credentials missing"):
        AdzunaConnector("", "")


def test_request_shape_includes_auth_and_search_params() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return page_response(0)

    connector = AdzunaConnector(
        "my-id",
        "my-key",
        country="au",
        category="it-jobs",
        results_per_page=2,
        client=make_client(handler),
    )
    list(connector.extract())

    assert len(requests) == 1
    url = requests[0].url
    assert url.path == "/v1/api/jobs/au/search/1"
    assert url.params["app_id"] == "my-id"
    assert url.params["app_key"] == "my-key"
    assert url.params["category"] == "it-jobs"
    assert url.params["results_per_page"] == "2"


def test_paginates_until_short_page_without_extra_request() -> None:
    pages = {1: page_response(2), 2: page_response(1)}
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.path.rsplit("/", 1)[-1])
        calls.append(page)
        return pages[page]

    connector = AdzunaConnector(
        "id", "key", results_per_page=2, max_pages=10, client=make_client(handler)
    )
    batches = list(connector.extract())

    assert calls == [1, 2]  # short page 2 ends the run; page 3 never requested
    assert [b.name for b in batches] == ["page_001", "page_002"]
    assert [b.record_count for b in batches] == [2, 1]
    assert json.loads(batches[0].payload)["results"] == [{"id": 0}, {"id": 1}]


def test_stops_at_max_pages_when_all_pages_full() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return page_response(2)

    connector = AdzunaConnector(
        "id", "key", results_per_page=2, max_pages=3, client=make_client(handler)
    )
    batches = list(connector.extract())

    assert len(batches) == 3


def test_stops_on_empty_first_page() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return page_response(0)

    connector = AdzunaConnector("id", "key", client=make_client(handler))
    assert list(connector.extract()) == []


def test_client_error_is_not_retried() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, json={"error": "bad key"})

    connector = AdzunaConnector("id", "key", client=make_client(handler))
    with pytest.raises(httpx.HTTPStatusError):
        list(connector.extract())
    assert len(calls) == 1


def test_server_error_is_retried_then_succeeds() -> None:
    responses = [httpx.Response(500), page_response(1)]

    def handler(request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    connector = AdzunaConnector("id", "key", results_per_page=2, client=make_client(handler))
    batches = list(connector.extract())

    assert len(batches) == 1
    assert batches[0].record_count == 1
