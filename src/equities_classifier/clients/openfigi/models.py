"""Internal data models for the OpenFIGI REST API."""


from typing import Any

from dataclasses import dataclass, fields, field

from equities_classifier.models import SecurityIdentifier
from equities_classifier.resolvers.base import SecurityIdentifierResolverRecord


@dataclass(slots=True, kw_only=True)
class OpenFIGIRecord(SecurityIdentifierResolverRecord):
    """Internal representation of a single OpenFIGI mapping result."""

    company_name: str | None = None
    ticker: str | None = None

    figi: str | None = None
    composite_figi: str | None = None
    share_class_figi: str | None = None

    security_description: str | None = None
    security_type: str | None = None
    security_type2: str | None = None
    market_sector: str | None = None

    exch_code: str | None = None
    mic_code: str | None = None
    currency: str | None = None
    state_code: str | None = None

    # potentially to be deleted if derivation from SecurityIdentifierResolverRecord works
    # identifiers: list[SecurityIdentifier] = field(default_factory=list)
    #
    # def provider_attributes2(self) -> dict[str, Any]:
    #     """Return all provider-specific attributes."""
    #
    #     return {
    #         field.name: getattr(self, field.name)
    #         for field in fields(self)
    #         if field.name != "identifiers" and getattr(self, field.name) is not None
    #     }
