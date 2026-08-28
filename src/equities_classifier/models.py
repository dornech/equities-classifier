"""Business domain model for equities_classifier."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "no-any-return, attr-defined, unused-ignore"

# fmt: off


from typing import Any, ClassVar, SupportsIndex, overload
from collections.abc import Iterable
from dataclasses import dataclass, fields, field

from equities_classifier.enums import DataSourceID, ClassificationSystemID, ClassificationLevel, SecurityIdentifierType


# classes regarding security classification


@dataclass(frozen=True, slots=True)
class ClassificationSystem:
    """Definition of a classification system."""

    id: ClassificationSystemID
    display_name: str
    short_name: str
    authorities: tuple[str, ...]
    hierarchy: tuple[str, ...]
    supports_codes: bool


@dataclass(frozen=True, slots=True)
class ClassificationNode:
    """Single hierarchy node."""

    value: str
    code: str | None = None


@dataclass(frozen=True, slots=True)
class SecurityClassification:
    """Classification of a security."""

    system: ClassificationSystem
    nodes: dict[ClassificationLevel, ClassificationNode]


# classes regarding securities themselves


@dataclass(frozen=True, slots=True)
class SecurityIdentifier:
    """Security identifier."""

    type: SecurityIdentifierType
    value: str
    value_cleaned: str | None = field(init=False)
    country: str | None = field(init=False)

    def __post_init__(self) -> None:
        """Strip identifier value and for Ticker split into value_cleaned and country provided as postfix.
         NOTE: derived attributes where not marked with a leading _ to allow transparent access as for
         original value.
         """

        # strip value
        object.__setattr__(self, "value", self.value.strip())

        # allow country suffix for ticker
        if self.type != SecurityIdentifierType.TICKER or "." not in self.value:
            object.__setattr__(self, "value_cleaned", self.value)
            object.__setattr__(self, "country", None)
        else:
            value_cleaned, country = self.value.split(".")
            object.__setattr__(self, "value_cleaned", value_cleaned)
            object.__setattr__(self, "country", country)

    def get_value_cleaned(self):
        """Getter function for value_cleaned"""
        return self.value_cleaned

    def get_country(self):
        """Getter function for country."""
        return self.country


class SecurityIdentifierList(list[SecurityIdentifier]):
    """List of security identifiers with unique identifier types."""

    def __init__(self, iterable: Iterable[SecurityIdentifier] = ()) -> None:
        """List of security identifiers with unique identifier types."""

        super().__init__()
        self.extend(iterable)

    @staticmethod
    def _validate(identifier: SecurityIdentifier) -> None:

        if not isinstance(identifier, SecurityIdentifier):
            message = f"Expected SecurityIdentifier, got {type(identifier).__name__}"
            raise TypeError(message)

    @classmethod
    def _validate_unique(cls, identifiers: Iterable[SecurityIdentifier]) -> None:

        seen: set[SecurityIdentifierType] = set()

        for identifier in identifiers:
            cls._validate(identifier)

            if identifier.type in seen:
                message = f"An identifier of type '{identifier.type}' already exists."
                raise ValueError(message)

            seen.add(identifier.type)

    def _check_duplicate(self, identifier: SecurityIdentifier, *, exclude_index: SupportsIndex | None = None) -> None:

        excluded = (
            exclude_index.__index__()
            if exclude_index is not None
            else None
        )

        if any(
            index != excluded and existing.type is identifier.type
            for index, existing in enumerate(self)
        ):
            message = f"An identifier of type '{identifier.type}' already exists."
            raise ValueError(message)

    def append(self, identifier: SecurityIdentifier) -> None:
        """List of security identifiers with unique identifier types - append overloading."""

        self._validate(identifier)
        self._check_duplicate(identifier)

        super().append(identifier)

    def extend(self, iterable: Iterable[SecurityIdentifier]) -> None:
        """List of security identifiers with unique identifier types - extend overloading."""

        identifiers = list(iterable)

        self._validate_unique(identifiers)
        for identifier in identifiers:
            self._check_duplicate(identifier)

        super().extend(identifiers)

    def insert(self, index: SupportsIndex, identifier: SecurityIdentifier) -> None:
        """List of security identifiers with unique identifier types - insert overloading."""

        self._validate(identifier)
        self._check_duplicate(identifier)

        super().insert(index, identifier)

    def replace(self, identifier: SecurityIdentifier) -> None:
        """Replace the identifier with the same type, or append it if absent."""

        self._validate(identifier)

        for index, existing in enumerate(self):
            if existing.type is identifier.type:
                super().__setitem__(index, identifier)
                return

        super().append(identifier)

    @overload
    def __setitem__(self, index: SupportsIndex, value: SecurityIdentifier) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[SecurityIdentifier]) -> None: ...

    def __setitem__(
        self,
        index: SupportsIndex | slice,
        value: SecurityIdentifier | Iterable[SecurityIdentifier]
    ) -> None:

        if isinstance(index, slice):
            # at runtime this branch guarantees that value is iterable
            replacement = list(value)  # type: ignore[arg-type]

            for identifier in replacement:
                self._validate(identifier)

            # Validate the resulting list before modifying this list.
            result = list(self)
            result[index] = replacement
            self._validate_unique(result)

            super().__setitem__(index, replacement)
            return

        # at runtime this branch is the single-item assignment
        identifier = value  # type: ignore[assignment]
        self._validate(identifier)  # type: ignore[arg-type]
        self._check_duplicate(identifier, exclude_index=index)  # type: ignore[arg-type]

        super().__setitem__(index, identifier)  # type: ignore[arg-type]


@dataclass(slots=True, kw_only=True)
class SecurityIdentifierIdentifiable:
    """Base class for objects identified by security identifiers."""

    identifiers: SecurityIdentifierList = field(default_factory=SecurityIdentifierList)

    def identifier(
        self,
        identifier_type: SecurityIdentifierType,
    ) -> SecurityIdentifier | None:
        """Find identifier of a specific type."""

        return next(
            (
                identifier
                for identifier in self.identifiers
                if identifier.type is identifier_type
            ),
            None,
        )

    def identifier_value(self, identifier_type: SecurityIdentifierType) -> str | None:
        """Return value of an identifier of a specific type."""

        identifier = self.identifier(identifier_type)
        return identifier.value if identifier is not None else None

    def identifier_value_cleaned(self, identifier_type: SecurityIdentifierType) -> str | None:
        """Return cleaned value of an identifier of a specific type."""

        identifier = self.identifier(identifier_type)
        return identifier.value_cleaned if identifier is not None else None

    def identifier_country(self, identifier_type: SecurityIdentifierType) -> str | None:
        """Return country of an identifier of a type TICKER."""

        identifier = self.identifier(identifier_type)
        return identifier.country if identifier is not None else None

    def has_identifier(self, identifier_type: SecurityIdentifierType) -> bool:
        """Check if an identifier of a specific type is registered."""

        return self.identifier(identifier_type) is not None


@dataclass(slots=True)
class SecurityProviderRecord(SecurityIdentifierIdentifiable):
    """Base class for SecurityProviderRecord classes ensuring common fields are contained."""

    datasource: ClassVar[DataSourceID]

    name: str | None = None
    ticker: str | None = None

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

    classifications: list[SecurityClassification] = field(default_factory=list)

    def provider_attribute(self, provider: DataSourceID, attribute: str) -> Any | None:
        """Return a provider-specific attribute."""
        return self.provider_attributes.get(provider, {}).get(attribute)
