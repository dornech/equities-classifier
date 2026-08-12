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

    def merge(
        self,
        left: Sequence[SecurityProviderRecord],
        right: Sequence[SecurityProviderRecord],
        *,
        join_type: JoinType = JoinType.LEFT,
    ) -> list[Security]:
        """Merge SecurityProviderRecords depending on matching result."""

        result: list[Security] = []

        for left_record in left:

            matches = [
                record
                for record in right
                if self._matcher.match(left_record, record)
            ]

            if not matches:
                if join_type is JoinType.LEFT:
                    result.append(self._create_security(left_record))
                continue

            if len(matches) > 1:
                MatchingHelper.other_error_with_message(
                    f"Multiple matching provider records for "
                    f"{left_record.name!r} / {left_record.ticker!r}."
                )

            result.append(self._create_from_merge_providerrecords(left_record, matches[0],)
            )

        return result

    @staticmethod
    def _create_security(
        provider_record: SecurityProviderRecord,
    ) -> Security:
        """Create a Security from a SecurityProviderRecord."""

        security = Security(
            name=provider_record.name,
            ticker=provider_record.ticker,
        )
        security.identifiers.extend(provider_record.identifiers)
        security.provider_attributes[provider_record.datasource] = provider_record.provider_attributes()

        return security

    def _create_from_merge_providerrecords(
        self,
        left: SecurityProviderRecord ,
        right: SecurityProviderRecord,
    ) -> Security:
        """Create a Security from a SecurityProviderRecord and merge 2nd SecurityProviderRecord."""

        security = self._create_security(left)

        self._merge_identifiers(security, right)
        self._merge_provider_attributes(security, right)

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
