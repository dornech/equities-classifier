"""client helper for all clients."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: E501, RUF105
# disable mypy errors
# mypy: disable-error-code = "operator"

# fmt: off


from typing import Any

from equities_classifier.enums import DataSourceID
from equities_classifier.models import SecurityIdentifier
from equities_classifier.exceptions import ClientResponseError
from equities_classifier.logginghelper import logger_equities_classifier


class ClientHelper:
    """Helper methods for client processing."""

    @staticmethod
    def invalid_security_type(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
    ) -> None:
        """Called when the provider is called with invalid security type."""

        logger_equities_classifier.warning(f"Identifier type '{identifier.type}' invalid or invalid for source '{provider}' (value was '{identifier.value}'.")

    @staticmethod
    def search_result_counter_issue(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        count_provider: int,
        count_found: int,
    ) -> None:
        """Called when the provider delivers inconsistent number of data records."""

        logger_equities_classifier.warning(f"Search result from source '{provider}' for ({identifier.type}, {identifier.value}) contains inconsistent counter value, expected {count_provider} vs {count_found} found.")

    @staticmethod
    def search_result_not_unique(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
    ) -> None:
        """Called when the provider cannot find unique dataset."""

        logger_equities_classifier.warning(f"Search result from source '{provider}' for ({identifier.type}, {identifier.value}) is not unique. Processing first match.")

    @staticmethod
    def unknown_provider_attribute(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        attribute: str,
        value: str,
        context: str,
    ) -> None:
        """Called when the provider returns an unmapped JSON attribute."""

        logger_equities_classifier.warning(f"Provider attribute {attribute}, value '{value}' from source '{provider}' for ({identifier.type}, {identifier.value}) not mapped in '{context}'.")

    @staticmethod
    def unknown_provider_attributes(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        attributes: set[tuple[str, ...]],
        context: str,
    ) -> None:
        """Called when the provider returns unmapped JSON attributes."""

        logger_equities_classifier.warning(f"Provider attributes {attributes} from source '{provider}' for ({identifier.type}, {identifier.value}) not mapped in '{context}'.")

    @staticmethod
    def missing_provider_attribute(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        attribute: str,
    ) -> None:
        """Called when the provider returns an unmapped JSON attribute."""

        logger_equities_classifier.warning(f"Missing provider attribute '{attribute}' from source '{provider}' for ({identifier.type}, {identifier.value}).")

    @staticmethod
    def missing_record_attribute(
        provider: DataSourceID,
        attribute: str,
        value: Any,
        context: str,
    ) -> None:
        """Called when the mapping points to a record attribute that does not exist."""

        logger_equities_classifier.warning(f"Unknown/not handled provider attribute '{attribute}' with value '{value}' in response from '{provider}',  not mapped in '{context}'.")

    @staticmethod
    def other_error_with_message(
        provider: DataSourceID,
        message: str,
        raise_object: type[ClientResponseError] | None = None
    ) -> None:
        """Called when the provider is called with invalid security type."""

        logger_equities_classifier.error(message)

        if raise_object:
            raise raise_object(message)
