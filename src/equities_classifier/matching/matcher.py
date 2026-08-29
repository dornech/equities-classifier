"""match SecurityProviderRecords."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: PLR0916, RUF105, TID252
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, no-any-return"

# fmt: off


from typing import TypeAlias

from enum import Enum
from dataclasses import dataclass

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityProviderRecord, Security

from .name import name_similarity


class MatchType(Enum):
    """Security matching result."""

    ISIN_TICKER = "isin_ticker"
    ISIN_TICKER_US = "isin_ticker_us"
    ISIN_NAME = "isin_name"
    TICKER_COUNTRY_NAME = "ticker_country_name"
    TICKER_NAME = "ticker_name"
    TICKER_US_NAME = "ticker_us_name"


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Result of comparing two provider records."""

    matched: bool
    match_type: MatchType | None = None
    warning: str | None = None
    name_similarity: float | None = None


SecurityMatchSource: TypeAlias = SecurityProviderRecord | Security


class SecurityMatcher:
    """Match provider records representing the same security."""

    def __init__(self, *, name_similarity_threshold: float = 85.0) -> None:
        """Initialize SecurityMatcher."""

        self._name_similarity_threshold = name_similarity_threshold

    def match(
        self,
        left: SecurityMatchSource,
        right: SecurityProviderRecord,
    ) -> MatchResult:
        """Match SecurityProviderRecords according to matching hierarchy."""

        left_ticker = left.identifier_value(SecurityIdentifierType.TICKER)
        left_ticker_cleaned = left.identifier_value_cleaned(SecurityIdentifierType.TICKER)
        left_ticker_country = left.identifier_country(SecurityIdentifierType.TICKER)
        right_ticker = right.identifier_value(SecurityIdentifierType.TICKER)
        right_ticker_cleaned = right.identifier_value_cleaned(SecurityIdentifierType.TICKER)
        right_ticker_country = right.identifier_country(SecurityIdentifierType.TICKER)

        left_ticker_us = left.identifier_value(SecurityIdentifierType.TICKER_US)
        right_ticker_us = right.identifier_value(SecurityIdentifierType.TICKER_US)

        left_isin = left.identifier_value(SecurityIdentifierType.ISIN)
        right_isin = right.identifier_value(SecurityIdentifierType.ISIN)

        # 1a. Ticker + ISIN
        if (
            left_ticker_cleaned
            and right_ticker_cleaned
            and left_isin
            and right_isin
            and left_ticker_cleaned == right_ticker_cleaned
            and left_isin == right_isin
        ):
            return MatchResult(matched=True, match_type=MatchType.ISIN_TICKER)

        # 1b. Ticker-US + ISIN
        if (
            left_ticker_us
            and right_ticker_us
            and left_isin
            and right_isin
            and left_ticker_us == right_ticker_us
            and left_isin == right_isin
        ):
            return MatchResult(matched=True, match_type=MatchType.ISIN_TICKER_US)

        # 2. ISIN + similar name
        if (
            left_isin
            and right_isin
            and left_isin == right_isin
            and left_ticker_cleaned != right_ticker_cleaned
        ):
            similarity = name_similarity(left.name, right.name)

            if similarity >= self._name_similarity_threshold:
                return MatchResult(
                    matched=True,
                    match_type=MatchType.ISIN_NAME,
                    warning=(f"ISIN matches but ticker differs: {left_ticker!r} != {right_ticker!r}"),
                    name_similarity=similarity,
                )

        # 3. Ticker incl. country postfix + similar name
        if (
            not (left_isin and right_isin)
            and left_ticker
            and left_ticker_country
            and right_ticker
            and right_ticker_country
            and left_ticker == right_ticker
        ):

            similarity = name_similarity(left.name, right.name)

            if similarity >= self._name_similarity_threshold:
                return MatchResult(
                    matched=True,
                    match_type=MatchType.TICKER_COUNTRY_NAME,
                    name_similarity=similarity,
                )

        # 4. Ticker + similar name
        if (
            not (left_isin and right_isin)
            and left_ticker_cleaned
            and right_ticker_cleaned
            and left_ticker_cleaned == right_ticker_cleaned
        ):
            similarity = name_similarity(left.name, right.name)

            if similarity >= self._name_similarity_threshold:
                return MatchResult(
                    matched=True,
                    match_type=MatchType.TICKER_NAME,
                    name_similarity=similarity,
                )

        # 5. Ticker-US + similar name
        if (
            not (left_isin and right_isin)
            and left_ticker_us
            and right_ticker_us
            and left_ticker_us == right_ticker_us
        ):
            similarity = name_similarity(left.name, right.name)

            if similarity >= self._name_similarity_threshold:
                return MatchResult(
                    matched=True,
                    match_type=MatchType.TICKER_US_NAME,
                    name_similarity=similarity,
                )

        return MatchResult(matched=False)
