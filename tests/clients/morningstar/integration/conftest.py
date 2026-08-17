"""conftest.py for Morningstar integration tests."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: RUF070, RUF105


# fmt: off


import pytest

from equities_classifier.clients.morningstar import MorningstarClient


@pytest.fixture(scope="module", autouse=True)
def client(request):

    # complete module using/requesting fixture i.e. test_morningstar_integration.py must be marked
    # (scope of fixture is module!)
    if request.node.get_closest_marker("usebrowser") or request.node.get_closest_marker("usechrome"):
        with MorningstarClient() as clientobject:
            yield clientobject
