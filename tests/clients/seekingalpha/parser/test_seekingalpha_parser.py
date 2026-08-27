"""Tests for Seeking Alpha client_dummy."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.seekingalpha.client import SeekingAlphaClient, SeekingAlphaResponseError
from equities_classifier.clients.seekingalpha.models import SeekingAlphaRecord


@pytest.fixture
def ssr_html() -> str:
    """Return valid Seeking Alpha SSR_DATA HTML."""
    return """
    <html>
    <script>
    window.SSR_DATA = {
        "symbol": {
            "response": {
                "data": {
                    "id": "146",
                    "type": "ticker",
                    "attributes": {
                        "name": "AAPL",
                        "companyName": "Apple Inc.",
                        "exchange": "NASDAQ",
                        "sectorDisplay": "Information Technology",
                        "industryDisplay":
                            "Technology Hardware, Storage and Peripherals"
                    },
                    "relationships": {
                        "sector": {
                            "data": {
                                "id": "45",
                                "type": "sector"
                            }
                        },
                        "subIndustry": {
                            "data": {
                                "id": "45202030",
                                "type": "subIndustry"
                            }
                        }
                    }
                },
                "included": []
            }
        }
    };
    </script>
    </html>
    """


def test_parse_record(client_dummy: SeekingAlphaClient, apple_ticker_us: SecurityIdentifier, ssr_html: str) -> None:
    """Test parsing of Seeking Alpha SSR_DATA."""

    result = client_dummy._parse_record(apple_ticker_us, ssr_html, False)

    assert isinstance(result, SeekingAlphaRecord)
    assert result.identifiers == [apple_ticker_us]
    assert result.ticker_us == "AAPL"
    assert result.name == "Apple Inc."
    assert result.exchange == "NASDAQ"
    assert result.sector == "Information Technology"
    assert result.sector_code == "45"
    assert result.subindustry == "Technology Hardware, Storage and Peripherals"
    assert result.subindustry_code == "45202030"


def test_parse_record_without_ssr_data(client_dummy: SeekingAlphaClient, apple_ticker_us: SecurityIdentifier) -> None:
    """Test parsing response without SSR_DATA."""

    result = client_dummy._parse_record(apple_ticker_us, "<html><body>nothing</body></html>", False)

    assert result is None


def test_parse_record_invalid_json(client_dummy: SeekingAlphaClient, apple_ticker_us: SecurityIdentifier) -> None:
    """Test parsing invalid SSR_DATA."""

    html = """
    <script>
    window.SSR_DATA = {"symbol": invalid};
    </script>
    """

    result = client_dummy._parse_record(apple_ticker_us, html, False)

    assert result is None


def test_parse_record_missing_data(client_dummy: SeekingAlphaClient, apple_ticker_us: SecurityIdentifier) -> None:
    """Test missing symbol response data."""

    html = """
    <script>
    window.SSR_DATA = {
        "symbol": {
            "response": {}
        }
    };
    </script>
    """

    result = client_dummy._parse_record(apple_ticker_us, html, False)

    assert result is None


def test_parse_record_missing_attributes(client_dummy: SeekingAlphaClient, apple_ticker_us: SecurityIdentifier) -> None:
    """Test missing attributes."""

    html = """
    <script>
    window.SSR_DATA = {
        "symbol": {
            "response": {
                "data": {
                    "attributes": {},
                    "relationships": {}
                }
            }
        }
    };
    </script>
    """

    result = client_dummy._parse_record(apple_ticker_us, html, False)

    assert result is not None
    assert result.ticker_us is None
    assert result.name is None
    assert result.exchange is None
    assert result.sector is None
    assert result.sector_code is None
    assert result.subindustry is None
    assert result.subindustry_code is None


def test_parse_record_raise_error_without_ssr_data(
    client_dummy: SeekingAlphaClient,
    apple_ticker_us: SecurityIdentifier,
) -> None:
    """Test parsing error with raise_error enabled."""

    with pytest.raises(SeekingAlphaResponseError):
        client_dummy._parse_record(apple_ticker_us, "<html></html>", True)
