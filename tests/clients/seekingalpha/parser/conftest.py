"""conftest.py for SeekingAlpha parser tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.seekingalpha.client import SeekingAlphaClient


@pytest.fixture(scope="module")
def client_dummy():

    return SeekingAlphaClient(test_wo_browser=True)
