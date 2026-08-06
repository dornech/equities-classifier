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
