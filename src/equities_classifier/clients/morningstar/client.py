"""Client for Morningstar."""


from typing import Self

import httpx
from bs4 import BeautifulSoup

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.models import (
    MorningstarRecord,
    MorningstarSearchResult
)
from equities_classifier.exceptions import (
    ClientAuthenticationError,
    ClientConnectionError,
    ClientResponseError
)

class MorningstarClient:
    """Morningstar HTTP client."""

    BASE_URL = "https://global.morningstar.com"

    def __init__(
        self,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the HTTP client."""

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._client = httpx.Client(
            headers=headers,
            timeout=timeout,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def map(
        self,
        identifier: SecurityIdentifier,
    ) -> MorningstarRecord | None:
        """Read Morningstar classification for a security."""

        search_result = self._search(identifier)
        if search_result is None:
            return None

        return self._read_classification(search_result)

    def _search(
        self,
        identifier: SecurityIdentifier,
    ) -> MorningstarSearchResult | None:
        """Search a security on Morningstar."""

        try:
            response = self._client.get(
                f"{self.BASE_URL}/en-eu/search/securities",
                params={"query": identifier.value},
            )
        except httpx.ConnectError as exc:
            raise ClientConnectionError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            raise ClientConnectionError(str(exc)) from exc
        match response.status_code:
            case 401 | 403:
                raise ClientAuthenticationError(response.text)
            case _:
                response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for result in soup.select("li.mdc-search-page-results__result__mdc"):

            link = result.select_one("a.mdc-search-page-results__result-link__mdc")
            if link is None:
                continue

            meta = [
                item.get_text(strip=True)
                for item in result.select("li.mdc-search-page-results__result-meta-item__mdc")
            ]
            if len(meta) != 5:
                continue

            search_result = MorningstarSearchResult(
                identifier=identifier,
                url=f"{self.BASE_URL}{link['href']}",
                company_name=link.get_text(strip=True),
                instrument_type=meta[0],
                exchange=meta[1],
                country=meta[2],
                ticker=meta[3],
                currency=meta[4],
            )
            if search_result.instrument_type != "Stock":
                continue
            if identifier.type == SecurityIdentifierType.ISIN:
                return search_result
            if (
                identifier.type == SecurityIdentifierType.TICKER
                and search_result.ticker == identifier.value
            ):
                return search_result

        return None

    def _read_classification(
        self,
        result: MorningstarSearchResult,
    ) -> MorningstarRecord:
        """Read the Morningstar quote page."""

        try:
            response = self._client.get(result.url)
        except httpx.ConnectError as exc:
            raise ClientConnectionError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            raise ClientConnectionError(str(exc)) from exc
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        record = MorningstarRecord(
            identifier=result.identifier,
            company_name=result.company_name
        )

        # Locate all label/value pairs.
        for row in soup.select("dl, table tr, li"):
            text = row.get_text(" ", strip=True)
            if not text:
                continue
            if text.startswith("Sector"):
                record.sector = text.removeprefix("Sector").strip()
            elif text.startswith("Industry"):
                record.industry = text.removeprefix("Industry").strip()

        record.provider_attributes = {
            "url": result.url,
            "exchange": result.exchange,
            "country": result.country,
            "ticker": result.ticker,
            "currency": result.currency,
        }

        return record


if __name__ == "__main__":
    client = MorningstarClient()

    identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "US0378331005",
    )

    with client:
        record = client.map(identifier)

    print(record)
