from equity_classifier.connectors.base import ClassificationProvider
from equity_classifier.enums import (
    SecurityIdentifierType,
    ClassificationSystemID,
    ClassificationLevel
 )
from equity_classifier.models import (
    ClassificationSystem,
    ClassificationNode,
    SecurityIdentifier,
    SecurityClassification
)


_DATA = {
"US0378331005": ("Apple Inc.", ("Sensitive", "Technology", "Consumer Electronics")),
"DE0007164600": ("SAP SE", ("Sensitive", "Technology", "Software"))
}


class DummyProvider(ClassificationProvider):

    def classify(self, securities):
        out = []
        for s in securities:
            company, names = _DATA.get(s.isin, ("Unknown", ("Unknown",)))
            nodes = tuple(ClassificationNode(ClassificationLevel(i + 1), n) for i, n in enumerate(names))
            out.append(
                SecurityClassification(
                    SecurityIdentifier(type=SecurityIdentifierType.ISIN, value=s),
                    company,
                    ClassificationSystemID.GECS,
                    nodes
                )
            )
        return out
