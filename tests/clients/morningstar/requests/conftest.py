"""conftest.py for Morningstar request tests."""

# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.morningstar import MorningstarClient


@pytest.fixture(scope="module")
def client():

    yield MorningstarClient()
