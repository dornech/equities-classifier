"""Test openfigi client."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "union-attr"

# fmt: off


import pytest

from equities_classifier.clients.openfigi.models import OpenFIGIRecord
from equities_classifier.clients.openfigi.client import OpenFIGIClient, OpenFIGIResponseError
from equities_classifier.models import SecurityIdentifier, SecurityIdentifierType


def test_create_batches(
    client: OpenFIGIClient,
) -> None:
    """Identifiers are split into batches."""

    client._limits.max_batch_size = 10

    identifiers = [
        SecurityIdentifier(SecurityIdentifierType.ISIN, f"ID{i}")
        for i in range(25)
    ]

    batches = client._create_batches(identifiers)

    assert len(batches) == 3
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5


def test_parse_single_record(
    client: OpenFIGIClient,
) -> None:
    """Parse a single OpenFIGI response."""

    source_identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "US0378331005",
    )

    item = {
        "data": [
            {
                "name": "Apple Inc.",
                "ticker": "AAPL",
                "figi": "BBG000B9XRY4",
                "shareClassFIGI": "BBG001S5N8V8",
                "securityType": "Common Stock",
            }
        ]
    }

    records: list[OpenFIGIRecord] = []
    client._parse_records(item, source_identifier, records=records, raise_error=True)

    assert len(records) == 1

    record = records[0]

    assert record.name == "Apple Inc."
    assert record.figi == ["BBG000B9XRY4"]
    assert record.share_class_figi == "BBG001S5N8V8"
    assert record.security_type == "Common Stock"

    assert len(record.identifiers) == 1
    assert record.identifiers[0] == source_identifier


def test_parse_multiple_records(
    client: OpenFIGIClient,
) -> None:
    """Multiple exchange listings are returned."""

    source_identifier = SecurityIdentifier(
        SecurityIdentifierType.TICKER,
        "AAPL",
    )

    item = {
        "data": [
            {
                "ticker": "AAPL",
                "figi": "FIGI1",
                "shareClassFIGI": "SC1",
            },
            {
                "ticker": "AAPL",
                "figi": "FIGI2",
                "shareClassFIGI": "SC2",
            },
        ]
    }

    records: list[OpenFIGIRecord] = []
    client._parse_records(item, source_identifier, records=records)

    assert len(records) == 2


def test_parse_unique_share_class_figi(
    client: OpenFIGIClient,
) -> None:
    """Duplicate share classes are removed."""

    source_identifier = SecurityIdentifier(
        SecurityIdentifierType.TICKER,
        "AAPL",
    )

    item = {
        "data": [
            {
                "ticker": "AAPL",
                "figi": "FIGI1",
                "shareClassFIGI": "SC1",
            },
            {
                "ticker": "AAPL",
                "figi": "FIGI2",
                "shareClassFIGI": "SC1",
            },
        ]
    }

    records: list[OpenFIGIRecord] = []
    client._parse_records(item, source_identifier, records=records, raise_error=True)

    assert len(records) == 1


def test_parse_error_response(
    client: OpenFIGIClient,
) -> None:
    """Provider errors raise an exception."""

    item = {"error": "Invalid identifier"}

    source_identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "ABC",
    )

    with pytest.raises(OpenFIGIResponseError):
        records: list[OpenFIGIRecord] = []
        client._parse_records(item, source_identifier, records=records, raise_error=True)


def test_missing_data_raises(
    client: OpenFIGIClient,
) -> None:
    """Missing data element raises an exception."""

    source_identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "ABC",
    )

    with pytest.raises(OpenFIGIResponseError):
        records: list[OpenFIGIRecord] = []
        client._parse_records({}, source_identifier, records=records, raise_error=True)
        client.check_and_set_primary_ticker(records)


def test_map_apple_isin(
    client: OpenFIGIClient,
):
    """Read data from OpenFIGI."""

    identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "US0378331005",
    )

    records = client.read_provider_base_data([identifier])
    client.check_and_set_primary_ticker(records)

    assert len([record for record in records if record.share_class_figi is not None]) == 1

    record = records[0]

    assert record.name.upper().startswith("APPLE")
    assert record.ticker == "AAPL"


def test_map_apple_ticker(
    client: OpenFIGIClient,
):
    """Read data from OpenFIGI."""

    identifier = SecurityIdentifier(
        SecurityIdentifierType.TICKER,
        "AAPL",
    )

    records = client.read_provider_base_data([identifier])
    client.check_and_set_primary_ticker(records)

    assert len([
        record for record in records
        if (record.share_class_figi is not None
            and record.security_type == "Common Stock"
            and record.security_type2 != "Depositary Receipt")
    ]) == 1

    record = records[0]

    assert record.name.upper().startswith("APPLE")
    assert record.ticker == "AAPL"
