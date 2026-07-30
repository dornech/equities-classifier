from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityIdentifier
from equities_classifier.providers.dummy import DummyProvider


def test_dummy():

    r = DummyProvider().classify([SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")])

    assert r[0].company == "Apple Inc."
