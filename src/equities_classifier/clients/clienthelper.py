"""client helper for all clients."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "operator"

# fmt: off


from typing import Any

from equities_classifier.enums import (
    DataSourceID,
    SecurityIdentifierType
)
from equities_classifier.exceptions import ClientResponseError


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
    def search_result_counter_issue(
        provider: DataSourceID,
        security_type: SecurityIdentifierType,
        security_identifier: str,
        count_provider: int,
        count_found: int,
    ) -> None:
        """Called when the provider delivers inconsistent number od data."""
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
        """Called when the provider returns unmapped JSON attributes."""
        pass

    @staticmethod
    def missing_record_attribute(
        provider: DataSourceID,
        attribute: str,
        value: Any
    ) -> None:
        """Called when the mapping points to a record attribute that does not exist."""
        pass

    @staticmethod
    def other_error_with_message(
        provider: DataSourceID,
        message: str,
        raise_object: type[ClientResponseError] | None = None
    ) -> None:
        """Called when the provider is called with invalid security type."""

        if raise_object:
            raise raise_object(message)
