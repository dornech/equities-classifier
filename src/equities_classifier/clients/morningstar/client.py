"""Client for Morningstar."""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E303
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: PLR1702, PLR6301, RUF050, RUF105
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, no-any-return"

# fmt: off


from typing import Any, Self

from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from immutabledict import immutabledict
from dataclasses import fields

from selenium.webdriver.common.by import By
# import utils_seleniumxp
# import undetected_chromedriver as uc
import undetected as uc
from waitless import stabilize
from urllib.parse import urlencode
import json
import datetime

from equities_classifier.enums import DataSourceID, SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.models import (
    MorningstarRecord,
    MorningstarSearchResult
)
from equities_classifier.clients.clienthelper import ClientHelper
from equities_classifier.exceptions import ClientResponseError


class MorningstarResponseError(ClientResponseError):
    """Morningstar returned an error response."""


class MorningstarClient:
    """Morningstar HTTP / API client."""

    _BASE_URL = "https://global.morningstar.com"
    _SEARCH_URL = "https://global.morningstar.com/api/v1/en-eu/legacy-search/securities"
    _TOKEN_URL = "https://global.morningstar.com/api/v1/en-eu/oauth/token/"
    _PROFILE_URL = "https://api-global.morningstar.com/sal-service/v1/stock/data/companyProfile"

    _SEARCH_FIELDS: str = "baseCurrency,exchange,exchangeCountry,isin,name,shortName,ticker"

    _MORNINGSTAR_IDENTIFIER_TYPES: immutabledict[str, SecurityIdentifierType] = immutabledict({
        "isin": SecurityIdentifierType.ISIN,
        "ticker": SecurityIdentifierType.TICKER
    })

    _MORNINGSTAR_SEARCH_RESULT_MAP: immutabledict[tuple[str, ...], str | None] = immutabledict({
        ("meta", "securityID"): "security_id",
        ("meta", "performanceID"): "performance_id",
        ("meta", "companyID"): "company_id",
        ("meta", "exchange"): "exchange",
        ("meta", "universe"): "universe",
        ("meta", "ticker"): "ticker",

        ("fields", "exchange", "value"): None,
        ("fields", "exchange", "displayAs"): "exchange_name",

        ("fields", "exchangeCountry", "value"): "exchange_country",
        ("fields", "exchangeCountry", "displayAs"): "exchange_country_name",

        ("fields", "marketCap", "value"): None,
        ("fields", "marketCap", "properties"): None,
        ("fields", "marketCap", "properties", "asOfDate", "value"): None,
        ("fields", "marketCap", "properties", "currency", "value"): None,

        ("fields", "isin", "value"): "isin",
        ("fields", "name", "value"): "name",
        ("fields", "shortName", "value"): "short_name",
        ("fields", "ticker", "value"): None,
    })

    _MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_COMPLETE: immutabledict[tuple[str, ...], str | None] = immutabledict({
        ("businessDescription", "value"): "business_description",
        ("contact", "address1"): None,
        ("contact", "address2"): None,
        ("contact", "country"): None,
        ("contact", "phone"): None,
        ("contact", "fax"): None,
        ("contact", "email"): None,
        ("contact", "url"): None,
        ("sector", "value"): "sector",
        ("industry", "value"): "industry",
        ("mostRecentEarning", "value"): None,
        ("fiscalYearEnds", "value"): None,
        ("totalEmployees", "value"): None,
        ("totalEmployees", "date"): None,
    })

    # only usable for dictionary entries with "Value" attribute
    _MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_USED: immutabledict[str, str] = immutabledict({
        "businessDescription": "business_description",
        "sector": "sector",
        "industry": "industry",
    })

    @staticmethod
    def leaf_paths(
        data: Mapping[str, Any],
        path: tuple[str, ...] = (),
        exclude_leaves: Collection[str] = []
    ) -> list[tuple[str, ...]]:
        """Return all key paths from the root to every leaf."""

        result: list[tuple[str, ...]] = []

        for key, value in data.items():

            if key in exclude_leaves:
                continue

            current = (*path, key)
            if isinstance(value, Mapping):
                result.extend(MorningstarClient.leaf_paths(value, current, exclude_leaves))
            else:
                result.append(current)

        return result

    @staticmethod
    def _get_nested_value(data: dict[str, Any], path: tuple[str, ...], ) -> Any:
        """Return a nested value from a dictionary."""

        value: Any = data
        for key in path:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
            if value is None:
                return None

        return value

    def __init__(
        self,
        timeout: float = 30.0,
        seleniumwrapper: object | None = None,
        test_wo_browser: bool = False,
    ) -> None:
        """Initialize Morningstar client."""

        if not test_wo_browser:
            if seleniumwrapper is None:
                # self._client = utils_seleniumxp.init_webdriver(
                #     stealthmode=False,
                #     optimizedscraping=False,
                #     URL="https://global.morningstar.com/en-eu",
                #     browser="chrome",
                #     alt_cls_webdriverwrapper=uc.Chrome,
                #     alt_cls_options=uc.ChromeOptions,
                # )
                self._client = stabilize(uc.Chrome())
            else:
                self._client = seleniumwrapper
        else:
            self._client = None

        self._timeout = timeout

        self._access_token: str | None = None
        self._access_token_expires: datetime.date | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Release browser resources."""
        self._client.close()

    # public API

    def read_provider_base_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = True
    ) -> list[MorningstarRecord]:
        """Read base data for one or more identifiers from Morningstar."""

        records: list[MorningstarRecord] = []

        for source_identifier in source_identifiers:

            if source_identifier.type not in self._MORNINGSTAR_IDENTIFIER_TYPES.values():
                ClientHelper.invalid_security_type(
                    DataSourceID.MORNINGSTAR,
                    source_identifier.type,
                    source_identifier.value
                )
                continue

            response_data = self._execute_search_request(source_identifier)
            search_results = self._parse_search_results(
                source_identifier,
                response_data,
                raise_error,
            )
            search_results = [
                result for result in search_results
                if (
                       source_identifier.type == SecurityIdentifierType.ISIN
                       and result.isin == source_identifier.value
                )
                or (
                   source_identifier.type == SecurityIdentifierType.TICKER
                   and result.ticker == source_identifier.value
               )
            ]

            if search_results is not None:
                record = self._parse_record(source_identifier, search_results, raise_error)
                if record:
                    records.append(record)

        return records

    def read_provider_profile_data(
        self,
        records: list[MorningstarRecord],
        raise_error: bool = True
    ) -> list[MorningstarRecord]:
        """Read profile data from Morningstar."""

        for record in records:

            profile_data = self._execute_profile_request(security_id=record.company_id)
            record = self._parse_profile_to_record(profile_data, record, raise_error)

        return records

    # internal routines

    def _execute_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_param: Any | None = None
    ) -> Any:
        """Execute a Morningstar request."""

        # self._rate_limiter.wait()

        self._client.get(f"{url}?{urlencode(params)}" if params else url)
        response = self._client.find_element(By.XPATH, "//pre").text
        if response is None:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"Response from {DataSourceID.MORNINGSTAR} was None.",
                MorningstarResponseError,
            )

        response_data = json.loads(response)
        message_morningstar = response_data.get("message")
        if isinstance(message_morningstar, str):
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} sent following message: '{message_morningstar}'.",
                MorningstarResponseError,
            )

        return response_data

    def _execute_search_request(
        self,
        source_identifier: SecurityIdentifier,
    ) -> dict[str, Any]:
        """Execute a Morningstar security search request."""

        query = (
            f'(isin ~= "{source_identifier.value}")'
            if source_identifier.type == SecurityIdentifierType.ISIN
            else f'(ticker ~= "{source_identifier.value}")'
        )
        params = {
            "fields": self._SEARCH_FIELDS,
            "query": query,
            "limit": 100,
            # "asPageResponse": "false",
        }

        response = self._execute_request(method="GET", url=self._SEARCH_URL, params=params)

        return response

    def _parse_search_results(
        self,
        source_identifier: SecurityIdentifier,
        response_data: dict[str, Any],
        raise_error: bool = True
    ) -> list[MorningstarSearchResult]:
        """Parse Morningstar search response."""

        # clean response data, delete embracing dictionary if necessary
        if "page" in response_data:
            response_data = response_data["page"]

        if "results" not in response_data:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} search query result does not contain 'results'.",
                MorningstarResponseError if raise_error else None,
            )
            return []
        results = response_data["results"]
        if not isinstance(results, list):
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                 f"{DataSourceID.MORNINGSTAR} profile 'results' is not list (of dictionaries).",
                 MorningstarResponseError if raise_error else None,
            )
        if len(results) == 0:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} returned no search data.",
                MorningstarResponseError if raise_error else None,
            )
        if not results:
            return []

        search_results: list[MorningstarSearchResult] = []

        for item in results:

            missing = (
                self.leaf_paths(item, exclude_leaves=["score", "sortAs"]) -
                self._MORNINGSTAR_SEARCH_RESULT_MAP.keys())
            if len(missing) != 0:
                ClientHelper.unknown_provider_attributes(
                    DataSourceID.MORNINGSTAR,
                    missing,
                    "_MORNINGSTAR_SEARCH_RESULT_MAP"
                )

            result = MorningstarSearchResult(source_identifier=source_identifier)
            for path, attribute in self._MORNINGSTAR_SEARCH_RESULT_MAP.items():
                if attribute is not None:
                    value = self._get_nested_value(item, path)
                    if hasattr(result, attribute):
                        if value is not None:
                            setattr(result, attribute, value)
                    else:
                        ClientHelper.missing_record_attribute(
                            DataSourceID.MORNINGSTAR,
                            attribute,
                            value,
                        )

            search_results.append(result)

            count = response_data["count"] - len(response_data) + 1
            if count != len(search_results):
                ClientHelper.search_result_counter_issue(
                    DataSourceID.MORNINGSTAR,
                    source_identifier.type,
                    source_identifier.value,
                    count_provider=count,
                    count_found=len(response_data) + 1,
                )

        return search_results

    def _parse_record(
        self,
        source_identifier: SecurityIdentifier,
        search_results: Sequence[MorningstarSearchResult],
        raise_error: bool = False
    ) -> MorningstarRecord | None:
        """Parse Morningstar search result and create a MorningstarRecord."""

        if not search_results:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"No {DataSourceID.MORNINGSTAR} search results available.",
                MorningstarResponseError if raise_error else None,
            )
            return None

        record = MorningstarRecord()

        counter_ticker = Counter(search_result.ticker for search_result in search_results)
        if len({r.company_id for r in search_results}) != 1:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} CompanyID is not unique for selected identifier.",
                MorningstarResponseError if raise_error else None,
            )

        # Copy scalar fields from first search result. Consider differing tickers in case of ISIN search
        first = search_results[0]
        record.name = first.name or ""
        record.ticker = counter_ticker.most_common(1)[0][0]
        record.company_id = first.company_id
        record.universe = first.universe

        for search_result in search_results:

            # copy other provider fields
            for field in fields(search_result):
                if field.name != "ticker":
                    if hasattr(record, field.name):
                        target = getattr(record, field.name)
                        if isinstance(target, list):
                            # Preserve positional correspondence between all listing-specific attributes.
                            value = getattr(search_result, field.name, None)
                            target.append(value)
                        elif getattr(search_result, field.name) != getattr(record, field.name):
                            message = (
                                f"Inconsistency between Morningstar search results and modelling assumption: "
                                f"field '{field.name}' differs between listings."
                            )
                            raise MorningstarResponseError(message)
                    else:
                        ClientHelper.missing_record_attribute(
                            DataSourceID.MORNINGSTAR,
                            field.name,
                            getattr(search_result, field.name, None),
                        )
                else:
                    record.ticker_exchange.append(search_result.ticker)

        # Create canonical security identifiers (including source identifier).
        identifiers: list[SecurityIdentifier] = [source_identifier]
        for identifierfield_name, identifier_type in self._MORNINGSTAR_IDENTIFIER_TYPES.items():
            value = getattr(search_result, identifierfield_name)
            if value and identifier_type != source_identifier.type:
                identifiers.append(
                    SecurityIdentifier(
                        type=identifier_type,
                        value=value,
                    )
                )
        record.identifiers = identifiers

        return record

    def _access_token_expired(self) -> bool:
        """Return token expiration check."""

        return True

    def _get_access_token(self) -> str | None:
        """Return a Morningstar OAuth access token."""

        if self._access_token is None or self._access_token_expired():
            self._execute_access_token_request()

        return self._access_token

    def _execute_access_token_request(self) -> None:
        """Request a Morningstar OAuth access token."""

        response_data = self._execute_request(method="POST", url=self._TOKEN_URL)
        self._access_token = response_data.get("token")
        if self._access_token is None:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} response does not contain an accessToken.",
                MorningstarResponseError
            )

    def _execute_profile_request(
        self,
        security_id: str,
    ) -> dict[str, Any]:
        """Request the Morningstar company profile."""

        params = {
            "shareClassId": security_id,
            "access_token": self._get_access_token(),
        }
        response_data = self._execute_request(method="GET", url=self._PROFILE_URL, params=params)
        if not isinstance(response_data, dict):
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"Unexpected {DataSourceID.MORNINGSTAR} company profile response.",
                MorningstarResponseError
            )

        return response_data

    def _parse_profile_to_record(
        self,
        profile: dict[str, Any],
        record: MorningstarRecord,
        raise_error: bool = False
    ) -> MorningstarRecord:
        """Enrich a MorningstarRecord with company profile information."""

        if "sections" not in profile:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile does not contain 'sections'.",
                MorningstarResponseError if raise_error else None,
            )
            return record
        sections = profile.get("sections")
        if not isinstance(sections, dict):
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile 'sections' is not a dictionary.",
                MorningstarResponseError,
            )
            return record

        missing = (
            self.leaf_paths(sections, exclude_leaves=["label"]) -
            self._MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_COMPLETE.keys())
        if len(missing) != 0:
            ClientHelper.unknown_provider_attributes(
                DataSourceID.MORNINGSTAR,
                missing,
                "_MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_COMPLETE",
            )

        for json_name, section in sections.items():
            if not isinstance(section, dict):
                continue
            attribute = self._MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_USED.get(json_name)
            if attribute is not None:
                if hasattr(record, attribute):
                    setattr(record, attribute, section.get("value"))
                else:
                    ClientHelper.missing_record_attribute(
                        DataSourceID.MORNINGSTAR,
                        attribute,
                        section.get("value"),
                    )
            else:
                ClientHelper.unknown_provider_attribute(
                    DataSourceID.MORNINGSTAR,
                    json_name,
                    section.get("value"),
                )

        return record

    def _parse_profile_to_dict(
        self,
        profile: dict[str, Any],
        raise_error: bool = False,
    ) -> dict[str, Any]:
        """Parse a Morningstar company profile."""

        if "sections" not in profile:
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile does not contain 'sections'.",
                MorningstarResponseError if raise_error else None,
            )
            return {}
        sections = profile.get("sections")
        if not isinstance(sections, dict):
            ClientHelper.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile 'sections' is not a dictionary.",
                MorningstarResponseError if raise_error else None,
            )
            return {}

        provider_attributes: dict[str, Any] = {}

        missing = (
            self.leaf_paths(sections, exclude_leaves=["label"]) -
            self._MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_COMPLETE.keys())
        if len(missing) != 0:
            message = f"{DataSourceID.MORNINGSTAR} fields {missing} not considered in profile mapping."
            if raise_error:
                raise MorningstarResponseError(message)

        for json_name, section in sections.items():
            if not isinstance(section, dict):
                continue
            attribute = self._MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_USED.get(json_name)
            if attribute is not None:
                provider_attributes[attribute] = section.get("value")
            else:
                ClientHelper.unknown_provider_attribute(
                    provider=DataSourceID.MORNINGSTAR,
                    attribute=json_name,
                    value=section,
                )

        return provider_attributes


if __name__ == "__main__":

    pass
