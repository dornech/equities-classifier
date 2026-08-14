"""Integration tests for Motley-Fool client."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, union-attr"

# fmt: off


import pytest

from equities_classifier.clients.motleyfool.client import MotleyFoolClient
from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier


pytestmark = [
    pytest.mark.usefixtures("apple_ticker"),
    pytest.mark.local,
    pytest.mark.integration,
]


@pytest.mark.usefixtures("client_httpx")
def test_read_provider_profile_data_httpx(
    client_httpx: MotleyFoolClient,
    apple_ticker: SecurityIdentifier,
):
    """Integration test against the live Motley Fool website using httpx."""

    records = client_httpx.read_provider_profile_data([apple_ticker], raise_error=True,)

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


@pytest.mark.usefixtures("client_selenium")
def test_read_provider_profile_data_selenium(
    client_selenium: MotleyFoolClient,
    apple_ticker: SecurityIdentifier,
):
    """Integration test against the live Motley Fool website using Selenium."""

    records = client_selenium.read_provider_profile_data([apple_ticker], raise_error=True,)

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
