"""conftest.py for MotleyFool Selenium integration tests."""


# ruff and mypy per file settings
#

# fmt: off


import pytest

from equities_classifier.clients.motleyfool.client import MotleyFoolClient, MotleyFoolMode


@pytest.fixture(scope="module", autouse=True)
def client_selenium(request):

    # complete module using/requesting fixture i.e. test_motleyfool_integration_selenium.py must be marked
    # (scope of fixture is module!)
    if request.node.get_closest_marker("usebrowser") or request.node.get_closest_marker("usechrome"):
        with MotleyFoolClient(mode=MotleyFoolMode.SELENIUM) as clientobject:
            yield clientobject
