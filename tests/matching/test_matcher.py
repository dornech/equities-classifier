"""Unit tests for SecurityMatcher."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "no-any-return"

# fmt: off


from typing import ClassVar
from dataclasses import dataclass

import pytest

from equities_classifier.enums import (
    DataSourceID,
    SecurityIdentifierType,
)
from equities_classifier.models import SecurityIdentifier, SecurityProviderRecord
from equities_classifier.matching.matcher import (
    MatchType,
    SecurityMatcher,
)


@dataclass(slots=True, kw_only=True)
class TestProviderRecord(SecurityProviderRecord):
    """Provider record for matcher tests."""

    datasource: ClassVar[DataSourceID] = DataSourceID.MORNINGSTAR

    name: str | None = None
    ticker: str | None = None


def provider_record(
    *,
    name: str,
    ticker: str | None = None,
    isin: str | None = None,
) -> SecurityProviderRecord:
    """Create a provider record for matcher tests."""

    record = TestProviderRecord(
        name=name,
        ticker=ticker,
    )

    if ticker is not None:
        record.identifiers.append(
            SecurityIdentifier(type=SecurityIdentifierType.TICKER, value=ticker,)
        )
    if isin is not None:
        record.identifiers.append(
            SecurityIdentifier(type=SecurityIdentifierType.ISIN, value=isin,
            )
        )

    return record


def test_match_ticker_and_isin() -> None:
    """Equal ticker and ISIN must produce a match."""

    left = provider_record(
        name="Apple Inc.",
        ticker="AAPL",
        isin="US0378331005",
    )
    right = provider_record(
        name="Apple Inc.",
        ticker="AAPL",
        isin="US0378331005",
    )

    result = SecurityMatcher().match(left, right)

    assert result.matched
    assert result.match_type is MatchType.TICKER_AND_ISIN
    assert result.warning is None


def test_match_isin_and_similar_name_with_different_ticker() -> None:
    """Equal ISIN and similar name may match despite different tickers."""

    left = provider_record(
        name="Apple Inc.",
        ticker="AAPL",
        isin="US0378331005",
    )
    right = provider_record(
        name="Apple Incorporated",
        ticker="APC",
        isin="US0378331005",
    )

    result = SecurityMatcher().match(left, right)

    assert result.matched
    assert result.match_type is MatchType.ISIN_NAME
    assert result.warning is not None
    assert result.name_similarity is not None


def test_match_ticker_and_similar_name_without_isin() -> None:
    """Equal ticker and similar name must produce a match."""

    left = provider_record(
        name="Apple Inc.",
        ticker="AAPL",
    )
    right = provider_record(
        name="Apple Incorporated",
        ticker="AAPL",
    )

    result = SecurityMatcher().match(left, right)

    assert result.matched
    assert result.match_type is MatchType.TICKER_NAME
    assert result.warning is None


def test_no_match_different_ticker_and_isin() -> None:
    """Different ticker and ISIN must not match."""

    left = provider_record(
        name="Apple Inc.",
        ticker="AAPL",
        isin="US0378331005",
    )
    right = provider_record(
        name="Microsoft Corporation",
        ticker="MSFT",
        isin="US5949181045",
    )

    result = SecurityMatcher().match(left, right)

    assert not result.matched
    assert result.match_type is None


def test_no_match_same_isin_with_different_name() -> None:
    """Equal ISIN alone must not be sufficient when names differ."""

    left = provider_record(
        name="Apple Inc.",
        ticker="AAPL",
        isin="US0378331005",
    )
    right = provider_record(
        name="Microsoft Corporation",
        ticker="MSFT",
        isin="US0378331005",
    )

    result = SecurityMatcher().match(left, right)

    assert not result.matched


def test_no_match_same_ticker_with_different_name() -> None:
    """Equal ticker alone must not be sufficient when names differ."""

    left = provider_record(
        name="Apple Inc.",
        ticker="AAPL",
    )
    right = provider_record(
        name="Microsoft Corporation",
        ticker="AAPL",
    )

    result = SecurityMatcher().match(left, right)

    assert not result.matched


@pytest.mark.parametrize(
    ("left_ticker", "left_isin", "right_ticker", "right_isin"),
    [
        (None, "US0378331005", "AAPL", "US0378331005"),
        ("AAPL", None, "AAPL", None),
        (None, None, None, None),
    ],
)
def test_missing_identifiers_do_not_match_without_name_rule(
    left_ticker: str | None,
    left_isin: str | None,
    right_ticker: str | None,
    right_isin: str | None,
) -> None:
    """Missing identifiers must not cause an accidental match."""

    left = provider_record(
        name="Apple Inc.",
        ticker=left_ticker,
        isin=left_isin,
    )
    right = provider_record(
        name="Microsoft Corporation",
        ticker=right_ticker,
        isin=right_isin,
    )

    result = SecurityMatcher().match(left, right)

    assert not result.matched
