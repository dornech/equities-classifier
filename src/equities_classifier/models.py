"""Business domain model for equities_classifier."""


from typing import Any

from dataclasses import dataclass, fields, field

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
    # name str
    value: str
    code: str | None = None


@dataclass(frozen=True, slots=True)
class SecurityIdentifier:
    """Security identifier."""

    type: SecurityIdentifierType
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", self.value.strip())


@dataclass(slots=True, kw_only=True)
class SecurityIdentifierIdentifiable:
    """Base class for objects identified by security identifiers."""

    identifiers: list[SecurityIdentifier] = field(default_factory=list)

    def identifier(
        self,
        identifier_type: SecurityIdentifierType,
    ) -> SecurityIdentifier | None:
        return next(
            (
                identifier
                for identifier in self.identifiers
                if identifier.type is identifier_type
            ),
            None,
        )

    def identifier_value(
        self,
        identifier_type: SecurityIdentifierType,
    ) -> str | None:

        if self.has_identifier(identifier_type):
            return self.identifier(identifier_type).value
        else:
            return None

    def has_identifier(
        self,
        identifier_type: SecurityIdentifierType,
    ) -> bool:
        return self.identifier(identifier_type) is not None


@dataclass(slots=True)
class SecurityProviderRecord(SecurityIdentifierIdentifiable):
    """Base class for SecurityProviderRecord classes ensuring common fields are contained."""

    def provider_attributes(self) -> dict[str, Any]:
        """Return all provider-specific attributes."""

        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name != "identifiers" and getattr(self, field.name) is not None
        }


@dataclass(slots=True)
class Security(SecurityIdentifierIdentifiable):
    """Security class."""

    name: str | None = None
    ticker: str | None = None
    provider_attributes: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SecurityClassification:
    """Classification of one company."""

    security: Security
    # company: str
    system: ClassificationSystem
    nodes: tuple[ClassificationNode, ...]
