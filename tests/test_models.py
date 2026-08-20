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
    assert security.identifier(SecurityIdentifierType.ISIN).value == "US0378331005"
    assert security.identifier(SecurityIdentifierType.ISIN).value_cleaned == "US0378331005"
    assert security.has_identifier(SecurityIdentifierType.ISIN)


def test_security_cleaned_ticker() -> None:

    securityidentifier = SecurityIdentifier(type=SecurityIdentifierType.TICKER, value="APPL.US")
    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        identifiers=[securityidentifier,]
    )

    assert security.has_identifier(SecurityIdentifierType.TICKER)
    assert security.identifier(SecurityIdentifierType.TICKER).value_cleaned == "APPL"
    assert security.identifier(SecurityIdentifierType.TICKER).value == "APPL.US"


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
    assert security.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI).value_cleaned == "BBG000B9XRY4"
    assert security.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI).country is None
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
        short_name="GECS",
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
            nodes={
                ClassificationLevel.LEVEL2: ClassificationNode(value="Technology"),
                ClassificationLevel.LEVEL3: ClassificationNode(value="Consumer Electronics")
            }
        )
    ]

    assert security.classifications[0].system.id == ClassificationSystemID.GECS
