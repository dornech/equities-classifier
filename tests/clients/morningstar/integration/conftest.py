"""conftest.py for Morningstar integration tests."""


import pytest

from equities_classifier.clients.morningstar import MorningstarClient


@pytest.fixture(scope="module")
def client():

    client = MorningstarClient()
    yield client
    # client.close()   -> client should do close itself as part of contextmanager
