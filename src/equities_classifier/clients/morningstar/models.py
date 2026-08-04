"""Internal data models for Morningstar."""


from dataclasses import dataclass, field

from equities_classifier.models import SecurityIdentifier, SecurityProviderRecord


@dataclass(slots=True)
class MorningstarSearchResult:
    """Internal representation of a Morningstar search result."""

    source_identifier: SecurityIdentifier

    name: str | None = None
    short_name: str | None = None

    ticker: str | None = None
    isin: str | None = None

    company_id: str | None = None
    security_id: str | None = None
    performance_id: str | None = None

    universe: str | None = None

    exchange: str | None = None
    exchange_name: str | None = None
    exchange_country: str | None = None
    exchange_country_name: str | None = None


@dataclass(slots=True)
class MorningstarRecord(SecurityProviderRecord):
    """Internal representation of a Morningstar search result and classification record."""

    name: str | None = None
    ticker: str | None = None
    company_id: str | None = None

    universe: str | None = None

    sector: str | None = None
    industry: str | None = None

    security_id: list[str] = field(default_factory=list)
    performance_id: list[str] = field(default_factory=list)
    ticker_exchange: list[str] = field(default_factory=list)
    exchange: list[str] = field(default_factory=list)
    exchange_name: list[str] = field(default_factory=list)
    exchange_country: list[str] = field(default_factory=list)
    exchange_country_name: list[str] = field(default_factory=list)
