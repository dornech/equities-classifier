"""conftest.py for Morningstar parser tests."""


# ruff and mypy per file settings
#

# fmt: off


import json
from pathlib import Path

import pytest

from equities_classifier.clients.morningstar.client import MorningstarClient


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def client():

    return MorningstarClient(test_wo_browser=True)


@pytest.fixture(scope="module")
def load_json():

    def _load(name: str):
        with open(DATA_DIR / name, encoding="utf-8") as fp:
            return json.load(fp)

    return _load
