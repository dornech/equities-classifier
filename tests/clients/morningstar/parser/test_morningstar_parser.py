"""Tests for Morningstar client parser methods."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, no-any-return, union-attr"

# fmt: off


import pytest

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.models import MorningstarRecord
from equities_classifier.clients.morningstar.client import MorningstarClient

from pathlib import Path
from tests.testhelpers import load_json


DATA_DIR = Path(__file__).parent.parent / "data"


pytestmark = [
    pytest.mark.usefixtures("client_dummy"),
]


@pytest.fixture
def identifier(apple_isin) -> SecurityIdentifier:
    return apple_isin


def test_parse_search_results_ok(client_dummy: MorningstarClient, identifier: SecurityIdentifier):

    search_result = load_json(DATA_DIR, "search_result_apple.json")
    results = client_dummy._parse_search_results(identifier, search_result)

    assert len(results) == 20
    assert all(r.isin == "US0378331005" for r in results)
    assert results[0].company_id == "0C00000ADA"


def test_parse_record_ok(client_dummy: MorningstarClient, identifier: SecurityIdentifier):

    search_result = load_json(DATA_DIR, "search_result_apple.json")
    results = client_dummy._parse_search_results(identifier, search_result)
    records: list[MorningstarRecord] = []
    client_dummy._parse_records(identifier, results, records)
    record = records[0]

    assert record.name == "Apple Inc"
    assert record.ticker == "AAPL"
    assert record.company_id == "0C00000ADA"
    assert record.identifier(SecurityIdentifierType.ISIN).value == "US0378331005"
    assert len(record.security_id) == 20
    assert len(record.performance_id) == 20
    assert len(record.exchange) == 20


def test_parse_profile_to_record(client_dummy: MorningstarClient, identifier: SecurityIdentifier):

    search_result = load_json(DATA_DIR, "search_result_apple.json")
    search_results = client_dummy._parse_search_results(identifier, search_result)
    records: list[MorningstarRecord] = []
    client_dummy._parse_records(identifier, search_results, records)

    profile = load_json(DATA_DIR, "profile_apple.json")

    assert "sections" in profile

    record = client_dummy._parse_profile_to_record(profile, records[0])

    assert record.sector == "Technology"
    assert record.industry == "Consumer Electronics"


def test_parse_profile_to_dict(client_dummy: MorningstarClient, identifier: SecurityIdentifier):

    profile = load_json(DATA_DIR, "profile_apple.json")
    attributes = client_dummy._parse_profile_to_dict(identifier, profile)

    assert attributes["sector"] == "Technology"
    assert attributes["industry"] == "Consumer Electronics"
    assert "business_description" in attributes
