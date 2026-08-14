"""conftest.py for OpenFIGI tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.motleyfool.client import MotleyFoolClient, MotleyFoolMode


@pytest.fixture(scope="module")
def client_httpx():

    yield MotleyFoolClient(mode=MotleyFoolMode.HTTPX)
