"""conftest.py for Morningstar integration tests."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: RUF070, RUF105


# fmt: off


import pytest

from equities_classifier.clients.morningstar import MorningstarClient


@pytest.fixture(scope="module")
def client():

    yield MorningstarClient()
