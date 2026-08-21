"""Client for Motley-Fool."""


# ruff and mypy per file settings
#
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: E501, RUF050, RUF105, S110
# disable mypy errors
# mypy: disable-error-code = "arg-type, index, operator, type-var, union-attr"

# fmt: off


from typing import Any, Self
from collections.abc import Sequence
from enum import StrEnum
from immutabledict import immutabledict

import time
import json
import re
from urllib.parse import urljoin
import httpx
from equities_classifier.clients.httpx_logger import log_request, log_response
import undetected as uc
from waitless import stabilize, get_diagnostics, StabilizationConfig, StabilizationTimeout
from waitless.diagnostics import print_report
from selenium.webdriver.common.by import By

from iso3166 import countries
from lxml import html

from equities_classifier.clients.clienthelper import ClientHelper
from equities_classifier.clients.motleyfool.models import (
    MotleyFoolSearchResult,
    MotleyFoolRecord,
)
from equities_classifier.enums import (
    DataSourceID,
    SecurityIdentifierType,
)
from equities_classifier.models import SecurityIdentifier
from equities_classifier.exceptions import (
    ClientConnectionError,
    ClientResponseError,
)


class MotleyFoolResponseError(ClientResponseError):
    """Motley-Fool returned an invalid response."""


class MotleyFoolMode(StrEnum):
    """Supported client modes."""

    HTTPX = "httpx"
    SELENIUM = "SELENIUM"


class MotleyFoolClient:
    """Motley-Fool HTTP client with httpx or Selenium mode as currenlty used fallback."""

    _BASE_URL = "https://www.fool.com"

    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )

    _MOTLEYFOOL_COUNTRY_FROM_EXCHANGE = immutabledict({
        "CPSE": "DK",
        "ETR": "DE",
        "FRA": "DE",
        "LSE": "GB",
        "NASDAQ": "US",
        "NYSE": "US",
        "TSX": "CA",
        "TYO": "JP",
        "XSWX": "CH",
    })

    _MOTLEYFOOL_SEARCH_RESULT_MAP: immutabledict[str, str] = immutabledict({
        "Symbol": "ticker",
        "Name": "name",
        "Exchange": "exchange",
        "HomeCountryCode": "home_country_code",
    })

    _MOTLEYFOOL_PROFILE_SECTION_FIELDS_XPATH_USED: immutabledict[str, str] = immutabledict({
        "sector": "//section/descendant::div/p[.='Sector']/following-sibling::a",
        "industry": "//section/descendant::div/p[.='Industry']/following-sibling::p",
    })

    def __init__(
        self,
        timeout: float = 30.0,
        mode: MotleyFoolMode = MotleyFoolMode.HTTPX,
        requestlog: bool = False
    ) -> None:
        """Initialize Motley-Fool client."""

        self._client: httpx.Client | uc.Chrome

        self._mode = mode
        if self._mode == MotleyFoolMode.HTTPX:
            self._client = httpx.Client(
                base_url=self._BASE_URL,
                timeout=timeout,
                follow_redirects=True,
                event_hooks={"request": [log_request], "response": [log_response], } if requestlog else None
            )
            # determine action code for next.js
            self._next_action = self._get_next_action()
        elif self._mode == MotleyFoolMode.SELENIUM:
            options = uc.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
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
            self._client.get(self._BASE_URL)
            time.sleep(5)  # additional wait for cookie popup (required in GitHub Action environment)
            self._client.find_element(By.XPATH, "//button[@id='onetrust-accept-btn-handler']").click()
        else:
            msg = f"MotleyFoolClient mode '{self._mode}' not valid.)"
            raise MotleyFoolResponseError(msg)

    def _get_next_action(self) -> str | None:

        next_action_regex = re.compile(
            r'\("([0-9a-f]+)",[\s\S]{1,2}\.callServer,\s*?void 0,[\s\S]{1,2}\.findSourceMapURL,.[\s\S]{0,1}searchInstruments"\)'
        )

        self._next_action = None

        response = self._client.get("https://www.fool.com/", headers={"User-Agent": self._USER_AGENT})
        response.raise_for_status()

        document = html.fromstring(response.content)

        for src in document.xpath("//script[@src]/@src"):
            if ".js" not in src:
                continue

            script_url = urljoin("https://www.fool.com/", src)
            script = self._client.get(script_url, headers={"User-Agent": self._USER_AGENT})
            script.raise_for_status()

            if "searchInstruments" not in script.text:
                continue

            match = next_action_regex.search(script.text)
            if match:
                return str(match.group(1))

        ClientHelper.other_error_with_message(
            DataSourceID.MOTLEYFOOL,
            f"Next-Action for searchInstruments not found at {DataSourceID.MOTLEYFOOL}.",
            MotleyFoolResponseError,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Release client resources."""

        # check self_client before execution due to potential double-close when using pytest
        if self._client:
            self._client.close()
            self._client = None

    # public API

    def read_provider_profile_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = False,
    ) -> list[MotleyFoolRecord]:
        """Read profile data for one or more identifiers from Motley-Fool."""

        records: list[MotleyFoolRecord] = []

        for source_identifier in source_identifiers:

            if source_identifier.type != SecurityIdentifierType.TICKER:
                ClientHelper.invalid_security_type(
                    DataSourceID.MOTLEYFOOL,
                    source_identifier
                )
                continue

            if self._mode == MotleyFoolMode.HTTPX:
                # determine search result and fill search_result via requests
                response_data = self._execute_search_request(source_identifier)
                search_results = self._parse_search_results(
                    source_identifier,
                    response_data,
                    raise_error,
                )
            else:
                # determine search result and fill search_result via selenium / HTML analysis
                search_results = self._get_search_results(
                    source_identifier,
                    raise_error,
                )

            search_result = self._select_search_result(
                source_identifier,
                search_results,
                raise_error,
            )
            if search_result:

                if self._mode == MotleyFoolMode.HTTPX:
                    html = self._execute_company_request(search_result)
                else:
                    html = self._get_company_profile_html(search_result)

                record = self._parse_record(
                    search_result,
                    html,
                    raise_error,
                )
                if record:
                    records.append(record)

        return records

    # internal routines

    def _execute_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_param: Any | None = None,
    ) -> Any:

        try:
            request = self._client.build_request(
                method,
                url,
                headers=headers,
                json=json_param,
            )
            request.headers["User-Agent"] = self._USER_AGENT
            response = self._client.send(request)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ClientConnectionError(str(exc)) from exc

        return response.text

    def _execute_search_request(
        self,
        identifier: SecurityIdentifier,
    ) -> Any:

        headers = {
            "accept": "text/x-component",
            "content-type": "text/plain;charset=UTF-8",
            "next-action": self._next_action,
            "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22(site)%22%2C%7B%22children%22%3A%5B%22(chrome)%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D%7D%2Cnull%2Cnull%5D",
        }

        response = self._execute_request(
            method="POST",
            url=self._BASE_URL,
            headers=headers,
            json_param=[identifier.value_cleaned],
        )

        return response

    def _parse_search_results(
        self,
        source_identifier: SecurityIdentifier,
        response: str,
        raise_error: bool = True,
    ) -> list[MotleyFoolSearchResult]:

        match = re.search(r"1:(\[.*\])", response, re.DOTALL)
        if match is None:
            ClientHelper.other_error_with_message(
                DataSourceID.MOTLEYFOOL,
                f"{DataSourceID.MOTLEYFOOL} search result response for identifier ({source_identifier.type}, {source_identifier.value}) does not contain any search result.",
            )
            return []

        data = json.loads(match.group(1))
        results: list[MotleyFoolSearchResult] = []

        for item in data:
            result = MotleyFoolSearchResult()
            for json_name, attribute in self._MOTLEYFOOL_SEARCH_RESULT_MAP.items():
                value = item.get(json_name)
                if hasattr(result, attribute):
                    setattr(result, attribute, value)
                else:
                    ClientHelper.missing_record_attribute(
                        DataSourceID.MOTLEYFOOL,
                        attribute,
                        value,
                        "_MOTLEYFOOL_SEARCH_RESULT_MAP",
                    )
            results.append(result)

        return results

    def _get_search_results(
        self,
        source_identifier: SecurityIdentifier,
        raise_error: bool = False,
    ) -> list[MotleyFoolSearchResult]:

        self._client.find_element(
            By.XPATH, "//div[./label[@id='company-search-label']]/descendant::input"
        ).send_keys(source_identifier.value_cleaned)
        htmlitems = self._client.find_elements(
            By.XPATH, "//div[@data-radix-popper-content-wrapper]/descendant::div[@cmdk-group-items]/div[@cmdk-item]"
        )
        if len(htmlitems) == 0:
            ClientHelper.other_error_with_message(
                DataSourceID.MOTLEYFOOL,
                f"{DataSourceID.MOTLEYFOOL} website search for identifier ({source_identifier.type}, {source_identifier.value}) does not contain any search result.",
            )
            return []

        results: list[MotleyFoolSearchResult] = []

        for htmlitem in htmlitems:
            result = MotleyFoolSearchResult()
            result.ticker, result.exchange, result.name = htmlitem.get_attribute("outerText").split("\n")
            # html does not contain country -> derive from stock exchange
            result.home_country_code = self._MOTLEYFOOL_COUNTRY_FROM_EXCHANGE.get(result.exchange, None)
            results.append(result)

        return results

    @staticmethod
    def _select_search_result(
        source_identifier: SecurityIdentifier,
        search_results: list[MotleyFoolSearchResult],
        raise_error: bool = False,
    ) -> MotleyFoolSearchResult | None:

        search_results_cleaned = [
            search_result
            for search_result in search_results
            if (
                (
                    search_result.ticker == source_identifier.value_cleaned or
                    search_result.ticker.replace(" ", "") == source_identifier.value_cleaned
                  ) and
                search_result.exchange != "CRYPTO" and
                search_result.home_country_code not in {"?undefined", "$undefined"}
            )
        ]
        if not search_results_cleaned:
            ClientHelper.other_error_with_message(
                DataSourceID.MOTLEYFOOL,
                f"{DataSourceID.MOTLEYFOOL} does not provide a valid search result for identifier ({source_identifier.type}, {source_identifier.value}).",
                MotleyFoolResponseError if raise_error else None,
            )
            return None

        if len(search_results_cleaned) > 1 and source_identifier.country:
            try:
                country_alpha2 = countries.get(source_identifier.country).alpha2
                country_alpha3 = countries.get(source_identifier.country).alpha3
                matches = [
                    search_result_cleaned
                    for search_result_cleaned in search_results_cleaned
                    if search_result_cleaned.home_country_code in {country_alpha2, country_alpha3}
                ]
            except Exception:
                pass
            if len(matches) == 0:
                matches = search_results_cleaned
        else:
            matches = search_results_cleaned

        if len(matches) > 1:
            ClientHelper.search_result_not_unique(
                DataSourceID.MOTLEYFOOL,
                source_identifier,
                MotleyFoolResponseError if raise_error else None,
            )

        return matches[0]

    def _execute_company_request(
        self,
        result: MotleyFoolSearchResult,
    ) -> Any:

        return self._execute_request(
            method="GET",
            url=f"/quote/{result.exchange}/{result.ticker}",
        )

    def _get_company_profile_html(
        self,
        result: MotleyFoolSearchResult,
    ) -> Any:

        self._client.get(f"{self._BASE_URL}/quote/{result.exchange}/{result.ticker}")
        return self._client.page_source

    def _parse_record(
        self,
        search_result: MotleyFoolSearchResult,
        html_text: str,
        raise_error: bool = True,
    ) -> MotleyFoolRecord | None:
        """Parse Motley-Fool company profile page."""

        def text(xpath: str) -> str | None:

            nodes = tree.xpath(xpath)
            if not nodes:
                return None
            node = nodes[0]
            return " ".join(node.itertext()).strip()

        if search_result is None:
            ClientHelper.other_error_with_message(
                DataSourceID.MOTLEYFOOL,
                f"No {DataSourceID.MOTLEYFOOL} search result available for ticker {search_result.value}).",
            )
            return None

        tree = html.fromstring(html_text)
        record = MotleyFoolRecord()

        ticker = search_result.ticker
        if search_result.home_country_code:
            ticker = ticker + "." + search_result.home_country_code
        record.identifiers = [
            SecurityIdentifier(
                type=SecurityIdentifierType.TICKER,
                value=ticker,
            )
        ]
        record.name = search_result.name or ""
        record.ticker = search_result.ticker
        record.exchange = search_result.exchange
        record.home_country_code = search_result.home_country_code

        for attribute, xpath in self._MOTLEYFOOL_PROFILE_SECTION_FIELDS_XPATH_USED.items():
            value = text(xpath)
            if not value:
                ClientHelper.missing_provider_attribute(
                    DataSourceID.MOTLEYFOOL,
                    record.identifier,
                    attribute
                )
            if hasattr(record, attribute):
                setattr(record, attribute, value)
            else:
                ClientHelper.missing_record_attribute(
                    DataSourceID.MOTLEYFOOL,
                    attribute,
                    value,
                    "_MOTLEYFOOL_PROFILE_SECTION_FIELDS_XPATH_USED",
                )

        return record


if __name__ == "__main__":

    pass
