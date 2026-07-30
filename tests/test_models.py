from equities_classifier.enums import (
    SecurityIdentifierType,
    ClassificationLevel,
    ClassificationSystem,
)
from equities_classifier.models import (
    ClassificationNode,
    SecurityIdentifier,
    SecurityClassification,
)


def test_security_is_hashable() -> None:

    security = SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")

    assert hash(security)


def test_create_classification() -> None:

    classification = SecurityClassification(
        securityID=SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005"),
        company_name="Apple Inc.",
        classification_system=ClassificationSystem.GICS,
        nodes=(
            ClassificationNode(
                level=ClassificationLevel.LEVEL1,
                name="Information Technology",
                code="45",
            ),
        ),
    )

    assert classification.company_name == "Apple Inc."
