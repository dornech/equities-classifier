"""conftest.py for Morningstar parser tests."""


import json
from pathlib import Path

import pytest

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.clients.morningstar.client import MorningstarClient


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def client():
    return MorningstarClient(test_wo_browser=True)


@pytest.fixture
def identifier():
    return SecurityIdentifier(
        type=SecurityIdentifierType.ISIN,
        value="US0378331005",
    )


@pytest.fixture
def load_json():

    def _load(name: str):
        with open(DATA_DIR / name, encoding="utf-8") as fp:
            return json.load(fp)

    return _load


# def load_json(filename: str):
#     with open(DATA_DIR / filename, encoding="utf-8") as fp:
#         return json.load(fp)
#
#
# @pytest.fixture
# def search_result():
#     return load_json("search_result_apple.json")
#
#
# @pytest.fixture
# def search_result_error_count():
#     return load_json("search_result_error_count.json")
#
#
# @pytest.fixture
# def search_result_error_companyid():
#     return load_json("search_result_error_companyid.json")
#
#
# @pytest.fixture
# def profile():
#     return load_json("profile_apple.json")
