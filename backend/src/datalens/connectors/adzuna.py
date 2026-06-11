from collections.abc import Iterator

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from datalens.connectors.base import BaseConnector, ExtractBatch, register_connector

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api"


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


@register_connector
class AdzunaConnector(BaseConnector):
    """Pulls job postings from the Adzuna search API, one page per batch."""

    source_name = "adzuna"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        *,
        country: str = "au",
        category: str = "it-jobs",
        results_per_page: int = 50,
        max_pages: int = 5,
        client: httpx.Client | None = None,
    ) -> None:
        if not app_id or not app_key:
            raise ValueError(
                "Adzuna credentials missing — set DATALENS_ADZUNA_APP_ID and "
                "DATALENS_ADZUNA_APP_KEY (free signup at https://developer.adzuna.com/)"
            )
        self._app_id = app_id
        self._app_key = app_key
        self._country = country
        self._category = category
        self._results_per_page = results_per_page
        self._max_pages = max_pages
        self._client = client or httpx.Client(base_url=ADZUNA_BASE_URL, timeout=30.0)

    def extract(self) -> Iterator[ExtractBatch]:
        for page in range(1, self._max_pages + 1):
            response = self._fetch_page(page)
            results = response.json().get("results") or []
            if not results:
                return
            yield ExtractBatch(
                name=f"page_{page:03d}",
                payload=response.content,
                record_count=len(results),
            )
            if len(results) < self._results_per_page:
                return  # short page == last page; skip a wasted empty-page request

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=8),
        retry=retry_if_exception(_is_retryable),
    )
    def _fetch_page(self, page: int) -> httpx.Response:
        response = self._client.get(
            f"/jobs/{self._country}/search/{page}",
            params={
                "app_id": self._app_id,
                "app_key": self._app_key,
                "category": self._category,
                "results_per_page": self._results_per_page,
            },
        )
        response.raise_for_status()
        return response
