from abc import ABC, abstractmethod
from collections.abc import Sequence
from equity_classifier.models import (
    SecurityIdentifier,
    SecurityClassification
)


class ClassificationProvider(ABC):

    def __enter__(self): return self

    def __exit__(self, *_): self.close()

    def close(self) -> None: ...

    @abstractmethod
    def classify(self, securityIDs: Sequence[SecurityIdentifier]) -> list[SecurityClassification]: ...
