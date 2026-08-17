"""Tests for Morningstar request methods."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, union-attr"

# fmt: off


import pytest

from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.client import MorningstarClient


pytestmark = [
    pytest.mark.usebrowser,
    pytest.mark.usechrome,
    pytest.mark.usefixtures("client"),
    pytest.mark.usefixtures("apple_isin"),
]


def test_execute_search_request(client: MorningstarClient, apple_isin: SecurityIdentifier):

    response = client._execute_search_request(apple_isin)

    assert isinstance(response, dict)
    assert "count" in response
    assert "results" in response
    assert response["count"] >= 1
    assert len(response["results"]) >= 1


def test_get_access_token(client: MorningstarClient):

    token = client._get_access_token()

    assert isinstance(token, str)
    assert len(token) > 20


def test_get_access_token_cached(client: MorningstarClient):
    """The second call should return the cached token."""

    token1 = client._get_access_token()
    token2 = client._get_access_token()

    assert token1 == token2


def test_execute_profile_request(client: MorningstarClient, apple_isin: SecurityIdentifier):

    search_response = client._execute_search_request(apple_isin)
    search_results = client._parse_search_results(
        apple_isin,
        search_response,
    )
    record = client._parse_record(
        source_identifier=apple_isin,
        search_results=search_results,
    )

    profile = client._execute_profile_request(
        security_id=record.company_id,
    )

    assert isinstance(profile, dict)
    assert "sections" in profile
    assert profile["performanceId"] == record.company_id
