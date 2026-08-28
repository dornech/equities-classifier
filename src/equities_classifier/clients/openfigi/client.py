"""HTTP client for the OpenFIGI REST API."""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E303
# naming conventions
# ruff: noqa: N806
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: PLR1702, RUF050, RUF105, SIM102
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, assignment, misc, no-any-return, union-attr"

# fmt: off


from typing import Any, Self

from collections.abc import Sequence
from immutabledict import immutabledict

import httpx

from equities_classifier.enums import DataSourceID, SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier, SecurityIdentifierList
from equities_classifier.exceptions import (
    ClientAuthenticationError, ClientConnectionError, ClientRateLimitError, ClientResponseError
)
from equities_classifier.clients.clienthelper import (
    ClientHelperErrorHandler,
    bloomberg_exchange_mapping, get_primary_ticker, get_us_ticker,
)
from equities_classifier.clients.ratelimiter import RateLimits, RateLimiter
from equities_classifier.clients.openfigi.models import OpenFIGIRecord


class OpenFIGIResponseError(ClientResponseError):
    """OpenFIGI returned an error response."""


class OpenFIGIClient:
    """Client for the OpenFIGI mapping REST API."""

    # constants and related evaluation routines

    _BASE_URL = "https://api.openfigi.com/v3/mapping"

    _OPENFIGI_IDENTIFIER_TYPES: immutabledict[str, SecurityIdentifierType] = immutabledict({
        "share_class_figi": SecurityIdentifierType.SHARE_CLASS_FIGI,
        "isin": SecurityIdentifierType.ISIN,
        "ticker": SecurityIdentifierType.TICKER,
    })

    _OPENFIGI_IDENTIFIER_TYPE_MAP: immutabledict[SecurityIdentifierType, str] = immutabledict({
        SecurityIdentifierType.CINS: "ID_CINS",
        SecurityIdentifierType.CUSIP: "ID_CUSIP",
        SecurityIdentifierType.SHARE_CLASS_FIGI: "ID_BB_GLOBAL_SHARE_CLASS_LEVEL",
        SecurityIdentifierType.ISIN: "ID_ISIN",
        SecurityIdentifierType.SEDOL: "ID_SEDOL",
        SecurityIdentifierType.TICKER: "TICKER",
        SecurityIdentifierType.WKN: "ID_WERTPAPIER",
    })

    @classmethod
    def _to_openfigi_identifier_type(cls, identifier_type: SecurityIdentifierType) -> str:
        return cls._OPENFIGI_IDENTIFIER_TYPE_MAP[identifier_type]

    _OPENFIGI_RECORDMAP: immutabledict[str, str] = immutabledict({
        "name": "name",
        "ticker": "ticker",
        "figi": "figi",
        "compositeFIGI": "composite_figi",
        "shareClassFIGI": "share_class_figi",
        "securityDescription": "security_description",
        "securityType": "security_type",
        "securityType2": "security_type2",
        "marketSector": "market_sector",
        "exchCode": "exch_code",
        "micCode": "mic_code",
        "currency": "currency",
        "stateCode": "state_code",
    })

    _ANONYMOUS_LIMITS = RateLimits(
        max_batch_size=10,
        requests_per_minute=25
    )

    _AUTHENTICATED_LIMITS = RateLimits(
        max_batch_size=100,
        requests_per_minute=250
    )

    # __init__, other ContextManager dunder routines and internal routines used within

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        """init the HTTP client."""

        self._client: httpx.Client | None

        headers: dict[str, str] = {
            "Content-Type": "application/json"
        }
        self._api_key = api_key
        if api_key:
            headers["X-OPENFIGI-APIKEY"] = api_key
            self._limits = self._AUTHENTICATED_LIMITS
        else:
            self._limits = self._ANONYMOUS_LIMITS
        self._rate_limiter = RateLimiter(requests_per_minute=self._limits.requests_per_minute)
        self._client = httpx.Client(
            headers=headers,
            timeout=timeout,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self._close()

    def _close(self) -> None:
        """Close the HTTP client."""

        # check self._client before execution due to potential double-close when using pytest
        if self._client:
            self._client.close()
            self._client = None

    # public API

    def read_provider_base_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = True
    ) -> list[OpenFIGIRecord]:
        """Read base date for one or more identifiers from OpenFIGI."""

        results: list[OpenFIGIRecord] = []

        batches = self._create_batches(source_identifiers)
        for batch in batches:

            response_data = self._execute_request(batch)
            for source_identifier, item in zip(batch, response_data, strict=True):
                # parsing across batches for comprehension of data for duplicate source identifiers
                # (i.e. ticker and ISIN)
                self._parse_records(
                    item=item,
                    source_identifier=source_identifier,
                    records=results,
                    raise_error=raise_error
                )

        # repeat for tickers with share_class_figi to get US tickers

        repeat_ticker_with_share_class_figi: list[SecurityIdentifier] = list({
            result.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI)
            for result in results
            if (
                result.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI) is not None and
                not result.has_identifier(SecurityIdentifierType.ISIN) and
                result.has_identifier(SecurityIdentifierType.TICKER) and
                result.identifier(SecurityIdentifierType.TICKER).value_cleaned !=
                get_us_ticker(result.ticker_exchange, result.exch_code)
            )
        })
        if len(repeat_ticker_with_share_class_figi) == 0:
            return results

        batches = self._create_batches(repeat_ticker_with_share_class_figi)
        for batch in batches:

            response_data = self._execute_request(batch)
            for source_identifier, item in zip(batch, response_data, strict=True):
                # parsing across batches for comprehension of data for duplicate source identifiers
                # (i.e. ticker and ISIN)
                self._parse_records(
                    item=item,
                    source_identifier=source_identifier,
                    records=results,
                    raise_error=raise_error
                )

        return results

    @staticmethod
    def remove_records_without_share_class_figi_1(
        records: list[OpenFIGIRecord],
    ) -> list[OpenFIGIRecord]:
        """Remove records without share_class_FIGI if no ISIN-matching record exists."""

        count_before = len(records)

        identifiers_with_share_class_figi: set[SecurityIdentifier] = {
            SecurityIdentifier(identifier.type, str(identifier.value_cleaned))
            for record in records
            if record.share_class_figi is not None
            for identifier in record.identifiers
            if identifier.type == SecurityIdentifierType.ISIN
        }
        records = [
            record
            for record in records
            if (
                record.share_class_figi is not None
                or not any(
                    (identifier.type, identifier.value_cleaned) in identifiers_with_share_class_figi
                    for identifier in record.identifiers
                    if identifier.type == SecurityIdentifierType.ISIN
                )
            )
        ]

        count_after = len(records)

        if count_before - count_after > 0:
            ClientHelperErrorHandler.records_cleaned(
                DataSourceID.OPENFIGI,
                count_before - count_after,
                "records without shareClassFIGI and no matching to shareClassFIGI via ISIN"
            )

        return records

    @staticmethod
    def remove_records_without_share_class_figi_2(
        records: list[OpenFIGIRecord],
    ) -> list[OpenFIGIRecord]:
        """Remove records without share_class_FIGI  and not Common Stock."""

        count_before = len(records)

        records = [
            record
            for record in records
                if record.share_class_figi and
                (record.security_type == "Common Stock" or record.security_type2 == "Common Stock")
        ]

        count_after = len(records)

        if count_before - count_after > 0:
            ClientHelperErrorHandler.records_cleaned(
                DataSourceID.OPENFIGI,
                count_before - count_after,
                "records without missing shareClassFIGI and no ISIN matching (i. e. non share fiancial instruments)"
            )

        return records

    @staticmethod
    def check_and_set_primary_ticker(
        records: list[OpenFIGIRecord],
        set_ticker: bool = True,
        raise_error: bool = False,
    ) -> None:
        """Check and optionally set the primary ticker for OpenFIGI records."""

        for record in records:

            if record.has_identifier(SecurityIdentifierType.ISIN):

                isin = record.identifier(SecurityIdentifierType.ISIN).value
                ticker_new1 = get_primary_ticker(
                    DataSourceID.OPENFIGI,
                    isin,
                    record.name,
                    record.ticker,
                    record.ticker_mic,
                    record.mic_code,
                    OpenFIGIResponseError,
                )
                mics_from_exchange = [
                    next(
                        (
                            entry["operating_mic"]
                            for entry in bloomberg_exchange_mapping
                            if entry["bloomberg_exchange"] == exchange
                        ),
                        None
                    )
                    for exchange in record.exch_code
                ]
                ticker_new2 = get_primary_ticker(
                    DataSourceID.OPENFIGI,
                    isin,
                    record.name,
                    record.ticker,
                    record.ticker_exchange,
                    mics_from_exchange,
                    OpenFIGIResponseError,
                )
                if ticker_new1 and ticker_new2 and ticker_new1 != ticker_new2:
                    ClientHelperErrorHandler.inconsistent_provider_data(
                        DataSourceID.OPENFIGI,
                        record.name,
                        "primary ticker from Bloomberg exchanges and mic-codes differ",
                        OpenFIGIResponseError,
                    )
                if ticker_new1 and set_ticker:
                    record.ticker = ticker_new1
                    record.identifiers.replace(SecurityIdentifier(SecurityIdentifierType.TICKER, ticker_new1))
                elif ticker_new2 and set_ticker:
                    record.ticker = ticker_new2
                    record.identifiers.replace(SecurityIdentifier(SecurityIdentifierType.TICKER, ticker_new2))

            elif record.has_identifier(SecurityIdentifierType.TICKER):

                if record.security_type == record.security_type2 == "Common Stock":
                    record.ticker = record.identifier(SecurityIdentifierType.TICKER).value

    @staticmethod
    def check_and_set_us_ticker(
        records: list[OpenFIGIRecord],
        set_ticker: bool = True,
        raise_error: bool = False,
    ) -> None:
        """Check and optionally set the primary ticker for OpenFIGI records."""

        for record in records:
            ticker_us = get_us_ticker(record.ticker_exchange, record.exch_code)
            if ticker_us:
                record.identifiers.append(SecurityIdentifier(SecurityIdentifierType.TICKER_US, ticker_us))

    # internal routines

    def _create_batches(self, identifiers: Sequence[SecurityIdentifier]) -> list[list[SecurityIdentifier]]:
        """Split identifiers into batches."""

        temp_identifiers = [
            identifier for identifier in identifiers if identifier.type not in self._OPENFIGI_IDENTIFIER_TYPE_MAP
        ]
        for identifier in temp_identifiers:
            ClientHelperErrorHandler.invalid_security_type(DataSourceID.OPENFIGI, identifier)

        temp_identifiers = [
            identifier for identifier in identifiers if identifier.type in self._OPENFIGI_IDENTIFIER_TYPE_MAP
        ]
        batch_size = self._limits.max_batch_size
        return [
            list(temp_identifiers[i: i + batch_size])
            for i in range(0, len(temp_identifiers), batch_size)
        ]

    def _execute_request(
        self,
        batch: Sequence[SecurityIdentifier],
    ) -> list[dict[str, Any]]:
        """Execute single OpenFIGI mapping request."""

        payload = [
            {
                "idType": self._to_openfigi_identifier_type(identifier.type),
                "idValue": identifier.value_cleaned.replace(" ", ""),
            }
            for identifier in batch
        ]
        self._rate_limiter.wait()

        try:
            response = self._client.post(self._BASE_URL, json=payload)
        except httpx.ConnectError as exc:
            raise ClientConnectionError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            raise ClientConnectionError(str(exc)) from exc
        match response.status_code:
            case 401 | 403:
                raise ClientAuthenticationError(response.text)
            case 429:
                raise ClientRateLimitError(response.text)
            case _:
                response.raise_for_status()

        response_data = response.json()
        if len(response_data) != len(batch):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.OPENFIGI,
                "Elements in batch and response must match.",
                OpenFIGIResponseError
            )

        return response_data

    def _parse_records(
        self,
        item: dict[str, Any],
        source_identifier: SecurityIdentifier,
        records: list[OpenFIGIRecord],
        raise_error: bool = False
    ) -> None:

        if "error" in item:
            openFIGI_msg = item["error"]
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"OpenFIGI returned an error for {source_identifier.type} '{source_identifier.value}: {openFIGI_msg}",
                OpenFIGIResponseError if raise_error else None,
            )
            return
        elif "warning" in item:
            openFIGI_msg = item["warning"]
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"OpenFIGI returned a warning for {source_identifier.type} '{source_identifier.value}': {openFIGI_msg}",
                OpenFIGIResponseError if raise_error else None,
            )
            return
        elif "data" not in item:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"{DataSourceID.OPENFIGI} response does not contain 'data' for "
                f"{source_identifier.type} '{source_identifier.value}'.",
                OpenFIGIResponseError if raise_error else None,
            )
            return

        data = item.get("data")
        if not isinstance(data, list):
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"{DataSourceID.OPENFIGI} response 'results' is not a list (of dictionaries).",
                OpenFIGIResponseError if raise_error else None,
            )
        if len(data) == 0:
            ClientHelperErrorHandler.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"{DataSourceID.OPENFIGI} returned no mapping result data.",
                OpenFIGIResponseError if raise_error else None,
            )
        if not data:
            # return []
            return None

        for record_data in data:

            # find existing record with share_class_figi otherwise new record
            # NOTE: share_class_figi might be empty due to non-share security type or data error
            record = None
            if record_data.get("shareClassFIGI"):
                record = next(
                    (existing_record for existing_record in records
                        if existing_record.share_class_figi == record_data.get("shareClassFIGI")
                    ),
                    None
                )
            else:
                record = next(
                    (existing_record for existing_record in records if (
                        existing_record.share_class_figi is None and
                        existing_record.market_sector == record_data.get("marketSector") and
                        existing_record.security_type2 == record_data.get("securityType2")
                    )),
                    None
                )

            if not record:

                record = OpenFIGIRecord()

                # Copy provider fields
                for json_name, value in record_data.items():
                    if json_name != "ticker":
                        attribute = self._OPENFIGI_RECORDMAP.get(json_name)
                        if attribute is not None:
                            # Preserve positional correspondence between all listing-specific attributes.
                            if hasattr(record, attribute):
                                if isinstance(getattr(record, attribute), list):
                                    getattr(record, attribute).append(value)
                                else:
                                    setattr(record, attribute, value)
                            else:
                                ClientHelperErrorHandler.missing_record_attribute(
                                    DataSourceID.OPENFIGI,
                                    json_name,
                                    value,
                                    "_OPENFIGI_RECORDMAP",
                                )
                        else:
                            ClientHelperErrorHandler.unknown_provider_attribute(
                                DataSourceID.OPENFIGI,
                                source_identifier,
                                json_name,
                                value,
                                "_OPENFIGI_RECORDMAP"
                            )
                    elif "exchCode" in record_data:
                        record.ticker_exchange.append(value)
                    elif "micCode" in record_data:
                        record.ticker_exchange.append(value)

                # Create canonical security identifiers (including source identifier)
                # identifiers: SecurityIdentifierList = [source_identifier]
                identifiers = SecurityIdentifierList([
                    SecurityIdentifier(type=source_identifier.type, value=source_identifier.value_cleaned)
                ])
                for identifier_field, identifier_type in self._OPENFIGI_IDENTIFIER_TYPES.items():
                    value = getattr(record, identifier_field) if hasattr(record, identifier_field) else None
                    if value and identifier_type not in {source_identifier.type, SecurityIdentifierType.TICKER}:
                        identifiers.append(SecurityIdentifier(type=identifier_type, value=value))
                record.identifiers = identifiers

                records.append(record)

            else:

                # only add new values for existing list fields for entry with same shareclassFIGI
                for json_name, value in record_data.items():
                    if json_name != "ticker":
                        attribute = self._OPENFIGI_RECORDMAP.get(json_name)
                        if attribute is not None and hasattr(record, attribute):
                            if isinstance(getattr(record, attribute), list):
                                getattr(record, attribute).append(value)
                    elif "exchCode" in record_data:
                        record.ticker_exchange.append(value)
                    elif "micCode" in record_data:
                        record.ticker_exchange.append(value)


if __name__ == "__main__":

    pass
