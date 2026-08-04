"""Client for Morningstar."""


from typing import Any, Self

from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from dataclasses import fields

import utils_seleniumxp
import undetected_chromedriver as uc
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
from equities_classifier.exceptions import (
    ClientAuthenticationError,
    ClientConnectionError,
    ClientRateLimitError,
    ClientResponseError
)


class MorningstarResponseError(ClientResponseError):
    """Morningstar returned an error response."""


class MorningstarClient:
    """Morningstar HTTP / API client."""

    _BASE_URL = "https://global.morningstar.com"
    _SEARCH_URL = "https://global.morningstar.com/api/v1/en-eu/legacy-search/securities"
    _TOKEN_URL = "https://global.morningstar.com/api/v1/en-eu/oauth/token/"
    _PROFILE_URL = "https://api-global.morningstar.com/sal-service/v1/stock/data/companyProfile"

    _SEARCH_FIELDS = (
        "baseCurrency,"
        "exchange,"
        "exchangeCountry,"
        "isin,"
        "name,"
        "shortName,"
        "ticker"
    )

    _MORNINGSTAR_IDENTIFIER_MAP: dict[str, SecurityIdentifierType] = {
        "isin": SecurityIdentifierType.ISIN,
        "ticker": SecurityIdentifierType.TICKER
    }

    _MORNINGSTAR_SEARCH_RESULT_MAP = {
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
    }

    _MORNINGSTAR_PROFILE_FIELD_MAP: dict[str, str] = {
        "businessDescription": "business_description",
        "sector": "sector",
        "industry": "industry",
    }

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

            current = path + (key,)
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
        seleniumwrapper: utils_seleniumxp.WebDriver = None,
        test_wo_browser: bool = False,
    ) -> None:
        """Initialize Morningstar client."""

        if not test_wo_browser:
            if seleniumwrapper is None:
                self._client = utils_seleniumxp.init_webdriver(
                    stealthmode=False,
                    optimizedscraping=False,
                    URL="https://global.morningstar.com/en-eu",
                    browser = "chrome",
                    alt_cls_webdriverwrapper = uc.Chrome,
                    alt_cls_options = uc.ChromeOptions,
                )
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

    def read_provider_base_data(
        self,
        identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = True
    ) -> list[MorningstarRecord]:
        """Read base date for one or more identifiers from Morningstar."""

        records: list[MorningstarRecord] = []

        for source_identifier in identifiers:

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
                record = self._parse_record(source_identifier,  search_results,  raise_error)
                records.append(record)

        return records

    def read_provider_profile_data(
        self,
        records: list[MorningstarRecord],
        raise_error: bool = True
    ) -> list[MorningstarRecord]:
        """Read profile data from Morningstar."""

        for record in records:

            profile_data = self._execute_profile_request(security_id = record.company_id)
            record = self._parse_profile_to_record(profile_data, record,raise_error)

        return records

    def _execute_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_param: Any  | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Execute a Morningstar request."""

        # self._rate_limiter.wait()

        self._client.get(f"{url}?{urlencode(params)}")
        response = self._client.find_element(utils_seleniumxp.By.XPATH, "//pre").text

        response_data = json.loads(response)

        return response_data

    def _execute_search_request(
        self,
        source_identifier: SecurityIdentifier,
    ) ->list[dict[str, Any]]:
        """Execute a Morningstar security search request."""

        query = (
            f'(isin ~= "{source_identifier.value}")'
            if source_identifier.type == SecurityIdentifierType.ISIN
            else f'(ticker ~= "{source_identifier.value}")'
        )
        params = {
            "fields": self._SEARCH_FIELDS,
            "query": query
        }

        return self._execute_request(method="GET", url=self._SEARCH_URL, params=params)

    def _parse_search_results(
        self,
        source_identifier: SecurityIdentifier,
        response_data: list[dict[str, Any]],
        raise_error: bool = True
    ) -> list[MorningstarSearchResult]:
        """Parse Morningstar search response."""

        count = response_data["count"] - len(response_data) + 1
        if count == 0:
            message = f"{DataSourceID.MORNINGSTAR} returned no search data."
            if raise_error:
                raise MorningstarResponseError(message)

        search_results: list[MorningstarSearchResult] = []

        for item in response_data["results"]:

            missing = self.leaf_paths(item,  exclude_leaves=["score", "sortAs"]) - self._MORNINGSTAR_SEARCH_RESULT_MAP.keys()
            if len(missing) != 0:
                message = f"{DataSourceID.MORNINGSTAR} fields {missing} not considered in search result mapping."
                if raise_error:
                    raise MorningstarResponseError(message)

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

        if count != len(search_results):
            message = f"{DataSourceID.MORNINGSTAR} returned inconsistent data or error in evaluation."
            if raise_error:
                raise MorningstarResponseError(message)

        return search_results

    def _parse_record(
        self,
        source_identifier: SecurityIdentifier,
        search_results: Sequence[MorningstarSearchResult],
        raise_error: bool = False
    ) -> MorningstarRecord:
        """Parse Morningstar search result and create a MorningstarRecord."""

        if not search_results:
            message = f"No {DataSourceID.MORNINGSTAR} search results available."
            if raise_error:
                raise MorningstarResponseError(message)

        record = MorningstarRecord()

        counter_ticker = Counter(search_result.ticker for search_result in search_results)
        if len(set(r.company_id for r in search_results)) != 1:
            message = f"{DataSourceID.MORNINGSTAR} CompanyID is not unique for selected identifier."
            raise MorningstarResponseError(message)

        # Copy scalar fields from first search result. Consider differing tickers in Case of ISIN search
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
                        else:
                            if getattr(search_result, field.name) != getattr(record, field.name):
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
        for attribute, identifier_type in self._MORNINGSTAR_IDENTIFIER_MAP.items():
            value = getattr(search_result, attribute)
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

    def _get_access_token(self) -> str:
        """Return a Morningstar OAuth access token."""

        if self._access_token is None or self._access_token_expired():
            self._access_token = self._execute_access_token_request()

        return self._access_token

    def _execute_access_token_request(self) -> None:
        """Request a Morningstar OAuth access token."""

        response_data = self._execute_request(method="POST", url=self._TOKEN_URL)
        self._access_token = response_data.get("token")
        if self._access_token is None:
            message = f"{DataSourceID.MORNINGSTAR} response does not contain an accessToken."
            raise MorningstarResponseError(message)

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
            message = f"Unexpected {DataSourceID.MORNINGSTAR} company profile response."
            raise MorningstarResponseError(message)

        return response_data

    def _parse_profile_to_record(
        self,
        profile: dict[str, Any],
        record: MorningstarRecord,
        raise_error: bool = False
    ) -> MorningstarRecord:
        """Enrich a MorningstarRecord with company profile information."""

        sections = profile.get("sections")
        if not isinstance(sections, dict):
            message = f"{DataSourceID.MORNINGSTAR} profile does not contain 'sections'."
            if raise_error:
                raise MorningstarResponseError(message)

        if isinstance(sections, dict):

            for json_name, section in sections.items():
                if not isinstance(section, dict):
                    continue
                attribute = self._MORNINGSTAR_PROFILE_FIELD_MAP.get(json_name)
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

        else:
            message = f"{DataSourceID.MORNINGSTAR} profile 'sections' is not a dictionary."
            raise MorningstarResponseError(message)

        return record

    def _parse_profile_to_dict(
        self,
        profile: dict[str, Any],
        raise_error: bool = False,
    ) -> dict[str, Any]:
        """Parse a Morningstar company profile."""

        sections = profile.get("sections")
        if not isinstance(sections, dict):
            message = f"{DataSourceID.MORNINGSTAR} profile does not contain 'sections'."
            if raise_error:
                raise MorningstarResponseError(message)

        provider_attributes: dict[str, Any] = {}

        if isinstance(sections, dict):

            for json_name, section in sections.items():
                if not isinstance(section, dict):
                    continue
                attribute = self._MORNINGSTAR_PROFILE_FIELD_MAP.get(json_name)
                if attribute is not None:
                    provider_attributes[attribute] = section.get("value")
                else:
                    ClientHelper.unknown_provider_attribute(
                        provider=DataSourceID.MORNINGSTAR,
                        attribute=json_name,
                        value=section,
                    )

        elif raise_error:
            message = f"{DataSourceID.MORNINGSTAR} profile 'sections' is not a dictionary."
            raise MorningstarResponseError(message)

        return provider_attributes


if __name__ == "__main__":

    pass
