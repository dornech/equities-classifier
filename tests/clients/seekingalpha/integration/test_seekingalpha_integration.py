"""Integration tests for the Morningstar client."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.seekingalpha.client import SeekingAlphaClient
from equities_classifier.clients.seekingalpha.models import SeekingAlphaRecord


# note: testcases can be executed successfully only locally
# (issue with undetected-chromedriver / CloudFront)


pytestmark = [
    pytest.mark.usefixtures("client"),
    pytest.mark.usefixtures("apple_ticker_us"),
    pytest.mark.usebrowser,
    pytest.mark.usechrome,
    pytest.mark.integration,
    pytest.mark.local,
]


def test_read_provider_profile_data(client: SeekingAlphaClient, apple_ticker_us: SecurityIdentifier) -> None:

    results = client.read_provider_profile_data([apple_ticker_us])
    result = results[0]

    assert isinstance(result, SeekingAlphaRecord)

    assert result.identifiers == [apple_ticker_us]
    assert result.ticker_us == "AAPL"
    assert result.name == "Apple Inc."
    assert result.exchange == "NASDAQ"
    assert result.sector == "Information Technology"
    assert result.sector_code == "45"
    assert result.subindustry == "Technology Hardware, Storage and Peripherals"
    assert result.subindustry_code == "45202030"
