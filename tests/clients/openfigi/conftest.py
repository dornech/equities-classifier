import pytest

from equities_classifier.clients.openfigi import OpenFIGIClient


@pytest.fixture(scope="session")
def client():

    client = OpenFIGIClient()
    yield client
    client.close()
