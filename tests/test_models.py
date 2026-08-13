"""Test global models."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "union-attr"


# fmt: off


from equities_classifier.enums import (
    SecurityIdentifierType,
    ClassificationSystemID,
    ClassificationLevel,
)
from equities_classifier.models import (
    ClassificationSystem,
    ClassificationNode,
    SecurityIdentifier,
    Security,
    SecurityClassification,
)


def test_security_is_identifiable() -> None:

    securityidentifier = SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")
    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        identifiers=[securityidentifier,]
    )

    assert security.identifier(SecurityIdentifierType.ISIN) is not None
    assert security.has_identifier(SecurityIdentifierType.ISIN)


def test_identifier_lookup() -> None:
    security = Security(
        identifiers=[
            SecurityIdentifier(
                type=SecurityIdentifierType.ISIN,
                value="US0378331005",
            ),
            SecurityIdentifier(
                type=SecurityIdentifierType.SHARE_CLASS_FIGI,
                value="BBG000B9XRY4",
            ),
        ],
    )

    assert security.identifier(SecurityIdentifierType.ISIN).value == "US0378331005"
    assert security.identifier_value(SecurityIdentifierType.ISIN) == "US0378331005"
    assert security.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI).value == "BBG000B9XRY4"
    assert not security.has_identifier(SecurityIdentifierType.WKN)


def test_create_classification() -> None:

    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        identifiers=[SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005"), ],
    )

    classification_system = ClassificationSystem(
        id=ClassificationSystemID.GECS,
        display_name="Global Equity Classification Structure",
        authorities=("Morningstar",),
        hierarchy=(
            "Super Sector",
            "Sector",
            "Industry",
        ),
        supports_codes=False,
    )

    security.classifications = [
        SecurityClassification(
            system=classification_system,
            nodes=(
                ClassificationNode(
                    level=ClassificationLevel.LEVEL2,
                    value="Technology"
                ),
                ClassificationNode(
                    level=ClassificationLevel.LEVEL3,
                    value="Consumer Electronics"
                )

            )
        )
    ]

    assert security.classifications[0].system.id == ClassificationSystemID.GECS
