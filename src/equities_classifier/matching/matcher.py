"""match SecurityProviderRecords."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: PLR0916, RUF105, TID252
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, no-any-return"

# fmt: off


from enum import Enum
from dataclasses import dataclass

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import SecurityProviderRecord

from .name import name_similarity


class MatchType(Enum):
    """Security matching result."""

    TICKER_AND_ISIN = "ticker_and_isin"
    ISIN_NAME = "isin_name"
    TICKER_NAME = "ticker_name"


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Result of comparing two provider records."""

    matched: bool
    match_type: MatchType | None = None
    warning: str | None = None
    name_similarity: float | None = None


class SecurityMatcher:
    """Match provider records representing the same security."""

    def __init__(self, *, name_similarity_threshold: float = 85.0,) -> None:
        """Initialize SecurityMatcher."""

        self._name_similarity_threshold = name_similarity_threshold

    def match(
        self,
        left: SecurityProviderRecord,
        right: SecurityProviderRecord,
    ) -> MatchResult:
        """Match SecurityProviderRecords according to matching hierarchy."""

        left_ticker = left.identifier_value(SecurityIdentifierType.TICKER,)
        right_ticker = right.identifier_value(SecurityIdentifierType.TICKER,)

        left_isin = left.identifier_value(SecurityIdentifierType.ISIN,)
        right_isin = right.identifier_value(SecurityIdentifierType.ISIN,)

        # 1. Ticker + ISIN
        if (
            left_ticker
            and right_ticker
            and left_isin
            and right_isin
            and left_ticker == right_ticker
            and left_isin == right_isin
        ):
            return MatchResult(matched=True, match_type=MatchType.TICKER_AND_ISIN,)

        # 2. ISIN + similar name
        if (
            left_isin
            and right_isin
            and left_isin == right_isin
            and left_ticker != right_ticker
        ):
            similarity = name_similarity(left.name, right.name)

            if similarity >= self._name_similarity_threshold:
                return MatchResult(
                    matched=True,
                    match_type=MatchType.ISIN_NAME,
                    warning=(f"ISIN matches but ticker differs: {left_ticker!r} != {right_ticker!r}"),
                    name_similarity=similarity,
                )

        # 3. Ticker + similar name
        if (
            left_ticker
            and right_ticker
            and left_ticker == right_ticker
        ):
            similarity = name_similarity(left.name, right.name)

            if similarity >= self._name_similarity_threshold:
                return MatchResult(
                    matched=True,
                    match_type=MatchType.TICKER_NAME,
                    name_similarity=similarity,
                )

        return MatchResult(matched=False)
