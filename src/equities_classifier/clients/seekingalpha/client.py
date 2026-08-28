"""Client for Seeking Alpha."""


# ruff and mypy per file settings
#
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: PLR1702, RUF105
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, no-any-return, union-attr"


# fmt: off


from collections.abc import Sequence
from immutabledict import immutabledict

import json
import re

import undetected as uc

from equities_classifier.enums import DataSourceID, SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.exceptions import ClientResponseError
from equities_classifier.clients.clienthelper import ClientHelperErrorHandler, get_nested_value
from equities_classifier.clients.seekingalpha.models import SeekingAlphaRecord


class SeekingAlphaResponseError(ClientResponseError):
    """Seeking Alpha returned an error response."""


class SeekingAlphaClient:
    """HTTP client for Seeking Alpha."""

    _BASE_URL = "https://seekingalpha.com"
    _SYMBOL_URL = f"{_BASE_URL}/symbol"

    _SSR_DATA_PATTERN = re.compile(
        r"<script[^>]*>\s*window\.SSR_DATA\s*=\s*(?P<data>\{.*?)(?=;\s*</script>)",
        re.DOTALL
    )

    _SEEKINGALPHA_IDENTIFIER_TYPES: immutabledict[str, SecurityIdentifierType] = immutabledict({
        "ticker": SecurityIdentifierType.TICKER,
        "ticker_us": SecurityIdentifierType.TICKER_US
    })

    _SEEKINGALPHA_PROFILE_FIELDS_MAP: immutabledict[tuple[str, ...], str | None] = immutabledict({
        # symbol.response.data.attributes
        ("attributes", "name"): "ticker",
        ("attributes", "companyName"): "name",
        ("attributes", "equityType"): None,
        ("attributes", "indexGroup"): None,
        ("attributes", "currency"): None,
        ("attributes", "exchange"): "exchange",
        ("attributes", "exchangeTitle"): None,
        ("attributes", "companyPrimaryCurrency"): None,
        ("attributes", "tradingViewSlug"): None,
        ("attributes", "exchangeDescription"): None,
        ("attributes", "company"): None,
        ("attributes", "isBdc"): None,
        ("attributes", "visible"): None,
        ("attributes", "searchable"): None,
        ("attributes", "private"): None,
        ("attributes", "pending"): None,
        ("attributes", "isDefunct"): None,
        ("attributes", "followersCount"): None,
        ("attributes", "fundTypeId"): None,
        ("attributes", "articleTraCOunt"): None,
        ("attributes", "newsRtaCOunt"): None,
        ("attributes", "divYieldType"): None,
        ("attributes", "mergedOn"): None,
        ("attributes", "primaryEpsConsensusMeanType"): None,
        ("attributes", "mergedInto"): None,
        ("attributes", "mergedTickers"): None,
        ("attributes", "isReit"): None,
        ("attributes", "isEtn"): None,
        ("attributes", "tickerType"): None,
        ("attributes", "fundType"): None,
        ("attributes", "sectorDisplay"): "sector",
        ("attributes", "industryDisplay"): "subindustry",

        # symbol.response.relationships
        ("relationships", "sector", "data", "id"): "sector_code",
        ("relationships", "sector", "data", "type"): None,
        ("relationships", "subIndustry", "data", "id"): "subindustry_code",
        ("relationships", "subIndustry", "data", "type"): None,
    })

    # __init__, other ContextManager dunder routines and internal routines used within

    def __init__(
        self,
        timeout: float = 30.0,
        test_wo_browser: bool = False,
    ) -> None:
        """Initialize Seeking Alpha client."""

        self._client: uc.Chrome | None

        if not test_wo_browser:
            options = uc.ChromeOptions()
            # options.add_argument("--headless=new")   # does not work with Morningstar because CloudFront-detected
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            try:
                self._client = uc.Chrome(options=options)
            except Exception as e:
                print("Failed to start Chrome")
                raise e
        else:
            self._client = None

        self._timeout = timeout

    def __enter__(self) -> "SeekingAlphaClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._close()

    def _close(self) -> None:
        """Close HTTP client."""

        # check self._client before execution due to potential double-close when using pytest
        if self._client:
            self._client.close()
            self._client = None

    # public API

    @classmethod
    def supports_identifier_type(cls, identifier_type: SecurityIdentifierType) -> bool:
        """Return whether the provider supports an identifier type."""
        return identifier_type in cls._SEEKINGALPHA_IDENTIFIER_TYPES.values()

    def read_provider_profile_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = False,
    ) -> list[SeekingAlphaRecord]:
        """Read profile data from SeekingAlpha."""

        records: list[SeekingAlphaRecord] = []

        for source_identifier in source_identifiers:

            if not self.supports_identifier_type(source_identifier.type):
                ClientHelperErrorHandler.invalid_security_type(DataSourceID.SEEKINGALPHA, source_identifier)
                continue

            response = self._execute_request(source_identifier, raise_error)
            record = self._parse_record(source_identifier, response, raise_error)
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

    def _execute_request(
        self,
        source_identifier: SecurityIdentifier,
        raise_error: bool,
    ) -> str | None:
        """Read a Seeking Alpha symbol page."""

        url = f"{self._SYMBOL_URL}/{source_identifier.value_cleaned}"

        try:
            self._client.get(self._BASE_URL)
            self._client.get(url)
        except Exception as exc:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.SEEKINGALPHA,
                f"HTTP request to SeekingAlpha failed for ticker_us"
                f"'{source_identifier.value}': {exc}",
                SeekingAlphaResponseError if raise_error else None,
            )
            return None

        # return response.text
        return self._client.page_source

    def _parse_record(
        self,
        source_identifier: SecurityIdentifier,
        html: str,
        raise_error: bool,
    ) -> SeekingAlphaRecord | None:
        """Extract and decode window.SSR_DATA from HTML."""

        match = self._SSR_DATA_PATTERN.search(html)

        if match is None:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.SEEKINGALPHA,
                f"SeekingAlpha response for identifier ticker_us"
                f"'{source_identifier.value}' does not contain SSR_DATA.",
                SeekingAlphaResponseError if raise_error else None,
            )
            return None

        try:
            data = json.loads(match.group("data"))
        except json.JSONDecodeError as exc:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.SEEKINGALPHA,
                f"Could not decode SSR_DATA for identifier ticker_us "
                f"'{source_identifier.value}': {exc}",
                SeekingAlphaResponseError if raise_error else None,
            )
            return None
        if not isinstance(data, dict):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.SEEKINGALPHA,
                "Seeking Alpha SSR_DATA is not a dictionary.",
                SeekingAlphaResponseError if raise_error else None,
            )
            return None

        symbol = data.get("symbol")
        if not isinstance(symbol, dict):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.SEEKINGALPHA,
                "Seeking Alpha SSR_DATA does not contain 'symbol'.",
                SeekingAlphaResponseError if raise_error else None,
            )
            return None

        response = symbol.get("response")
        if not isinstance(response, dict):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.SEEKINGALPHA,
                "Seeking Alpha SSR_DATA 'symbol' does not contain "
                "'response'.",
                SeekingAlphaResponseError if raise_error else None,
            )
            return None

        data = response.get("data")
        if not isinstance(data, dict):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.SEEKINGALPHA,
                "Seeking Alpha SSR_DATA 'response' -> 'response' does not contain "
                "'data'.",
                SeekingAlphaResponseError if raise_error else None,
            )
            return None

        record = SeekingAlphaRecord()

        for path, attribute in self._SEEKINGALPHA_PROFILE_FIELDS_MAP.items():
            if attribute is not None:
                value = get_nested_value(data, path)
                if hasattr(record, attribute):
                    if value is not None:
                        setattr(record, attribute, value)
                else:
                    ClientHelperErrorHandler.missing_record_attribute(
                        DataSourceID.MORNINGSTAR,
                        attribute,
                        value,
                        "_SEEKINGALPHA_PROFILE_FIELDS_MAP",
                    )
        record.ticker_us = record.ticker
        record.identifiers.append(source_identifier)

        return record
