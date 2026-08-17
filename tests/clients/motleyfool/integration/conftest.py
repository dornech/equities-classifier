"""conftest.py for OpenFIGI tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.motleyfool.client import MotleyFoolClient, MotleyFoolMode


@pytest.fixture(scope="module", autouse=True)
def client_httpx():

    yield MotleyFoolClient(mode=MotleyFoolMode.HTTPX)


@pytest.fixture(scope="module", autouse=True)
def client_selenium(request):

    with MotleyFoolClient(mode=MotleyFoolMode.SELENIUM) as clientobject:
        yield clientobject
