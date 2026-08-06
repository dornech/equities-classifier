"""Internal data models for the OpenFIGI REST API."""


# ruff and mypy per file settings
#

# fmt: off


from dataclasses import dataclass, field

from equities_classifier.models import SecurityProviderRecord


@dataclass(slots=True, kw_only=True)
class OpenFIGIRecord(SecurityProviderRecord):
    """Internal representation of a single OpenFIGI mapping result."""

    name: str | None = None
    ticker: str | None = None

    figi: list[str] = field(default_factory=list)
    composite_figi: list[str] = field(default_factory=list)
    share_class_figi: str | None = None

    security_description: str | None = None
    security_type: str | None = None
    security_type2: str | None = None
    market_sector: str | None = None

    exch_code: list[str] = field(default_factory=list)
    mic_code: list[str] = field(default_factory=list)
    currency: str | None = None
    state_code: str | None = None
