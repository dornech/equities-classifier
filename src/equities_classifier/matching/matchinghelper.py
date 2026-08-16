"""Mathing helper."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "operator"


# fmt: off


from equities_classifier.exceptions import MatchingError
from equities_classifier.logginghelper import logger_equities_classifier


class MatchingHelper:
    """Helper methods for matching."""

    @staticmethod
    def other_error_with_message(
        message: str,
        raise_object: type[MatchingError] | None = None
    ) -> None:
        """Called when the provider is called with invalid security type."""

        logger_equities_classifier.error(message)

        if raise_object:
            raise raise_object(message)
