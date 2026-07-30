"""Abstract base classes for security identifier resolvers."""


from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from equities_classifier.models import Security, SecurityIdentifier


class SecurityIdentifierResolver(ABC):
    """Base class for Securityidentifier resolvers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the resolver name."""

    def __enter__(self) -> SecurityIdentifierResolver:
        """Enter the runtime context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context."""
        self.close()

    def close(self) -> None:
        """Release allocated resources."""

    @abstractmethod
    def resolve(self, securityidentifiers: Sequence[SecurityIdentifier]) -> list[Security]:
        """Resolve security identifiers into canonical securities."""
