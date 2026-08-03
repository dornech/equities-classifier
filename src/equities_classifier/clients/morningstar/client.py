"""Client for Morningstar."""


from typing import Any, Self

from collections.abc import Sequence
from dataclasses import fields

# from playwright.sync_api import sync_playwright, Browser, BrowserContext, APIRequestContext
# from undetected_playwright import Tarnished
# from playwright_stealth import Stealth
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
        ("meta", "companyID"): "company_id",
        ("meta", "securityID"): "security_id",
        ("meta", "performanceID"): "performance_id",
        ("meta", "universe"): "universe",

        ("fields", "name", "value"): "name",
        ("fields", "shortName", "value"): "short_name",
        ("fields", "ticker", "value"): "ticker",
        ("fields", "isin", "value"): "isin",

        ("fields", "exchange", "value"): "exchange",
        ("fields", "exchange", "displayAs"): "exchange_name",

        ("fields", "exchangeCountry", "value"): "exchange_country",
        ("fields", "exchangeCountry", "displayAs"): "exchange_country_name",
    }

    _MORNINGSTAR_PROFILE_FIELD_MAP: dict[str, str] = {
        "businessDescription": "business_description",
        "sector": "sector",
        "industry": "industry",
    }

    @staticmethod
    def _get_nested_value(data: dict[str, Any], path: tuple[str, ...],) -> Any:
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
    ) -> None:
        """Initialize Morningstar client."""

        # approach with playwright (including undetected playwright libraries)
        # self._playwright = sync_playwright().start()
        # # self._playwright = Stealth().use_sync(sync_playwright()).start()
        # # self._browser: Browser = self._playwright.chromium.launch(headless=True, channel="msedge")
        # self._browser: Browser = self._playwright.chromium.launch(headless=False, channel="msedge")
        # self._context: BrowserContext = self._browser.new_context(
        #     locale="en-GB",
        #     user_agent=(
        #         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        #         "AppleWebKit/537.36 (KHTML, like Gecko) "
        #         "Chrome/138.0.0.0 Safari/537.36"
        #     ),
        # )
        # # Tarnished.apply_stealth(self._context)
        # self._request: APIRequestContext = self._context.request
        #
        # # load morningstar page to intialize
        # self._page = self._context.new_page()
        # self._page.goto("https://global.morningstar.com/en-eu")

        # approach with Selenium
        self._client = utils_seleniumxp.init_webdriver(
            stealthmode=False,
            optimizedscraping=False,
            URL="https://global.morningstar.com/en-eu",
            browser = "chrome",
            alt_cls_webdriverwrapper = uc.Chrome,
            alt_cls_options = uc.ChromeOptions,
        )

        self._timeout = timeout

        self._access_token: str | None = None
        self._access_token_expires: datetime.date | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Release browser resources."""

        # approach with playwright
        # self._context.close()
        # self._browser.close()
        # self._playwright.stop()

        # approach with Selenium
        self._client.close()

    def read_provider_base_data(
        self,
        identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = True
    ) -> list[MorningstarRecord]:
        """Read base date for one or more identifiers from Morningstar."""

        records: list[MorningstarRecord] = []

        for source_identifier in identifiers:

            response_data = self._execute_search_request(identifier)
            search_results = self._parse_search_results(source_identifier, response_data, raise_error)
            search_results = [
                result for result in search_results
                if (
                       identifier.type == SecurityIdentifierType.ISIN
                       and result.isin == identifier.value
                )
                or (
                   identifier.type == SecurityIdentifierType.TICKER
                   and result.ticker == identifier.value
               )
            ]

            if search_results is not None:
                record = self._parse_record(source_identifier,  search_results,  raise_error)
                records.append(record)

        return records

    def read_provider_profile_data(
        self,
        records: Sequence[MorningstarRecord],
        raise_error: bool = True
    ) -> list[MorningstarRecord]:

        for record in records:

            profile_data = self._execute_profile_request(share_class_id = record.security_id[0])
            record = self._parse_profile_to_record(profile_data, record,raise_error)


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

        # approach with playwright
        # response = self._request.fetch(
        #     url,
        #     method=method,
        #     params=params,
        #     data=json_param,
        #     timeout=self._timeout * 1000,
        # )
        # match response.status:
        #     case 401 | 403:
        #         raise ClientAuthenticationError(response.text())
        #     case 429:
        #         raise ClientRateLimitError(response.text())
        #     case _ if response.status >= 400:
        #         raise ClientResponseError(response.text())

        # approach with selenium-request
        # try:
        #     response = self._client.request(method, url, params=params)
        # except utils_seleniumxp.TimeoutException as exc:
        #     raise ClientConnectionError(str(exc)) from exc
        # match response.status_code:
        #     case 401 | 403:
        #         raise ClientAuthenticationError(response.text)
        #     case _:
        #         response.raise_for_status()

        # response_data = response.json()

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

        count = response_data["count"] - len(response_data)
        if raise_error and count == 0:
            message = f"Morningstar returned no search data."
            raise MorningstarResponseError(message)

        search_results: list[MorningstarSearchResult] = []

        for item in response_data["results"]:

            result = MorningstarSearchResult(source_identifier=source_identifier)
            for path, attribute in self._MORNINGSTAR_SEARCH_RESULT_MAP.items():
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
            message = f"Morningstar returned inconsistent data or error in evaluation."
            raise MorningstarResponseError(message)

        return search_results

    def _parse_record(
        self,
        source_identifier: SecurityIdentifier,
        search_results: list[MorningstarSearchResult],
        raise_error: bool = False
    ) -> MorningstarRecord:

        if raise_error and not search_results:
            msg = "No Morningstar search results available."
            raise MorningstarResponseError(msg)

        record = MorningstarRecord()

        # Copy scalar fields from first search result.
        first = search_results[0]
        record.name = first.name or ""
        record.ticker = first.ticker
        record.company_id = first.company_id
        record.universe = first.universe

        for search_result in search_results:

            # copy other provider fields
            for field in fields(search_result):
                if hasattr(record, field.name):
                    target = getattr(record, field.name)
                    if isinstance(target, list):
                        # Preserve positional correspondence between all listing-specific attributes.
                        value = getattr(search_result, field.name, None)
                        target .append(value)
                    else:
                        if getattr(search_result, field.name) != getattr(record, field.name):
                            msg = (
                                f"Inconsistency between Morningstar search results and modelling assumption: "
                                f"field '{field.name}' differs between listings."
                            )
                            raise MorningstarResponseError(msg)

                else:
                    # provider attributes not yet in record definition -> potential logging endpoint
                    pass

        # Create canonical security identifiers (including source identifier).
        identifiers: list[SecurityIdentifier] = [source_identifier]
        for attribute, identifier_type in self._MORNINGSTAR_IDENTIFIER_MAP.items():
            value = getattr(record, attribute)
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
            msg = "Morningstar response does not contain an accessToken."
            raise MorningstarResponseError(msg)

    def _execute_profile_request(
        self,
        share_class_id: str,
    ) -> dict[str, Any]:
        """Request the Morningstar company profile."""

        params = {
            "shareClassId": share_class_id,
            "access_token": self._get_access_token(),
        }
        response_data = self._execute_request(method="GET", url=self._PROFILE_URL, params=params)

        if not isinstance(response_data, dict):
            msg = "Unexpected Morningstar company profile response."
            raise MorningstarResponseError(msg)

        return response_data

    def _parse_profile_to_record(
        self,
        profile: dict[str, Any],
        record: MorningstarRecord,
        raise_error: bool = False
    ) -> MorningstarRecord:
        """Enrich a MorningstarRecord with company profile information."""

        sections = profile.get("sections")
        if raise_error and not isinstance(sections, dict):
            msg = "Morningstar profile does not contain 'sections'."
            raise MorningstarResponseError(msg)

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
            msg = "Morningstar profile 'sections' is not a dictionary."
            raise MorningstarResponseError(msg)

        return record

    def _parse_profile_to_dict(
        self,
        profile: dict[str, Any],
        raise_error: bool = False,
    ) -> dict[str, Any]:
        """Parse a Morningstar company profile."""

        sections = profile.get("sections")
        if raise_error and not isinstance(sections, dict):
            msg = "Morningstar profile does not contain 'sections'."
            raise MorningstarResponseError(msg)

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
            msg = "Morningstar profile 'sections' is not a dictionary."
            raise MorningstarResponseError(msg)

        return provider_attributes


if __name__ == "__main__":

    client = MorningstarClient()

    identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "US0378331005",
    )

    with client:

        records = client.read_provider_base_data([identifier])

    print(records)
