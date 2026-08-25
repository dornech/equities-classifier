"""conftest.py for Yahoo tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.yahoo import YahooClient


@pytest.fixture(scope="session")
def client():

    yield YahooClient()
