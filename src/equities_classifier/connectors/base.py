"""Abstract base classes for security classification"""


from abc import ABC, abstractmethod
from collections.abc import Sequence
from equities_classifier.models import (
    ClassificationSystem,
    SecurityIdentifier,
    Security,
    SecurityClassification
)


# remainder from first approach
class ClassificationProvider(ABC):

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None: ...

    @abstractmethod
    def classify(self, securityIDs: Sequence[SecurityIdentifier]) -> list[SecurityClassification]:
        """Classify a sequence of securities."""


class ClassificationConnector(ABC):
    """Base class for classification connectors."""

    def __init__(self, classification_system: ClassificationSystem) -> None:
        if classification_system is None:
            msg = "classification_system must not be None"
            raise ValueError(msg)
        self._classification_system = classification_system

    @property
    def classification_system(self) -> ClassificationSystem:
        """Return the configured classification system."""
        return self._classification_system

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the connector name."""
        return self._classification_system.display_name

    def __enter__(self) -> "ClassificationConnector":
        """Enter the runtime context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context."""
        self.close()

    def close(self) -> None:
        """Release allocated resources."""
        pass

    @abstractmethod
    def classify(self, securities: Sequence[Security]) -> list[SecurityClassification]:
        """Classify a sequence of securities."""
