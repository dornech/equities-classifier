"""Abstract base classes for security identifier resolvers."""

from typing import Any

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, field
from collections.abc import Sequence

from equities_classifier.models import Security, SecurityIdentifier


class SecurityIdentifierResolver(ABC):
    """Base class for SecurityIdentifierResolver classes."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the resolver name."""

    def __enter__(self) -> "SecurityIdentifierResolver":
        """Enter the runtime context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context."""
        self.close()

    def close(self) -> None:
        """Release allocated resources."""

    @abstractmethod
    def resolve(
        self,
        identifiers: Sequence[SecurityIdentifier]
    ) -> list[Security]:
        """Resolve security identifiers into canonical securities."""


@dataclass(slots=True)
class SecurityIdentifierResolverRecord(ABC):
    """Base class for SecurityIdentifierResolverRecord classes ensuring common fields are contained."""

    identifiers: list[SecurityIdentifier] = field(default_factory=list)

    def provider_attributes(self) -> dict[str, Any]:
        """Return all provider-specific attributes."""

        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name != "identifiers" and getattr(self, field.name) is not None
        }
