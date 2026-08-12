"""Common exceptions used by equities-classifier."""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E302
# others
# ruff: noqa: RUF105


# fmt: off


class EquitiesClassifierError(Exception):
    """Base class for all library exceptions."""


# Provider / HTTP related exceptions

class ClientError(EquitiesClassifierError):
    """Base class for all client errors."""


class ClientAuthenticationError(ClientError):
    """Authentication with the provider failed."""


class ClientConnectionError(ClientError):
    """The remote service could not be reached."""


class ClientResponseError(ClientError):
    """The remote service returned an invalid response."""


class ClientRateLimitError(ClientError):
    """The provider rate limit has been exceeded."""


# Matching error


class MatchingError(EquitiesClassifierError):
    """Base class for all library exceptions."""
