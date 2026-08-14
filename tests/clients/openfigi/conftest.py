"""conftest.py for OpenFIGI tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.openfigi import OpenFIGIClient


@pytest.fixture(scope="session")
def client():

    yield OpenFIGIClient()
