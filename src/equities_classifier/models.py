from dataclasses import dataclass
from equities_classifier.enums import ClassificationLevel, ClassificationSystemID, SecurityIdentifierType


@dataclass(frozen=True, slots=True)
class ClassificationSystem:
    """Definition of a classification system."""

    id: ClassificationSystemID
    display_name: str
    authorities: tuple[str, ...]
    hierarchy: tuple[str, ...]
    supports_codes: bool


@dataclass(slots=True, frozen=True)
class ClassificationNode:
    """Single hierarchy node."""

    level: ClassificationLevel
    name: str
    code: str | None = None


@dataclass(slots=True, frozen=True)
@dataclass(frozen=True, slots=True)
class SecurityIdentifier:
    """Security identifier."""

    type: SecurityIdentifierType
    value: str


@dataclass(slots=True, frozen=True)
class SecurityClassification:
    """Classification of one company."""

    securityID: SecurityIdentifier
    company: str
    system: ClassificationSystem
    nodes: tuple[ClassificationNode, ...]
