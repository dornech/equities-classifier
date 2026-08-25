"""Internal data models for Yahoo Finance."""


# ruff and mypy per file settings
#
# fmt: off


from typing import ClassVar
from dataclasses import dataclass

from equities_classifier.enums import DataSourceID
from equities_classifier.models import SecurityProviderRecord


@dataclass(slots=True)
class YahooSearchResult:
    """Internal representation of a Yahoo Finance search result."""

    shortname: str | None = None
    longname: str | None = None
    symbol: str | None = None
    index: str | None = None
    quote_type: str | None = None
    type_disp: str | None = None
    exchange: str | None = None
    exch_disp: str | None = None
    sector: str | None = None
    sector_disp: str | None = None
    industry: str | None = None
    industry_disp: str | None = None
    score: float | None = None


@dataclass(slots=True)
class YahooRecord(SecurityProviderRecord):
    """Internal representation of a Yahoo Finance classification record."""

    # identifiers, identifier inherited form SecurityIdentifierIdentifiable via SecurityProviderRecord
    # name, ticker inherited from SecurityProviderRecord !

    datasource: ClassVar[DataSourceID] = DataSourceID.YAHOO

    ticker_yahoo: str | None = None

    exchange: str | None = None
    exch_disp: str | None = None

    sector: str | None = None
    industry: str | None = None
