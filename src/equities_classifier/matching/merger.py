"""merge set of SecurityProviderRecords."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: RUF105, TID252

# fmt: off


from enum import Enum
from collections.abc import Sequence

from equities_classifier.models import (
    Security,
    SecurityProviderRecord,
)

from .matcher import SecurityMatcher
from .matchinghelper import MatchingHelper


class JoinType(Enum):
    """Security provider record join type."""

    INNER = "inner"
    LEFT = "left"


class SecurityMerger:
    """Merge SecurityProviderRecords into Security objects."""

    def __init__(
        self,
        matcher: SecurityMatcher | None = None,
    ) -> None:
        """Initialize SecurityMerger object."""

        self._matcher = matcher or SecurityMatcher()

    def create_securities(
        self,
        provider_records: Sequence[SecurityProviderRecord],
    ) -> list[Security]:
        """Create Security objects from provider records."""

        return [
            self._create_security(provider_record)
            for provider_record in provider_records
        ]

    def merge_enrich_single(
        self,
        security: Security,
        right: Sequence[SecurityProviderRecord],
        *,
        join_type: JoinType = JoinType.LEFT,
    ) -> Security:
        """Merge provider records into existing Security record."""

        matches = [
            provider_record
            for provider_record in right
            if self._matcher.match(security, provider_record,)
        ]

        if len(matches) > 1:
            MatchingHelper.other_error_with_message(
                f"Multiple matching provider records for "
                f"{security.name!r} / {security.ticker!r}."
            )

        provider_record = matches[0]

        self._merge_identifiers(security, provider_record,)
        self._merge_provider_attributes(security, provider_record,)

        return security

    def merge_enrich_multiple(
        self,
        left: Sequence[Security],
        right: Sequence[SecurityProviderRecord],
        *,
        join_type: JoinType = JoinType.LEFT,
    ) -> list[Security]:
        """Merge provider records into existing Security objects."""

        for security in left:
            security = self.merge_enrich_single(security, right)

        return list(left)

    @staticmethod
    def _create_security(
        provider_record: SecurityProviderRecord,
    ) -> Security:
        """Create a Security from a SecurityProviderRecord."""

        security = Security(name=provider_record.name, ticker=provider_record.ticker,)
        security.identifiers = provider_record.identifiers
        security.provider_attributes[provider_record.datasource] = provider_record.provider_attributes()

        return security

    @staticmethod
    def _merge_identifiers(
        security: Security,
        provider_record: SecurityProviderRecord,
    ) -> None:
        """Merge identifiers from a SecurityProviderRecord into a Security."""

        for identifier in provider_record.identifiers:
            if security.identifier(identifier.type) is None:
                security.identifiers.append(identifier)

    @staticmethod
    def _merge_provider_attributes(
        security: Security,
        provider_record: SecurityProviderRecord,
    ) -> None:
        """Merge SecurityProviderRecord into a Security."""

        if not security.provider_attributes[provider_record.datasource]:
            security.provider_attributes[provider_record.datasource] = provider_record.provider_attributes()
        else:
            MatchingHelper.other_error_with_message(
                f"Provider attributes for {provider_record.datasource} already exist."
            )
