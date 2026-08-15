"""Mathing helper."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "operator"


# fmt: off


from equities_classifier.exceptions import MatchingError


class MatchingHelper:
    """Helper methods for matching."""

    @staticmethod
    def other_error_with_message(
        message: str,
        raise_object: type[MatchingError] | None = None
    ) -> None:
        """Called when the provider is called with invalid security type."""

        if raise_object:
            raise raise_object(message)
