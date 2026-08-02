"""Internal data models for Morningstar."""


from dataclasses import dataclass, field

from equities_classifier.models import SecurityIdentifier


@dataclass(slots=True)
class MorningstarSearchResult:
    """Internal representation of a Morningstar search result."""

    identifier: SecurityIdentifier

    url: str
    company_name: str
    instrument_type: str
    exchange: str
    country: str
    ticker: str
    currency: str


@dataclass(slots=True)
class MorningstarRecord:
    """Internal representation of a Morningstar classification."""

    identifier: SecurityIdentifier

    company_name: str = ""
    sector: str | None = None
    industry: str | None = None

    provider_attributes: dict[str, str] = field(default_factory=dict)
