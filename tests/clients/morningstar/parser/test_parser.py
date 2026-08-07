"""Tests for Morningstar client parser methods."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.client import MorningstarClient, MorningstarResponseError

from pathlib import Path
from tests.testhelpers import load_json


DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def identifier(apple_isin) -> SecurityIdentifier:
    return apple_isin


def test_parse_search_results_ok(client: MorningstarClient, identifier: SecurityIdentifier):

    search_result = load_json(DATA_DIR, "search_result_apple.json")
    results = client._parse_search_results(identifier, search_result,)

    assert len(results) == 20
    assert all(r.isin == "US0378331005" for r in results)
    assert results[0].company_id == "0C00000ADA"


def test_parse_record_companyid_not_unique(client: MorningstarClient, identifier: SecurityIdentifier):

    search_result_error_companyid = load_json(DATA_DIR, "search_result_apple_error_companyid.json")
    results = client._parse_search_results(identifier, search_result_error_companyid,)

    with pytest.raises(MorningstarResponseError):
        client._parse_record(
            identifier,
            results,
            raise_error=True
        )


def test_parse_record_ok(client: MorningstarClient, identifier: SecurityIdentifier):

    search_result = load_json(DATA_DIR, "search_result_apple.json")
    results = client._parse_search_results(identifier, search_result)
    record = client._parse_record(identifier, results)

    assert record.name == "Apple Inc"
    assert record.ticker == "AAPL"
    assert record.company_id == "0C00000ADA"
    assert record.identifier(SecurityIdentifierType.ISIN).value == "US0378331005"
    assert len(record.security_id) == 20
    assert len(record.performance_id) == 20
    assert len(record.exchange) == 20


def test_parse_profile_to_record(client: MorningstarClient, identifier: SecurityIdentifier):

    search_result = load_json(DATA_DIR, "search_result_apple.json")
    search_results = client._parse_search_results(identifier, search_result,)
    record = client._parse_record(identifier, search_results)

    profile = load_json(DATA_DIR, "profile_apple.json")

    assert "sections" in profile

    record = client._parse_profile_to_record(profile, record)

    assert record.sector == "Technology"
    assert record.industry == "Consumer Electronics"


def test_parse_profile_to_dict(client: MorningstarClient):

    profile = load_json(DATA_DIR, "profile_apple.json")
    attributes = client._parse_profile_to_dict(profile)

    assert attributes["sector"] == "Technology"
    assert attributes["industry"] == "Consumer Electronics"
    assert "business_description" in attributes
