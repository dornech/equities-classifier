"""conftest.py for Morningstar request tests."""

# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.morningstar import MorningstarClient


@pytest.fixture(scope="module", autouse=True)
def client(request):

    if request.node.get_closest_marker("usebrowser") or request.node.get_closest_marker("usechrome"):
        with MorningstarClient() as clientobject:
            yield clientobject
