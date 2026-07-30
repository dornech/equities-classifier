from dataclasses import dataclass
from equities_classifier.enums import (
    ClassificationSystemID,
    ClassificationLevel,
    SecurityIdentifierType
)


@dataclass(frozen=True, slots=True)
class ClassificationSystem:
    """Definition of a classification system."""

    id: ClassificationSystemID
    display_name: str
    authorities: tuple[str, ...]
    hierarchy: tuple[str, ...]
    supports_codes: bool


@dataclass(frozen=True, slots=True)
class ClassificationNode:
    """Single hierarchy node."""

    level: ClassificationLevel
    name: str
    code: str | None = None


@dataclass(frozen=True, slots=True)
class SecurityIdentifier:
    """Security identifier."""

    type: SecurityIdentifierType
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True, slots=True)
class Security:
    figi: str
    company_name: str
    identifiers: tuple[SecurityIdentifier, ...]

    def identifier(self, identifier_type: SecurityIdentifierType,) -> SecurityIdentifier | None:
        """Return the first identifier of the requested type."""

        return next(
            (identifier for identifier in self.identifiers if identifier.type is identifier_type),
            None,
        )

    def identifier_value(self, identifier_type: SecurityIdentifierType,) -> str | None:
        """Return the value of the requested identifier type."""

        identifier = self.identifier(identifier_type)
        return None if identifier is None else identifier.value

    def has_identifier(self, identifier_type: SecurityIdentifierType,) -> bool:
        """Return whether an identifier of the requested type exists."""

        return self.identifier(identifier_type) is not None


@dataclass(frozen=True, slots=True)
class SecurityClassification:
    """Classification of one company."""

    security: Security
    # company: str
    system: ClassificationSystem
    nodes: tuple[ClassificationNode, ...]
