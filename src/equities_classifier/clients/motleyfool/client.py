"""Client for Motley-Fool."""


# ruff and mypy per file settings
#

# fmt: off


from typing import Any, Self
from collections.abc import Sequence
from immutabledict import immutabledict

import json
import re
from urllib.parse import urljoin
import httpx

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
    """Motley Fool returned an invalid response."""


class MotleyFoolClient:
    """Motley-Fool HTTP client."""

    _BASE_URL = "https://www.fool.com"

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
    ) -> None:

        self._client = httpx.Client(
            base_url=self._BASE_URL,
            timeout=timeout,
            follow_redirects=True,
        )

        # determine action code for next.js
        # self._next_action = _get_next"7f7d5f149d49636ec2e379afcb059e7e5cc4f99c0e"
        self._next_action = self._get_next_action()

    def _get_next_action(self) -> str |None:

        _NEXT_ACTION_RE = re.compile(r'\("([0-9a-f]+)",\s*x\.callServer,\s*void 0,\s*x\.findSourceMapURL,\s*"searchInstruments"\)')

        self._next_action = None
        next_action = None

        response = self._client.get("https://www.fool.com/")
        response.raise_for_status()

        document = html.fromstring(response.content)

        for src in document.xpath("//script[@src]/@src"):
            if ".js" not in src:
                continue

            script_url = urljoin("https://www.fool.com/", src)
            script = self._client.get(script_url)
            script.raise_for_status()

            if "searchInstruments" not in script.text:
                continue

            match = _NEXT_ACTION_RE.search(script.text)
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
        self._client.close()

    # public API

    def read_provider_profile_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = True,
    ) -> list[MotleyFoolRecord]:

        records: list[MotleyFoolRecord] = []

        for source_identifier in source_identifiers:

            if source_identifier.type != SecurityIdentifierType.TICKER:
                ClientHelper.invalid_security_type(
                    DataSourceID.MOTLEYFOOL,
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
            search_result = self._select_search_result(
                source_identifier,
                search_results,
                raise_error,
            )
            html = self._execute_company_request(search_result)
            record = self._parse_record(
                search_result,
                html,
                raise_error,
            )

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
    ) -> str:

        try:
            response = self._client.request(
                method,
                url,
                headers=headers,
                json=json_param,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ClientConnectionError(str(exc)) from exc

        return response.text

    def _execute_search_request(
        self,
        identifier: SecurityIdentifier,
    ) -> str:

        headers = {
            "accept": "text/x-component",
            "content-type": "text/plain;charset=UTF-8",
            "next-action": self._next_action,
            "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22(site)%22%2C%7B%22children%22%3A%5B%22(chrome)%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D%7D%2Cnull%2Cnull%5D",
        }

        return self._execute_request(
            method="POST",
            url="/",
            headers=headers,
            json_param=[identifier.value],
        )

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
                f"{DataSourceID.MOTLEYFOOL} response does not contain any search results.",
                MotleyFoolResponseError if raise_error else None,
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
                    )
            results.append(result)

        return results

    def _select_search_result(
        self,
        source_identifier: SecurityIdentifier,
        results: list[MotleyFoolSearchResult],
        raise_error: bool = True,
    ) -> MotleyFoolSearchResult:

        matches = [
            result
            for result in results
            if (
                result.ticker == source_identifier.value and
                result.exchange != "CRYPTO" and
                result.home_country_code != "?undefined"
            )
        ]
        if not matches:
            ClientHelper.other_error_with_message(
                DataSourceID.MOTLEYFOOL,
                f"{DataSourceID.MOTLEYFOOL} does not provide a valid search result for {source_identifier.value}.",
                MotleyFoolResponseError if raise_error else None,
            )
            return None
        if len(matches) > 1:
            ClientHelper.search_result_not_unique(
                DataSourceID.MOTLEYFOOL,
                source_identifier.type,
                source_identifier.value
            )

        return matches[0]

    def _execute_company_request(
        self,
        result: MotleyFoolSearchResult,
    ) -> str:

        return self._execute_request(
            method="GET",
            url=f"/quote/{result.exchange}/{result.ticker}",
        )


    def _parse_record(
        self,
        search_result: MotleyFoolSearchResult,
        html_text: str,
        raise_error: bool = True,
    ) -> MotleyFoolRecord:
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
                f"No {DataSourceID.MOTLEYFOOL} search result available.",
                MotleyFoolResponseError if raise_error else None,
            )
            return []

        tree = html.fromstring(html_text)
        record = MotleyFoolRecord()

        record.identifiers = [
            SecurityIdentifier(type=SecurityIdentifierType.TICKER, value=search_result.ticker,)
        ]
        record.name = search_result.name or ""
        record.ticker = search_result.ticker
        record.exchange = search_result.exchange
        record.home_country_code = search_result.home_country_code

        for attribute, xpath in self._MOTLEYFOOL_PROFILE_SECTION_FIELDS_XPATH_USED.items():
            value = text(xpath)
            if hasattr(record, attribute):
                setattr(record, attribute, value)
            else:
                ClientHelper.missing_record_attribute(
                    DataSourceID.MOTLEYFOOL,
                    attribute,
                    value,
                )

        return record


if __name__ == "__main__":

    pass
