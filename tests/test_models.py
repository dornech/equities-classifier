"""Test global models."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "union-attr"


# fmt: off


import pytest

from equities_classifier.enums import (
    SecurityIdentifierType,
    ClassificationSystemID,
    ClassificationLevel,
)
from equities_classifier.models import (
    ClassificationSystem,
    ClassificationNode,
    SecurityIdentifier,
    SecurityIdentifierList,
    Security,
    SecurityClassification,
)


def test_security_is_identifiable() -> None:

    securityidentifier = SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005")
    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        identifiers=SecurityIdentifierList([securityidentifier,])
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
        identifiers=SecurityIdentifierList([securityidentifier,])
    )

    assert security.has_identifier(SecurityIdentifierType.TICKER)
    assert security.identifier(SecurityIdentifierType.TICKER).value_cleaned == "APPL"
    assert security.identifier(SecurityIdentifierType.TICKER).value == "APPL.US"


def test_identifier_lookup() -> None:
    security = Security(
        identifiers=SecurityIdentifierList([
            SecurityIdentifier(
                type=SecurityIdentifierType.ISIN,
                value="US0378331005",
            ),
            SecurityIdentifier(
                type=SecurityIdentifierType.SHARE_CLASS_FIGI,
                value="BBG000B9XRY4",
            ),
        ]),
    )

    assert security.identifier(SecurityIdentifierType.ISIN).value == "US0378331005"
    assert security.identifier_value(SecurityIdentifierType.ISIN) == "US0378331005"
    assert security.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI).value == "BBG000B9XRY4"
    assert security.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI).value_cleaned == "BBG000B9XRY4"
    assert security.identifier(SecurityIdentifierType.SHARE_CLASS_FIGI).country is None
    assert not security.has_identifier(SecurityIdentifierType.WKN)


def test_empty() -> None:
    identifiers = SecurityIdentifierList()

    assert identifiers == []


def test_init(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier
) -> None:

    identifiers = SecurityIdentifierList([apple_isin, apple_ticker])

    assert identifiers == [apple_isin, apple_ticker]


def test_init_rejects_invalid_type() -> None:

    with pytest.raises(TypeError):
        SecurityIdentifierList(["AAPL"])  # type: ignore[list-item]


def test_init_rejects_duplicate_types(
    deere_ticker: SecurityIdentifier,
    deere_ticker_country: SecurityIdentifier,
) -> None:

    with pytest.raises(ValueError):
        SecurityIdentifierList([deere_ticker, deere_ticker_country])


def test_append(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList()

    identifiers.append(apple_isin)
    identifiers.append(apple_ticker)

    assert identifiers == [apple_isin, apple_ticker]


def test_append_rejects_invalid_type(
    apple_isin: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin])

    with pytest.raises(TypeError):
        identifiers.append("AAPL")  # type: ignore[arg-type]


def test_append_rejects_duplicate_type(
    deere_ticker: SecurityIdentifier,
    deere_ticker_country: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([deere_ticker])

    with pytest.raises(ValueError):
        identifiers.append(deere_ticker_country)

    assert identifiers == [deere_ticker]


def test_extend(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
    sedol_dummy: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList()

    identifiers.extend([apple_isin, apple_ticker, sedol_dummy])

    assert identifiers == [apple_isin, apple_ticker, sedol_dummy]


def test_extend_rejects_duplicate_type(
    deere_ticker: SecurityIdentifier,
    deere_ticker_country: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([deere_ticker])

    with pytest.raises(ValueError):
        identifiers.extend([deere_ticker_country])

    assert identifiers == [deere_ticker]


def test_extend_rejects_duplicates_within_iterable(
    deere_ticker: SecurityIdentifier,
    deere_ticker_country: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList()

    with pytest.raises(ValueError):
        identifiers.extend([deere_ticker, deere_ticker_country])

    assert identifiers == []


def test_insert(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin])

    identifiers.insert(0, apple_ticker)

    assert identifiers == [apple_ticker, apple_isin]


def test_insert_rejects_duplicate_type(
    deere_ticker: SecurityIdentifier,
    deere_ticker_country: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([deere_ticker])

    with pytest.raises(ValueError):
        identifiers.insert(0, deere_ticker_country)

    assert identifiers == [deere_ticker]


def test_setitem_replaces_same_type(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
    deere_ticker: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin, deere_ticker])

    identifiers[1] = apple_ticker

    assert identifiers == [apple_isin, apple_ticker]


def test_setitem_rejects_duplicate_type(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
    deere_ticker: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin, apple_ticker])

    with pytest.raises(ValueError):
        identifiers[0] = deere_ticker

    assert identifiers == [apple_isin, apple_ticker]


def test_setitem_rejects_invalid_type(
    apple_isin: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin])

    with pytest.raises(TypeError):
        identifiers[0] = "AAPL"  # type: ignore[call-overload]

    assert identifiers == [apple_isin]


def test_slice_assignment(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
    sedol_dummy: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin, apple_ticker])

    identifiers[:] = [sedol_dummy, apple_ticker]

    assert identifiers == [sedol_dummy, apple_ticker]


def test_slice_assignment_rejects_duplicate_type(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
    deere_ticker: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin, apple_ticker])

    with pytest.raises(ValueError):
        identifiers[:] = [deere_ticker, apple_ticker, apple_isin]

    assert identifiers == [apple_isin, apple_ticker]


def test_slice_assignment_rejects_invalid_type(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin, apple_ticker])

    with pytest.raises(TypeError):
        identifiers[:] = [apple_isin, "AAPL"]  # type: ignore[list-item]

    assert identifiers == [apple_isin, apple_ticker]


def test_setitem_can_replace_with_new_type(
    apple_isin: SecurityIdentifier,
    apple_ticker: SecurityIdentifier,
) -> None:

    identifiers = SecurityIdentifierList([apple_isin])

    identifiers[0] = apple_ticker

    assert identifiers == [apple_ticker]


def test_create_classification() -> None:

    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        identifiers=SecurityIdentifierList([
            SecurityIdentifier(type=SecurityIdentifierType.ISIN, value="US0378331005"),
        ]),
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
