"""Integration tests for the Morningstar client."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.client import MorningstarClient


pytestmark = [
    pytest.mark.usefixtures("client"),
    pytest.mark.usefixtures("apple_isin"),
    pytest.mark.local,
    pytest.mark.integration,
]


def test_read_provider_base_data(client: MorningstarClient, apple_isin: SecurityIdentifier) -> None:

    records = client.read_provider_base_data([apple_isin])

    assert len(records) == 1

    record = records[0]

    assert record.name == "Apple Inc"
    assert record.company_id is not None

    assert len(record.security_id) > 0
    assert len(record.performance_id) > 0
    assert len(record.exchange) > 0

    identifier = record.identifier(SecurityIdentifierType.ISIN)
    assert identifier is not None
    assert identifier.value == apple_isin.value


def test_read_provider_profile_data(client: MorningstarClient, apple_isin: SecurityIdentifier) -> None:

    records = client.read_provider_base_data([apple_isin])
    records = client.read_provider_profile_data(records)

    record = records[0]

    assert record.name == "Apple Inc"
    assert record.sector == "Technology"
    assert record.industry == "Consumer Electronics"
    assert record.business_description is not None
    assert len(record.business_description) > 100

    assert len(record.identifiers) >= 2
