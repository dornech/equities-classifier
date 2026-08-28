"""Client for Yahoo Finance."""


# ruff and mypy per file settings
#
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: PLC2701, PLR1702, RUF105
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, assignment, no-any-return"

# fmt: off


from typing import Any, Self
from collections.abc import Sequence
from immutabledict import immutabledict

import httpx
from equities_classifier.clients.httpx_logger import log_request, log_response

from finance_enums import exchange_records_by_market_category
from yfinance.const import _MIC_TO_YAHOO_SUFFIX

from equities_classifier.enums import DataSourceID, SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier, SecurityIdentifierList
from equities_classifier.exceptions import ClientConnectionError, ClientResponseError
from equities_classifier.clients.clienthelper import ClientHelperErrorHandler
from equities_classifier.clients.yahoo.models import YahooSearchResult, YahooRecord


def _build_yahoo_suffix_to_countries() -> dict[str, str]:
    """Build Yahoo Finance suffix to ISO country-code mapping."""

    exchanges = exchange_records_by_market_category("RMKT")
    country_by_mic = {
        exchange.operating_mic: exchange.iso_country_code
        for exchange in exchanges
    }
    return {
        suffix: country_by_mic[mic]
        for mic, suffix in _MIC_TO_YAHOO_SUFFIX.items()
        if mic in country_by_mic
    }


_YAHOO_SUFFIX_TO_COUNTRIES = _build_yahoo_suffix_to_countries()


class YahooResponseError(ClientResponseError):
    """Yahoo Finance returned an invalid response."""


class YahooClient:
    """Yahoo Finance HTTP client."""

    _BASE_URL = "https://query1.finance.yahoo.com"
    _SEARCH_URL = "/v1/finance/search"

    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )

    _YAHOO_IDENTIFIER_TYPES: immutabledict[str, SecurityIdentifierType] = immutabledict({
        "isin": SecurityIdentifierType.ISIN,
        "ticker": SecurityIdentifierType.TICKER
    })

    _YAHOO_SEARCH_RESULT_MAP: immutabledict[str, str] = immutabledict({
        "shortname": "shortname",
        "longname": "longname",
        "symbol": "symbol",
        "index": "index",
        "quoteType": "quote_type",
        "typeDisp": "type_disp",
        "exchange": "exchange",
        "exchDisp": "exch_disp",
        "sector": "sector",
        "sectorDisp": "sector_disp",
        "industry": "industry",
        "industryDisp": "industry_disp",
        "score": "score",
    })

    # __init__, other ContextManager dunder routines and internal routines used within

    def __init__(
        self,
        timeout: float = 30.0,
        requestlog: bool = False,
    ) -> None:
        """Initialize Yahoo Finance client."""

        _client: httpx.Client | None

        self._client = httpx.Client(
            base_url=self._BASE_URL,
            timeout=timeout,
            follow_redirects=True,
            event_hooks={"request": [log_request], "response": [log_response]} if requestlog else None,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self._close()

    def _close(self) -> None:
        """Release client resources."""

        # check self._client before execution due to potential double-close when using pytest
        if self._client:
            self._client.close()
            self._client = None

    # public API

    @classmethod
    def supports_identifier_type(cls, identifier_type: SecurityIdentifierType) -> bool:
        """Check if identifier type is supported."""
        return identifier_type in cls._YAHOO_IDENTIFIER_TYPES.values()

    def read_provider_profile_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = False,
    ) -> list[YahooRecord]:
        """Read profile data for identifiers from Yahoo Finance."""

        records: list[YahooRecord] = []

        for source_identifier in source_identifiers:

            if not self.supports_identifier_type(source_identifier.type):
                ClientHelperErrorHandler.invalid_security_type(DataSourceID.YAHOO, source_identifier)
                continue

            response_data = self._execute_search_request(source_identifier)
            search_results = self._parse_search_results(source_identifier, response_data, raise_error)
            if search_results is None or len(search_results) == 0:
                continue

            record = self._parse_record(source_identifier, search_results[0])
            # check for duplicates
            if record:
                duplicate = False
                for existing_record in records:
                    if record.name == existing_record.name:
                        duplicate = True
                        for identifier in record.identifiers:
                            if not existing_record.has_identifier(identifier.type):
                                existing_record.identifiers.append(identifier)
                if not duplicate:
                    records.append(record)

        return records

    # internal routines

    def _execute_search_request(
        self,
        identifier: SecurityIdentifier,
    ) -> dict[str, Any]:
        """Execute Yahoo Finance search request."""

        try:
            response = self._client.get(
                self._SEARCH_URL,
                params={"q": (identifier.value_cleaned or "").replace(" ", "-")},
                headers={"User-Agent": self._USER_AGENT},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ClientConnectionError(str(exc)) from exc
        except ValueError as exc:
            message = f"Invalid JSON response from {DataSourceID.YAHOO}."
            raise YahooResponseError(message) from exc

    def _parse_search_results(
        self,
        source_identifier: SecurityIdentifier,
        response: dict[str, Any],
        raise_error: bool = True,
    ) -> list[YahooSearchResult]:
        """Parse Yahoo Finance search results."""

        if "quotes" not in response:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.YAHOO,
                f"{DataSourceID.YAHOO} search query result does not contain 'quotes'.",
                YahooResponseError if raise_error else None,
            )
            return []

        quotes = response["quotes"]

        if not isinstance(quotes, list):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.YAHOO,
                (
                    f"{DataSourceID.YAHOO} search response for identifier "
                    f"({source_identifier.type}, {source_identifier.value}) "
                    "does not contain any search results."
                ),
                YahooResponseError if raise_error else None,
            )
            return []

        results: list[YahooSearchResult] = []

        for item in quotes:
            if not isinstance(item, dict):
                continue

            result = YahooSearchResult()

            for json_name, attribute in self._YAHOO_SEARCH_RESULT_MAP.items():
                value = item.get(json_name)
                if hasattr(result, attribute):
                    setattr(result, attribute, value)
                else:
                    ClientHelperErrorHandler.missing_record_attribute(
                        DataSourceID.YAHOO,
                        attribute,
                        value,
                        "_YAHOO_SEARCH_RESULT_MAP",
                    )
            results.append(result)

        return results

    @staticmethod
    def _parse_record(
        source_identifier: SecurityIdentifier,
        search_result: YahooSearchResult,
    ) -> YahooRecord | None:
        """Create Yahoo Finance provider record."""

        if not search_result:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.YAHOO,
                f"No {DataSourceID.YAHOO} search result available for identifier "
                f"{source_identifier.type} '{source_identifier.value}'.",
            )
            return None

        record = YahooRecord()

        record.name = search_result.longname
        record.ticker_yahoo = search_result.symbol
        record.exchange = search_result.exchange
        record.exch_disp = search_result.exch_disp
        record.sector = search_result.sector
        record.industry = search_result.industry

        if source_identifier.type == SecurityIdentifierType.ISIN:
            record.identifiers = SecurityIdentifierList([source_identifier])
        if record.ticker_yahoo and "." in record.ticker_yahoo:
            record.ticker, suffix = record.ticker_yahoo.split(".")
            country = _YAHOO_SUFFIX_TO_COUNTRIES.get(suffix)
        else:
            record.ticker = record.ticker_yahoo
            country = "US"
        if source_identifier.type == SecurityIdentifierType.ISIN:
            if country != source_identifier.value:
                ClientHelperErrorHandler.inconsistent_provider_data(
                    DataSourceID.YAHOO,
                    record.name,
                    "country of standard Yahoo suffix does not match with ISIN country",
                )
            record.identifiers.append(
                SecurityIdentifier(SecurityIdentifierType.TICKER, str(record.ticker or "") + "." + str(country or ""))
            )
        else:
            record.identifiers.append(
                SecurityIdentifier(SecurityIdentifierType.TICKER, record.ticker)
            )

        return record
