"""Tests for Yahoo Finance client."""


# ruff and mypy per file settings
#
# ruff: noqa: FBT001
# others
# ruff: noqa: RUF105

# fmt: off


import pytest

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.yahoo.models import YahooSearchResult


@pytest.mark.parametrize(
    ("identifier_type", "expected"),
    [
        (SecurityIdentifierType.ISIN, True),
        (SecurityIdentifierType.TICKER, True),
        (SecurityIdentifierType.CUSIP, False),
        (SecurityIdentifierType.SEDOL, False),
        (SecurityIdentifierType.WKN, False),
    ],
)
def test_supports_identifier_type(
    client,
    identifier_type: SecurityIdentifierType,
    expected: bool,
) -> None:
    """Test supported identifier types."""

    assert (
        client.supports_identifier_type(identifier_type)
        is expected
    )


def test_parse_search_results(client) -> None:
    """Test parsing Yahoo Finance search results."""

    identifier = SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")
    response = {
        "quotes": [
            {
                "symbol": "AAPL",
                "shortname": "Apple Inc.",
                "longname": "Apple Inc.",
                "quoteType": "EQUITY",
                "exchange": "NMS",
                "exchDisp": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "score": 100000,
            },
        ],
    }
    results = client._parse_search_results(
        identifier,
        response,
    )

    assert len(results) == 1
    assert results[0].symbol == "AAPL"
    assert results[0].longname == "Apple Inc."
    assert results[0].sector == "Technology"
    assert results[0].industry == "Consumer Electronics"


def test_parse_record(client) -> None:
    """Test creation of Yahoo provider record."""

    source_identifier = SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")
    search_result = YahooSearchResult(
        symbol="AAPL",
        shortname="Apple Inc.",
        longname="Apple Inc.",
        quote_type="EQUITY",
        exchange="NMS",
        exch_disp="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
    )
    record = client._parse_record(source_identifier, search_result)

    assert record.name == "Apple Inc."
    assert record.ticker == "AAPL"
    assert record.sector == "Technology"
    assert record.industry == "Consumer Electronics"

    assert record.identifier(SecurityIdentifierType.ISIN) == source_identifier

    assert (
        record.identifier(SecurityIdentifierType.TICKER) ==
        SecurityIdentifier(type=SecurityIdentifierType.TICKER, value="AAPL.US")
    )
