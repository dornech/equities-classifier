"""Client for Morningstar."""

# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E303
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: E501, N803, N806, PLR1702, PLR6301, RUF050, RUF105, S110, SIM102
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, no-any-return, union-attr"

# fmt: off


from typing import Any, Self

from collections import Counter
from collections.abc import Sequence
from immutabledict import immutabledict
from dataclasses import fields

import undetected as uc
from waitless import stabilize, get_diagnostics, StabilizationConfig, StabilizationTimeout
from waitless.diagnostics import print_report
from selenium.webdriver.common.by import By
from urllib.parse import urlencode
import json
import datetime
from iso3166 import countries

from equities_classifier.enums import DataSourceID, SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier, SecurityIdentifierList
from equities_classifier.exceptions import ClientResponseError
from equities_classifier.clients.clienthelper import (
    ClientHelperErrorHandler,
    get_primary_ticker, leaf_paths, get_nested_value
)
from equities_classifier.clients.morningstar.models import MorningstarRecord, MorningstarSearchResult


class MorningstarResponseError(ClientResponseError):
    """Morningstar returned an error response."""


class MorningstarClient:
    """Morningstar HTTP / API client."""

    # constants and related evaluation routines

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

        ("fields", "baseCurrency", "value"): None,

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
        ("mostRecentEarnings", "value"): None,
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

    # __init__, other ContextManager dunder routines and internal routines used within

    def __init__(
        self,
        timeout: float = 30.0,
        clean_nonUS_ticker: bool = False,
        test_wo_browser: bool = False,
    ) -> None:
        """Initialize Morningstar client."""

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
            try:
                config = StabilizationConfig(
                    timeout=10,  # Max wait time (seconds)
                    network_idle_threshold=5,  # Max pending requests (allows background traffic)
                    strictness='normal',  # 'strict' | 'normal' | 'relaxed'
                    debug_mode=False  # Enable logging
                )
                self._client = stabilize(self._client, config=config)
            except StabilizationTimeout as e:
                print("Failed to stabilize Chrome  with 'waitless'")
                diagnostics = get_diagnostics(self._client)
                print_report(diagnostics)  # Print detailed report
                raise e
        else:
            self._client = None

        self._timeout = timeout

        self._access_token: str | None = None
        self._access_token_expires: datetime.date | None = None

        self._clean_nonUS_ticker = clean_nonUS_ticker

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self._close()

    def _close(self) -> None:
        """Release browser resources."""

        # check self._client before execution due to potential double-close when using pytest
        if self._client:
            self._client.close()
            self._client = None

    # public API

    @classmethod
    def supports_identifier_type(cls, identifier_type: SecurityIdentifierType, ) -> bool:
        """Check if identifier type supported"""
        return identifier_type in cls._MORNINGSTAR_IDENTIFIER_TYPES.values()

    def read_provider_base_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = False
    ) -> list[MorningstarRecord]:
        """Read base data for one or more identifiers from Morningstar."""

        records: list[MorningstarRecord] = []

        for source_identifier in source_identifiers:

            if not self.supports_identifier_type(source_identifier.type):
                ClientHelperErrorHandler.invalid_security_type(DataSourceID.MORNINGSTAR, source_identifier)
                continue

            response_data = self._execute_search_request(source_identifier)
            search_results = self._parse_search_results(source_identifier, response_data, raise_error)
            search_results = [
                result for result in search_results
                if (
                        source_identifier.type == SecurityIdentifierType.ISIN
                        and result.isin == source_identifier.value
                   ) or (
                        source_identifier.type == SecurityIdentifierType.TICKER
                        and result.ticker == source_identifier.value_cleaned
                   )
            ]

            if search_results is not None:
                self._parse_records(source_identifier, search_results, records, raise_error)

        return records

    @staticmethod
    def check_and_set_primary_ticker(
        records: list[MorningstarRecord],
        set_ticker: bool = True,
        raise_error: bool = False,
    ) -> None:
        """Check and optionally set the primary ticker for Morningstar records."""

        for record in records:

            if not record.has_identifier(SecurityIdentifierType.ISIN):
                ClientHelperErrorHandler.unknown_identifier_type(
                    DataSourceID.OPENFIGI,
                    SecurityIdentifierType.ISIN,
                    record.name,
                    MorningstarResponseError if raise_error else None,
                )
                continue

            isin = record.identifier(SecurityIdentifierType.ISIN).value
            ticker_new = get_primary_ticker(
                DataSourceID.OPENFIGI,
                isin,
                record.name,
                record.ticker,
                record.ticker_exchange,
                record.exchange,
                MorningstarResponseError,
            )
            if ticker_new and set_ticker:
                record.ticker = ticker_new
                record.identifiers.replace(SecurityIdentifier(SecurityIdentifierType.TICKER, ticker_new))

    def read_provider_profile_data(
        self,
        records: list[MorningstarRecord],
        raise_error: bool = False
    ) -> None:
        """Read profile data from Morningstar."""

        for record in records:
            profile_data = self._execute_profile_request(
                security_id=record.company_id if record.company_id else record.performance_id[0]
            )
            self._parse_profile_to_record(profile_data, record, raise_error)

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
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"Response from {DataSourceID.MORNINGSTAR} was None.",
                MorningstarResponseError,
            )

        response_data = json.loads(response)
        message_morningstar = response_data.get("message")
        if isinstance(message_morningstar, str):
            ClientHelperErrorHandler.other_error_with_message(
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
            else f'(ticker ~= "{source_identifier.value_cleaned}")'
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
        raise_error: bool = False
    ) -> list[MorningstarSearchResult]:
        """Parse Morningstar search response."""

        # clean response data, delete embracing dictionary if necessary
        if "page" in response_data:
            response_data = response_data["page"]

        if "results" not in response_data:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} search query result does not contain 'results'.",
                MorningstarResponseError if raise_error else None,
            )
            return []
        results = response_data["results"]
        if not isinstance(results, list):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile 'results' is not list (of dictionaries).",
                MorningstarResponseError if raise_error else None,
            )
            return []
        if len(results) == 0:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} search result response for identifier {source_identifier.type} '{source_identifier.value}' does not contain any search result.",
            )
        if not results:
            return []

        search_results: list[MorningstarSearchResult] = []

        for item in results:

            if "fundID" in item["meta"]:
                continue

            missing = (
                leaf_paths(item, exclude_leaves=["score", "sortAs"]) -
                self._MORNINGSTAR_SEARCH_RESULT_MAP.keys()
            )
            if len(missing) != 0:
                ClientHelperErrorHandler.unknown_provider_attributes(
                    DataSourceID.MORNINGSTAR,
                    source_identifier,
                    missing,
                    "_MORNINGSTAR_SEARCH_RESULT_MAP"
                )

            result = MorningstarSearchResult(source_identifier=source_identifier)

            for path, attribute in self._MORNINGSTAR_SEARCH_RESULT_MAP.items():
                if attribute is not None:
                    value = get_nested_value(item, path)
                    if hasattr(result, attribute):
                        if value is not None:
                            setattr(result, attribute, value)
                    else:
                        ClientHelperErrorHandler.missing_record_attribute(
                            DataSourceID.MORNINGSTAR,
                            attribute,
                            value,
                            "_MORNINGSTAR_SEARCH_RESULT_MAP",
                        )

            search_results.append(result)

        if response_data["count"] != len(response_data["results"]):
            ClientHelperErrorHandler.search_result_counter_issue(
                DataSourceID.MORNINGSTAR,
                source_identifier,
                count_provider=response_data["count"],
                count_found=len(response_data["results"]),
            )

        return search_results

    def _parse_records(
        self,
        source_identifier: SecurityIdentifier,
        search_results: Sequence[MorningstarSearchResult],
        records: list[MorningstarRecord],
        raise_error: bool = False
    ) -> list[MorningstarRecord] | None:
        """Parse Morningstar search result and create a MorningstarRecord."""

        if not search_results:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"No {DataSourceID.MORNINGSTAR} search result available for identifier "
                f"{source_identifier.type} '{source_identifier.value}'.",
            )
            return None

        # delete non-stock search result entries
        for search_result in search_results:
            if search_result.universe not in {"EQ", "FC"}:
                ClientHelperErrorHandler.other_error_with_message(
                    DataSourceID.MORNINGSTAR,
                    f"{DataSourceID.MORNINGSTAR} search result contained non-equity result '{search_result.name}' "
                    f"for identifier {source_identifier.type} '{source_identifier.value}'. Deleted.",
                )
        search_results = [search_result for search_result in search_results if search_result.universe in {"EQ", "FC"}]

        # analyse search results - if ticker, check for country, otherwise valid ticker should preferably have
        # a US stock exchange registration
        if source_identifier.type == SecurityIdentifierType.TICKER:

            if source_identifier.country:

                try:
                    country_alpha2 = countries.get(source_identifier.country).alpha2
                    country_alpha3 = countries.get(source_identifier.country).alpha3
                    search_results = [
                        search_result
                        for search_result in search_results
                        if search_result.exchange_country in {country_alpha2, country_alpha3}
                    ]
                except Exception:
                    pass

            elif self._clean_nonUS_ticker:

                selected_name = None
                counter_name = Counter(search_result.name for search_result in search_results)
                if len(counter_name.most_common()) > 1:
                    for counted_name in counter_name.most_common():
                        for search_result in search_results:
                            if search_result.name == counted_name[0] and search_result.exchange_country == "USA":
                                selected_name = search_result.name
                                ClientHelperErrorHandler.other_error_with_message(
                                    DataSourceID.MORNINGSTAR,
                                    f"On {DataSourceID.MORNINGSTAR} '{selected_name}' is most mentioned security name "
                                    f"with US registration for identifier {source_identifier.type} '{source_identifier.value}'."
                                )
                                break

                if selected_name:
                    for search_result in search_results:
                        if search_result.name != selected_name:
                            ClientHelperErrorHandler.other_error_with_message(
                                DataSourceID.MORNINGSTAR,
                                f"{DataSourceID.MORNINGSTAR} search result contained non-US registered result "
                                f"'{search_result.name}' for identifier type {source_identifier.type} '{source_identifier.value}'. Deleted.",
                            )
                    search_results = [
                        search_result
                        for search_result in search_results
                        if search_result.name == selected_name
                    ]

        # cleaned everything :-(
        if not search_results:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} search result for identifier "
                f"{source_identifier.type} '{source_identifier.value}' empty after cleaning.",
            )
            return []

        for search_result in search_results:

            # Find existing record with ISIN (assumed standard field by Morningstar!) otherwise new record
            if search_result.isin:
                record = next(
                    (existing_record for existing_record in records
                        if existing_record.isin == search_result.isin
                    ),
                    None,
                )
            else:
                record = None

            if not record:

                record = MorningstarRecord()

                # Determine ticker
                if source_identifier.type == SecurityIdentifierType.ISIN:
                    try:
                        # Take ticker on exchange in country of registration from ISIN
                        country_alpha2 = countries.get(source_identifier.value[:2]).alpha2
                        country_alpha3 = countries.get(source_identifier.value[:2]).alpha3
                        counter_ticker = Counter(
                            search_result.ticker
                            for search_result in search_results
                            if search_result.exchange_country in {country_alpha2, country_alpha3}
                        )
                    except Exception:
                        # Take ticker on exchange mentioned most
                        counter_ticker = Counter(search_result.ticker for search_result in search_results)
                    if len(counter_ticker) > 0:
                        record.ticker = counter_ticker.most_common(1)[0][0]
                    else:
                        record.ticker = search_result.ticker
                elif source_identifier.type == SecurityIdentifierType.TICKER:
                    record.ticker = source_identifier.value_cleaned

                # Copy provider fields
                for field in fields(search_result):
                    if field.name != "ticker":
                        value = getattr(search_result, field.name, None)
                        if hasattr(record, field.name):
                            if isinstance(getattr(record, field.name), list):
                                # Preserve positional correspondence between all listing-specific attributes.
                                getattr(record, field.name).append(value)
                            else:
                                if getattr(record, field.name) and getattr(record, field.name) != value:
                                    ClientHelperErrorHandler.other_error_with_message(
                                        DataSourceID.MORNINGSTAR,
                                        f"Inconsistency between Morningstar search results and modelling"
                                        f"assumption: field '{field.name}' differs between listings. Current "
                                        f"value '{getattr(record, field.name)}', new '{value}'."
                                    )
                                setattr(record, field.name, value)
                        elif field.name not in {"source_identifier", "isin", "short_name"}:
                            # differences between MorningstarSearchResult and MorningstarRecord are intended
                            # -> probably delete error caller
                            ClientHelperErrorHandler.missing_record_attribute(
                                DataSourceID.MORNINGSTAR,
                                field.name,
                                getattr(search_result, field.name, None),
                                f"copy from {type(search_result).__name__} to {type(record).__name__}",
                            )
                record.ticker_exchange.append(getattr(search_result, "ticker", None))

                # Create canonical security identifiers (including source identifier).
                identifiers = SecurityIdentifierList([source_identifier])
                for identifier_field, identifier_type in self._MORNINGSTAR_IDENTIFIER_TYPES.items():
                    value = getattr(record, identifier_field)
                    if value and identifier_type != source_identifier.type:
                        identifiers.append(SecurityIdentifier(type=identifier_type, value=value))
                record.identifiers = identifiers

                records.append(record)

                if not record.company_id:
                    ClientHelperErrorHandler.other_error_with_message(
                        DataSourceID.MORNINGSTAR,
                        f"{DataSourceID.MORNINGSTAR} CompanyID not provided for "
                        f"{source_identifier.type} '{source_identifier.value}'.",
                    )

            else:

                # only add new values for existing list fields for entry with same ISIN
                for field in fields(search_result):
                    value = getattr(search_result, field.name, None)
                    if field.name != "ticker":
                        if hasattr(record, field.name) and isinstance(getattr(record, field.name), list):
                            getattr(record, field.name).append(value)
                record.ticker_exchange.append(getattr(search_result, "ticker", None))

    @staticmethod
    def _access_token_expired() -> bool:
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
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} response does not contain an accessToken.",
                MorningstarResponseError
            )

    def _execute_profile_request(self, security_id: str) -> dict[str, Any]:
        """Request the Morningstar company profile."""

        params = {
            "shareClassId": security_id,
            "access_token": self._get_access_token(),
        }
        response_data = self._execute_request(method="GET", url=self._PROFILE_URL, params=params)
        if not isinstance(response_data, dict):
            ClientHelperErrorHandler.other_error_with_message(
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
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile does not contain 'sections'.",
                MorningstarResponseError if raise_error else None,
            )
            return record
        sections = profile.get("sections")
        if not isinstance(sections, dict):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile 'sections' is not a dictionary.",
                MorningstarResponseError,
            )
            return record

        missing = (
            leaf_paths(sections, exclude_leaves=["label"]) -
            self._MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_COMPLETE.keys())
        if len(missing) != 0:
            ClientHelperErrorHandler.unknown_provider_attributes(
                DataSourceID.MORNINGSTAR,
                record.identifiers[0],
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
                    ClientHelperErrorHandler.missing_record_attribute(
                        DataSourceID.MORNINGSTAR,
                        attribute,
                        section.get("value"),
                        "_MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_USED",
                    )
            else:
                # do not report willingly not transfered fields
                # ClientHelperErrorHandler.unknown_provider_attribute(
                #     DataSourceID.MORNINGSTAR,
                #     record.identifiers[0],
                #     json_name,
                #     section.get("value"),
                #     "_MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_USED",
                # )
                pass

        return record

    def _parse_profile_to_dict(
        self,
        identifier: SecurityIdentifier,
        profile: dict[str, Any],
        raise_error: bool = False,
    ) -> dict[str, Any]:
        """Parse a Morningstar company profile."""

        if "sections" not in profile:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile does not contain 'sections'.",
                MorningstarResponseError if raise_error else None,
            )
            return {}
        sections = profile.get("sections")
        if not isinstance(sections, dict):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.MORNINGSTAR,
                f"{DataSourceID.MORNINGSTAR} profile 'sections' is not a dictionary.",
                MorningstarResponseError if raise_error else None,
            )
            return {}

        provider_attributes: dict[str, Any] = {}

        missing = (
            leaf_paths(sections, exclude_leaves=["label"]) -
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
                ClientHelperErrorHandler.unknown_provider_attribute(
                    DataSourceID.MORNINGSTAR,
                    identifier,
                    json_name,
                    section.get("value"),
                    "_MORNINGSTAR_PROFILE_SECTION_FIELDS_MAP_USED",
                )

        return provider_attributes


if __name__ == "__main__":

    pass
