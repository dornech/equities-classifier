"""Classification helper."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "operator"


# fmt: off


from equities_classifier.enums import (
    DataSourceID,
    ClassificationSystemID,
    ClassificationLevel,
)
from equities_classifier.exceptions import ClassificationError


class ClassificationHelper:
    """Helper methods for classification processing."""

    @staticmethod
    def classification_element_invalid(
        datasource: DataSourceID,
        system: ClassificationSystemID,
        level: ClassificationLevel,
        supplied: str,
    ) -> None:
        """Handle a classification mismatch."""
        pass

    @staticmethod
    def classification_mismatch(
        datasource: DataSourceID,
        system: ClassificationSystemID,
        level: ClassificationLevel,
        supplied: str,
        resolved: str,
    ) -> None:
        """Handle a classification mismatch."""
        pass

    @staticmethod
    def other_error_with_message(
        message: str,
        raise_object: type[ClassificationError] | None = None
    ) -> None:
        """Called when the provider is called with invalid security type."""

        if raise_object:
            raise raise_object(message)
