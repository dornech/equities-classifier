"""Integration tests for Morningstar request methods."""


from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.client import MorningstarClient


def test_execute_search_request(client: MorningstarClient):

    identifier = SecurityIdentifier(
        type=SecurityIdentifierType.ISIN,
        value="US0378331005",
    )

    response = client._execute_search_request(identifier)

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


def test_execute_profile_request(client: MorningstarClient):

    identifier = SecurityIdentifier(
        type=SecurityIdentifierType.ISIN,
        value="US0378331005",
    )

    search_response = client._execute_search_request(identifier)
    search_results = client._parse_search_results(
        identifier,
        search_response,
    )
    record = client._parse_record(
        source_identifier=identifier,
        search_results=search_results,
    )

    profile = client._execute_profile_request(
        security_id=record.security_id[0],
    )

    assert isinstance(profile, dict)
    assert "sections" in profile
    assert profile["companyID"] == record.company_id[0]
