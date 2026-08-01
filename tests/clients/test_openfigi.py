"""Test openfigi client."""


import pytest

from equities_classifier.clients.openfigi.client import OpenFIGIClient, OpenFIGIResponseError
from equities_classifier.models import SecurityIdentifier, SecurityIdentifierType


def test_create_request_plan() -> None:
    """Identifiers are grouped by identifier type."""

    identifiers = [
        SecurityIdentifier(SecurityIdentifierType.ISIN, "US0378331005"),
        SecurityIdentifier(SecurityIdentifierType.CUSIP, "037833100"),
        SecurityIdentifier(SecurityIdentifierType.ISIN, "US5949181045"),
    ]

    client = OpenFIGIClient()

    plan = client._create_request_plan(identifiers)

    assert len(plan) == 2
    assert len(plan[SecurityIdentifierType.ISIN]) == 2
    assert len(plan[SecurityIdentifierType.CUSIP]) == 1


def test_create_batches() -> None:
    """Identifiers are split into batches."""

    client = OpenFIGIClient()
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


def test_parse_single_record() -> None:
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

    client = OpenFIGIClient()

    records = client._parse_record(item, source_identifier, raise_error=True)

    assert len(records) == 1

    record = records[0]

    assert record.company_name == "Apple Inc."
    assert record.ticker == "AAPL"
    assert record.figi == "BBG000B9XRY4"
    assert record.share_class_figi == "BBG001S5N8V8"
    assert record.security_type == "Common Stock"

    assert len(record.identifiers) == 3
    assert record.identifiers[0] == source_identifier


def test_parse_multiple_records() -> None:
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

    client = OpenFIGIClient()

    records = client._parse_record(
        item,
        source_identifier,
        unique_share_class_figi_only=False,
    )

    assert len(records) == 2


def test_parse_unique_share_class_figi() -> None:
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

    client = OpenFIGIClient()

    records = client._parse_record(item, source_identifier, raise_error=True)

    assert len(records) == 1


def test_parse_error_response() -> None:
    """Provider errors raise an exception."""

    client = OpenFIGIClient()

    item = {"error": "Invalid identifier"}

    source_identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "ABC",
    )

    with pytest.raises(OpenFIGIResponseError):
        client._parse_record(item, source_identifier, raise_error=True)


def test_missing_data_raises() -> None:
    """Missing data element raises an exception."""

    client = OpenFIGIClient()

    source_identifier = SecurityIdentifier(
        SecurityIdentifierType.ISIN,
        "ABC",
    )

    with pytest.raises(OpenFIGIResponseError):
        client._parse_record({}, source_identifier, raise_error=True)
