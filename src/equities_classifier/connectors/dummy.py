from equities_classifier.enums import (
    SecurityIdentifierType,
    ClassificationSystemID,
    ClassificationLevel
)
from equities_classifier.models import (
    ClassificationNode,
    SecurityIdentifier,
    Security,
    SecurityClassification
)
from equities_classifier.connectors.base import ClassificationProvider


_DATA = {
"US0378331005": ("Apple Inc.", ("Sensitive", "Technology", "Consumer Electronics")),
"DE0007164600": ("SAP SE", ("Sensitive", "Technology", "Software"))
}


# based on ClassificationProvider and adjusted - might be deleted
# Note: parameter is a list of securityidentifiers of type ISIN, not security class object!
class DummyProvider(ClassificationProvider):

    def classify(self, securityidentifiers):
        out = []
        for si in securityidentifiers:
            company, names = _DATA.get(si.value, ("Unknown", ("Unknown",)))
            security = Security(
                figi="test-FIGI",
                company_name=company,
                identifiers=tuple(SecurityIdentifier(type=SecurityIdentifierType.ISIN, value=si.value),)
            )
            nodes = tuple(ClassificationNode(ClassificationLevel(i + 1), n) for i, n in enumerate(names))
            out.append(
                SecurityClassification(
                    security,
                    ClassificationSystemID.GECS,
                    nodes
                )
            )
        return out
