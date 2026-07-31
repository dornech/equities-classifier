"""Common exceptions used by equities-classifier."""


class EquitiesClassifierError(Exception):
    """Base class for all library exceptions."""


# Resolver related exceptions

class ResolverError(EquitiesClassifierError):
    """Base class for identifier resolver errors."""

class IdentifierNotFoundError(ResolverError):
    """No matching security could be resolved."""

class AmbiguousIdentifierError(ResolverError):
    """The identifier resolves to multiple securities."""


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


# Connector related exceptions


class ConnectorError(EquitiesClassifierError):
    """Base class for classification connector errors."""

class ClassificationNotAvailableError(ConnectorError):
    """The requested classification is not available."""
