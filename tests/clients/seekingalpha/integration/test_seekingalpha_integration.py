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

    records = client.read_provider_profile_data([apple_ticker_us])
    record = records[0]

    assert isinstance(record, SeekingAlphaRecord)

    assert record.identifiers == [apple_ticker_us]
    assert record.ticker_us == "AAPL"
    assert record.name == "Apple Inc."
    assert record.exchange == "NASDAQ"
    assert record.sector == "Information Technology"
    assert record.sector_code == "45"
    assert record.subindustry == "Technology Hardware, Storage and Peripherals"
    assert record.subindustry_code == "45202030"
