"""HTTP client for the OpenFIGI REST API."""


from typing import Any

from collections import defaultdict
from collections.abc import Sequence

import httpx

from equities_classifier.models import (
    SecurityIdentifier,
    SecurityIdentifierType
)
from equities_classifier.clients.openfigi.models import OpenFIGIRecord
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

    BASE_URL = "https://api.openfigi.com/v3/mapping"

    _IDENTIFIER_TYPE_MAP: dict[SecurityIdentifierType, str] = {
        SecurityIdentifierType.CINS: "ID_CINS",
        SecurityIdentifierType.CUSIP: "ID_CUSIP",
        SecurityIdentifierType.SHARE_CLASS_FIGI: "ID_BB_GLOBAL_SHARE_CLASS_LEVEL",
        SecurityIdentifierType.ISIN: "ID_ISIN",
        SecurityIdentifierType.SEDOL: "ID_SEDOL",
        SecurityIdentifierType.TICKER: "TICKER",
        SecurityIdentifierType.WKN: "WKN"
    }

    @classmethod
    def _to_openfigi_identifier_type(cls, identifier_type: SecurityIdentifierType) -> str:
        return cls._IDENTIFIER_TYPE_MAP[identifier_type]

    _ANONYMOUS_LIMITS = RateLimits(
        max_batch_size=10,
        requests_per_minute=25
    )

    _AUTHENTICATED_LIMITS = RateLimits(
        max_batch_size=100,
        requests_per_minute=250
    )

    _OPENFIGI_IDENTIFIER_MAP: dict[str, SecurityIdentifierType] = {
        "cusip": SecurityIdentifierType.CUSIP,
        "cins": SecurityIdentifierType.CINS,
        "isin": SecurityIdentifierType.ISIN,
        "shareClassFIGI": SecurityIdentifierType.SHARE_CLASS_FIGI,
        "sedol": SecurityIdentifierType.SEDOL,
        "ticker": SecurityIdentifierType.TICKER
    }

    _OPENFIGI_RECORDMAP: dict[str, str] = {
        "name": "company_name",
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
    }

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        """init the HTTP client."""

        headers: dict[str, str] = {}
        headers["Content-Type"] = "application/json"
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

    def __enter__(self) -> "OpenFIGIClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def map(
        self,
        identifiers: Sequence[SecurityIdentifier],
        unique_share_class_figi_only: bool = True,
        raise_error: bool = True
    ) -> list[OpenFIGIRecord]:
        """Resolve one or more identifiers via OpenFIGI."""

        records: list[OpenFIGIRecord] = []

        request_plan = self._create_request_plan(identifiers)
        for identifier_type, identifier_list in request_plan.items():

            batches = self._create_batches(identifier_list)
            for batch in batches:

                response_data=self._execute_request(batch)
                for source_identifier, item in zip(batch, response_data, strict=True):
                    records.extend(
                        self._parse_record(
                            item=item,
                            source_identifier=source_identifier,
                            unique_share_class_figi_only=unique_share_class_figi_only,
                            raise_error=raise_error
                        )
                    )

        return records

    def _create_request_plan(
        self,
        identifiers: Sequence[SecurityIdentifier],
    ) -> dict[SecurityIdentifierType, list[SecurityIdentifier]]:
        """Group identifiers by source identifier type."""

        request_plan: defaultdict[
            SecurityIdentifierType,
            list[SecurityIdentifier],
        ] = defaultdict(list)
        for identifier in identifiers:
            request_plan[identifier.type].append(identifier)

        return dict(request_plan)

    def _create_batches(
        self,
        identifiers: Sequence[SecurityIdentifier]
    ) -> list[list[SecurityIdentifier]]:
        """Split identifiers into batches."""

        batch_size = self._limits.max_batch_size
        return [
            list(identifiers[i: i + batch_size])
            for i in range(0, len(identifiers), batch_size)
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
            response = self._client.post(self.BASE_URL, json=payload)
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
            msg = "Elements in batch and response must match."
            raise ClientResponseError(msg)

        return response_data

    def _parse_record(
        self,
        item: dict[str, Any],
        source_identifier: SecurityIdentifier,
        unique_share_class_figi_only: bool = True,
        raise_error: bool = False
    ) -> list[OpenFIGIRecord]:
        """Parse a single OpenFIGI mapping response."""

        if raise_error and "error" in item:
            openFIGI_msg = item["error"]
            message = f"OpenFIGI returned an error: {openFIGI_msg}"
            raise OpenFIGIResponseError(message)

        data = item.get("data")
        if raise_error and data is None:
            message = "OpenFIGI response does not contain a 'data' element."
            raise OpenFIGIResponseError(message)
        if raise_error and len(data) == 0:
            message = "OpenFIGI returned no mapping result."
            raise OpenFIGIResponseError(message)
        if not data:
            return []

        seen_share_class_figis: set[str] = set()
        records: list[OpenFIGIRecord] = []

        for record_data in data:

            record = OpenFIGIRecord()

            # Copy provider fields.
            for json_name, value in record_data.items():
                attribute = self._OPENFIGI_RECORDMAP.get(json_name)
                if attribute is not None and hasattr(record, attribute):
                    setattr(record, attribute, value)

            # Remove duplicate share classes if requested.
            if unique_share_class_figi_only:
                share_class_figi = record.share_class_figi
                if share_class_figi is not None and share_class_figi in seen_share_class_figis:
                    continue
                if share_class_figi is not None:
                    seen_share_class_figis.add(share_class_figi)

            # Create canonical security identifiers (including source identifier).
            identifiers: list[SecurityIdentifier] = [source_identifier]
            for json_name, identifier_type in self._OPENFIGI_IDENTIFIER_MAP.items():
                value = record_data.get(json_name)
                if value and identifier_type != source_identifier.type:
                    identifiers.append(
                        SecurityIdentifier(
                            type=identifier_type,
                            value=value,
                        )
                    )
            record.identifiers = identifiers

            records.append(record)

        return records


if __name__ == "__main__":
    pass
