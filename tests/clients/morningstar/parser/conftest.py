"""conftest.py for Morningstar parser tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.morningstar.client import MorningstarClient


@pytest.fixture(scope="module")
def client_dummy():

    return MorningstarClient(test_wo_browser=True)
