"""conftest.py for all tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier


@pytest.fixture(scope="session")
def apple_isin() -> SecurityIdentifier:
    return SecurityIdentifier(
        type=SecurityIdentifierType.ISIN,
        value="US0378331005",
    )


@pytest.fixture(scope="session")
def apple_ticker() -> SecurityIdentifier:
    return SecurityIdentifier(
        type=SecurityIdentifierType.TICKER,
        value="AAPL",
    )


@pytest.fixture(scope="session")
def abt_ticker() -> SecurityIdentifier:
    return SecurityIdentifier(
        type=SecurityIdentifierType.TICKER,
        value="ABT",
    )


@pytest.fixture(scope="session")
def abt_ticker_country() -> SecurityIdentifier:
    return SecurityIdentifier(
        type=SecurityIdentifierType.TICKER,
        value="ABT.US",
    )


@pytest.fixture(scope="session")
def deere_ticker() -> SecurityIdentifier:
    return SecurityIdentifier(
        type=SecurityIdentifierType.TICKER,
        value="DE",
    )


@pytest.fixture(scope="session")
def deere_ticker_country() -> SecurityIdentifier:
    return SecurityIdentifier(
        type=SecurityIdentifierType.TICKER,
        value="DE.US",
    )


@pytest.fixture(scope="session")
def sedol_dummy() -> SecurityIdentifier:
    return SecurityIdentifier(
        type=SecurityIdentifierType.SEDOL,
        value="2046251",
    )
