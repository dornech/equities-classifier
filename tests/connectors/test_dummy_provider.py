from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.connectors.dummy import DummyProvider


def test_dummy_alt():

    r = DummyProvider().classify([SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")])

    assert r[0].security.company_name == "Apple Inc."
