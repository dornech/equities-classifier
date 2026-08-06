"""conftest.py for OpenFIGI tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from pathlib import Path

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.motleyfool.client import MotleyFoolClient


_DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def client():

    client = MotleyFoolClient()
    yield client
    client.close()


@pytest.fixture
def identifier():

    return SecurityIdentifier(
        type=SecurityIdentifierType.TICKER,
        value="AAPL",
    )


@pytest.fixture
def load_text():

    def _load(filename: str) -> str:
        return (_DATA / filename).read_text(encoding="utf-8")

    return _load
