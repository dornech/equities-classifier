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
# mypy: disable-error-code = "arg-type, no-any-return"

# fmt: off


from typing import Any, Self

from collections.abc import Sequence
from immutabledict import immutabledict

import httpx

from equities_classifier.enums import DataSourceID, SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.openfigi.models import OpenFIGIRecord
from equities_classifier.clients.clienthelper import ClientHelper
from equities_classifier.clients.ratelimiter import (
    RateLimits,
    RateLimiter
)
from equities_classifier.exceptions import (
    ClientAuthenticationError,
    ClientConnectionError,
    ClientRateLimitError,
    ClientResponseError
)


class OpenFIGIResponseError(ClientResponseError):
    """OpenFIGI returned an error response."""


class OpenFIGIClient:
    """Client for the OpenFIGI mapping REST API."""

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
        SecurityIdentifierType.WKN: "WKN"
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
        "stateCode": "state_code"
    })

    _ANONYMOUS_LIMITS = RateLimits(
        max_batch_size=10,
        requests_per_minute=25
    )

    _AUTHENTICATED_LIMITS = RateLimits(
        max_batch_size=100,
        requests_per_minute=250
    )

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        """init the HTTP client."""

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
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    # public API

    def read_provider_base_data(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
        raise_error: bool = True
    ) -> list[OpenFIGIRecord]:
        """Read base date for one or more identifiers from OpenFIGI."""

        records: list[OpenFIGIRecord] = []

        batches = self._create_batches(source_identifiers)
        for batch in batches:

            response_data = self._execute_request(batch)
            for source_identifier, item in zip(batch, response_data, strict=True):
                records.extend(
                    self._parse_records(
                        item=item,
                        source_identifier=source_identifier,
                        raise_error=raise_error
                    )
                )

        return records

    # internal routines

    def _create_batches(
        self,
        identifiers: Sequence[SecurityIdentifier]
    ) -> list[list[SecurityIdentifier]]:
        """Split identifiers into batches."""

        temp_identifiers = [
            identifier for identifier in identifiers if identifier.type not in self._OPENFIGI_IDENTIFIER_TYPE_MAP
        ]
        for identifier in temp_identifiers:
            ClientHelper.invalid_security_type(DataSourceID.OPENFIGI, identifier)

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
                "idValue": identifier.value,
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
            ClientHelper.other_error_with_message(
                DataSourceID.OPENFIGI,
                "Elements in batch and response must match.",
                OpenFIGIResponseError
            )

        return response_data

    def _parse_records(
        self,
        item: dict[str, Any],
        source_identifier: SecurityIdentifier,
        raise_error: bool = False
    ) -> list[OpenFIGIRecord]:
        """Parse a single OpenFIGI mapping response."""

        if "error" in item:
            openFIGI_msg = item["error"]
            ClientHelper.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"OpenFIGI returned an error: {openFIGI_msg}",
                OpenFIGIResponseError if raise_error else None,
            )

        if "data" not in item:
            ClientHelper.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"{DataSourceID.OPENFIGI} response does not contain 'data'.",
                OpenFIGIResponseError if raise_error else None,
            )
        data = item.get("data")
        if not isinstance(data, list):
            ClientHelper.other_error_with_message(
                DataSourceID.OPENFIGI,
                 f"{DataSourceID.OPENFIGI} response 'results' is not a list (of dictionaries).",
                 OpenFIGIResponseError if raise_error else None,
            )
        if len(data) == 0:
            ClientHelper.other_error_with_message(
                DataSourceID.OPENFIGI,
                f"{DataSourceID.OPENFIGI} returned no mapping result data.",
                OpenFIGIResponseError if raise_error else None,
            )
        if not data:
            return []

        records: list[OpenFIGIRecord] = []

        for record_data in data:

            # find existing record with share_class_figi otherwise new record
            record = next(
                (record for record in records if record.share_class_figi == record_data.get("shareClassFIGI")),
                OpenFIGIRecord()
            )
            newrecord = record.share_class_figi is None

            if newrecord:

                # Copy provider fields
                for json_name, value in record_data.items():
                    attribute = self._OPENFIGI_RECORDMAP.get(json_name)
                    if attribute is not None:
                        # Preserve positional correspondence between all listing-specific attributes.
                        if hasattr(record, attribute):
                            if isinstance(getattr(record, attribute), list):
                                getattr(record, attribute).append(value)
                            else:
                                setattr(record, attribute, value)
                        else:
                            ClientHelper.missing_record_attribute(
                                DataSourceID.OPENFIGI,
                                json_name,
                                value,
                                "_OPENFIGI_RECORDMAP",
                            )
                    else:
                        ClientHelper.unknown_provider_attribute(
                            DataSourceID.OPENFIGI,
                            source_identifier,
                            json_name,
                            value,
                            "_OPENFIGI_RECORDMAP"
                        )

                # Create canonical security identifiers (including source identifier)
                identifiers: list[SecurityIdentifier] = [source_identifier]
                for identifier_fieldname, identifier_type in self._OPENFIGI_IDENTIFIER_TYPES.items():
                    value = record_data.get(identifier_fieldname)
                    if value and identifier_type != source_identifier.type:
                        identifiers.append(
                            SecurityIdentifier(
                                type=identifier_type,
                                value=value,
                            )
                        )
                record.identifiers = identifiers

                records.append(record)

            else:

                # only add new values for existing list fields for entry with same shareclassFIGI
                for json_name, value in record_data.items():
                    attribute = self._OPENFIGI_RECORDMAP.get(json_name)
                    if attribute is not None and hasattr(record, attribute):
                        if isinstance(getattr(record, attribute), list):
                            getattr(record, attribute).append(value)

        return records


if __name__ == "__main__":

    pass
