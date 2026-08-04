"""conftest.py for Morningstar request tests."""


import pytest

from equities_classifier.clients.morningstar import MorningstarClient


@pytest.fixture(scope="session")
def client():

    client = MorningstarClient()
    yield client
    client.close()
