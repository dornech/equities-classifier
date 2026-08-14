"""Tests for Motley-Fool client."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, union-attr"

# fmt: off


import pytest

from equities_classifier.clients.motleyfool.client import (
    MotleyFoolClient,
    MotleyFoolResponseError,
)
from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier

from pathlib import Path
from tests.testhelpers import load_text


DATA_DIR = Path(__file__).parent.parent / "data"


pytestmark = [
    pytest.mark.usefixtures("client_httpx"),
]


def test_parse_search_results_ok(
    client_httpx: MotleyFoolClient,
    apple_ticker: SecurityIdentifier,
) -> None:

    response = load_text(DATA_DIR, "search_response_aapl.txt")
    results = client_httpx._parse_search_results(apple_ticker, response,)

    assert len(results) == 10

    first = results[0]

    assert first.ticker == "AAPL"
    assert first.name == "Apple"
    assert first.exchange == "NASDAQ"
    assert first.home_country_code == "US"


def test_parse_search_results_invalid_response(
    client_httpx: MotleyFoolClient,
    apple_ticker: SecurityIdentifier,
) -> None:

    with pytest.raises(MotleyFoolResponseError):
        client_httpx._parse_search_results(
            apple_ticker,
            "foobar",
            raise_error=True,
        )


def test_select_search_result(
    client_httpx: MotleyFoolClient,
    apple_ticker: SecurityIdentifier,
) -> None:

    response = load_text(DATA_DIR, "search_response_aapl.txt")
    results = client_httpx._parse_search_results(
        apple_ticker,
        response,
    )
    result = client_httpx._select_search_result(
        apple_ticker,
        results,
    )

    assert result.ticker == "AAPL"
    assert result.exchange == "NASDAQ"


def test_select_search_result_not_found(
    client_httpx: MotleyFoolClient,
    apple_ticker: SecurityIdentifier,
) -> None:

    with pytest.raises(MotleyFoolResponseError):
        client_httpx._select_search_result(
            apple_ticker,
            [],
            raise_error=True,
        )


def test_parse_record(
    client_httpx: MotleyFoolClient,
    apple_ticker: SecurityIdentifier,
) -> None:

    search_response = load_text(DATA_DIR, "search_response_aapl.txt")
    results = client_httpx._parse_search_results(apple_ticker, search_response,)
    result = client_httpx._select_search_result(apple_ticker, results,)

    html = load_text(DATA_DIR, "company_aapl.html")
    record = client_httpx._parse_record(result, html,)

    assert record.name == "Apple"
    assert record.ticker == "AAPL"
    assert record.exchange == "NASDAQ"

    assert record.sector == "Information Technology"
    assert record.industry == "Technology Hardware, Storage and Peripherals"

    assert record.identifier(
        SecurityIdentifierType.TICKER
    ).value == "AAPL"
