"""Internal data models for Seeking Alpha."""


# ruff and mypy per file settings
#

# fmt: off


from typing import ClassVar
from dataclasses import dataclass

from equities_classifier.enums import DataSourceID
from equities_classifier.models import SecurityProviderRecord


@dataclass(slots=True, kw_only=True)
class SeekingAlphaRecord(SecurityProviderRecord):
    """Seeking Alpha security and GICS classification record."""

    # identifiers, identifier inherited form SecurityIdentifierIdentifiable via SecurityProviderRecord
    # name, ticker inherited from SecurityProviderRecord !

    datasource: ClassVar[DataSourceID] = DataSourceID.SEEKINGALPHA

    ticker_us: str | None = None

    exchange: str | None = None

    sector: str | None = None
    sector_code: str | None = None
    subindustry: str | None = None
    subindustry_code: str | None = None
