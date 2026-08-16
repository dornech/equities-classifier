"""Classification helper."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: E501, RUF105
# disable mypy errors
# mypy: disable-error-code = "operator"

# fmt: off


from equities_classifier.enums import (
    DataSourceID,
    ClassificationSystemID,
    ClassificationLevel,
)
from equities_classifier.exceptions import ClassificationError
from equities_classifier.logginghelper import logger_equities_classifier


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

        logger_equities_classifier.warning(
            f"Invalid value '{supplied}' by source {datasource}' for level {level} of classification system '{system}'."
        )

    @staticmethod
    def classification_mismatch(
        datasource: DataSourceID,
        system: ClassificationSystemID,
        level: ClassificationLevel,
        supplied: str,
        resolved: str,
    ) -> None:
        """Handle a classification mismatch."""

        logger_equities_classifier.warning(
            f"Mismatch of value '{supplied}' by source {datasource}' for level {level} of classification system '{system}', expected '{resolved}'."
        )

    @staticmethod
    def other_error_with_message(
        message: str,
        raise_object: type[ClassificationError] | None = None
    ) -> None:
        """Called when the provider is called with invalid security type."""

        if raise_object:
            logger_equities_classifier.error(message)
            raise raise_object(message)
        else:
            logger_equities_classifier.warning(message)
