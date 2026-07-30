from equities_classifier.enums import (
    SecurityIdentifierType,
    ClassificationSystemID,
    ClassificationLevel,
)
from equities_classifier.models import (
    ClassificationNode,
    SecurityIdentifier,
    Security,
    SecurityClassification,
)


def test_security_is_hashable() -> None:

    securityidentifier = SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")
    security = Security(
        figi="test-FIGI",
        company_name="Apple Inc.",
        identifiers=tuple(securityidentifier,)
    )

    assert hash(security)


def test_identifier_lookup() -> None:
    security = Security(
        identifiers=(
            SecurityIdentifier(
                type=SecurityIdentifierType.ISIN,
                value="US0378331005",
            ),
            SecurityIdentifier(
                type=SecurityIdentifierType.FIGI,
                value="BBG000B9XRY4",
            ),
        ),
    )

    assert security.identifier_value(SecurityIdentifierType.ISIN) == "US0378331005"
    assert security.identifier_value(SecurityIdentifierType.FIGI) == "BBG000B9XRY4"
    assert security.identifier(SecurityIdentifierType.WKN) is None
    assert not security.has_identifier(SecurityIdentifierType.WKN)


def test_create_classification() -> None:

    security = Security(
        figi="test-FIGI",
        company_name="Apple Inc.",
        identifiers=tuple(SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005"), ),
    )
    classification = SecurityClassification(
        security=security,
        system=ClassificationSystemID.GICS,
        nodes=(
            ClassificationNode(
                level=ClassificationLevel.LEVEL1,
                name="Information Technology",
                code="45",
            ),
        ),
    )

    assert classification.security.company_name == "Apple Inc."
