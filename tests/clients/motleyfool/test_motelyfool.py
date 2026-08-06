"""Tests for Motley-Fool client."""



# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.motleyfool.client import (
    MotleyFoolClient,
    MotleyFoolResponseError,
)
from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier


pytestmark = pytest.mark.usefixtures("client")

client = MotleyFoolClient()


def test_parse_search_results_ok(
    client: MotleyFoolClient,
    identifier: SecurityIdentifier,
    load_text,
) -> None:


    response = load_text("search_response_aapl.txt")
    results = client._parse_search_results(identifier, response,)

    assert len(results) == 10

    first = results[0]

    assert first.ticker == "AAPL"
    assert first.name == "Apple"
    assert first.exchange == "NASDAQ"
    assert first.home_country_code == "US"


def test_parse_search_results_invalid_response(
    client: MotleyFoolClient,
    identifier: SecurityIdentifier,
) -> None:

    with pytest.raises(MotleyFoolResponseError):
        client._parse_search_results(
            identifier,
            "foobar",
            raise_error=True,
        )


def test_select_search_result(
    client: MotleyFoolClient,
    identifier: SecurityIdentifier,
    load_text,
) -> None:

    response = load_text("search_response_aapl.txt")
    results = client._parse_search_results(
        identifier,
        response,
    )
    result = client._select_search_result(
        identifier,
        results,
    )

    assert result.ticker == "AAPL"
    assert result.exchange == "NASDAQ"


def test_select_search_result_not_found(
    client: MotleyFoolClient,
    identifier: SecurityIdentifier,
) -> None:

    with pytest.raises(MotleyFoolResponseError):
        client._select_search_result(
            identifier,
            [],
            raise_error=True,
        )


def test_parse_record(
    client: MotleyFoolClient,
    identifier: SecurityIdentifier,
    load_text,
) -> None:

    search_response = load_text("search_response_aapl.txt")
    results = client._parse_search_results(identifier, search_response,)
    result = client._select_search_result(identifier, results,)

    html = load_text("company_aapl.html")
    record = client._parse_record(result, html,)

    assert record.name == "Apple"
    assert record.ticker == "AAPL"
    assert record.exchange == "NASDAQ"

    assert record.sector == "Information Technology"
    assert record.industry == "Technology Hardware, Storage and Peripherals"

    assert record.identifier(
        SecurityIdentifierType.TICKER
    ).value == "AAPL"


def test_read_provider_profile_data(
    client: MotleyFoolClient,
    identifier: SecurityIdentifier,
):
    """Integration test against the live Motley Fool website."""

    records = client.read_provider_profile_data([identifier], raise_error=True,)

    assert len(records) == 1

    record = records[0]

    assert record.name is not None
    assert record.name.startswith("Apple")

    assert record.ticker == "AAPL"
    assert record.exchange == "NASDAQ"

    assert record.sector == "Information Technology"
    assert record.industry == "Technology Hardware, Storage and Peripherals"

    isin = record.identifier(SecurityIdentifierType.TICKER)
    assert isin is not None
    assert isin.value == "AAPL"
