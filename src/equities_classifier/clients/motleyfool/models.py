"""Internal data models for Motley-Fool."""


# ruff and mypy per file settings
#

# fmt: off


from dataclasses import dataclass

from equities_classifier.models import SecurityProviderRecord


@dataclass(slots=True)
class MotleyFoolSearchResult:
    """Internal representation of a Motley-Fool search result."""

    name: str | None = None
    ticker: str | None = None
    exchange: str | None = None
    home_country_code: str | None = None


@dataclass(slots=True)
class MotleyFoolRecord(SecurityProviderRecord):
    """Internal representation of a single Motley-Fool mapping result."""

    name: str | None = None
    ticker: str | None = None
    exchange: str | None = None
    home_country_code: str | None = None

    sector: str | None = None
    industry: str | None = None
