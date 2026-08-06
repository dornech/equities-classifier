"""client helper for all clients."""


# ruff and mypy per file settings
#

# fmt: off


from typing import Any

from equities_classifier.enums import (
    DataSourceID,
    SecurityIdentifierType
)


class ClientHelper:

    @staticmethod
    def invalid_security_type(
        provider: DataSourceID,
        security_type: SecurityIdentifierType,
        security_identifier: str,
    ) -> None:
        """Called when the provider is called with invalid security type."""
        pass

    @staticmethod
    def search_result_not_unique(
        provider: DataSourceID,
        security_type: SecurityIdentifierType,
        security_identifier: str,
    ) -> None:
        """Called when the provider cannot find unique dataset."""
        pass

    @staticmethod
    def unknown_provider_attribute(
        provider: DataSourceID,
        attribute: str,
        value: Any
    ) -> None:
        """Called when the provider returns an unmapped JSON attribute."""
        pass

    @staticmethod
    def unknown_provider_attributes(
        provider: DataSourceID,
        attributes: set[tuple[str, ...]],
        context: str | None = None
    ) -> None:
        """Called when the provider returns an unmapped JSON attribute."""
        pass

    @staticmethod
    def missing_record_attribute(
        provider: DataSourceID,
        attribute: str,
        value: Any
    ) -> None:
        """Called when the mapping points to a record attribute that does not exist."""
        pass
