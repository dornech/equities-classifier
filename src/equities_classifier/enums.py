"""Enumerations used by business domain model of equities_classifier."""


# ruff and mypy per file settings
#

# fmt: off


from enum import IntEnum, StrEnum


class DataSourceID(StrEnum):
    """Supported data sources."""

    MORNINGSTAR = "Morningstar"
    MOTLEYFOOL = "MotleyFool"
    OPENFIGI = "OpenFIGI"
    SEEKINGALPHA = "SeekingAlpha"
    YAHOO = "Yahoo"


class SecurityIdentifierType(StrEnum):
    """Security identifier type
    possible types see f. e. https://www.openfigi.com/api/documentation#v3-id-type-values
    """

    CIK = "cik"
    CINS = "cins"
    CUSIP = "cusip"
    ISIN = "isin"
    SHARE_CLASS_FIGI = "share_class_figi"
    SEDOL = "sedol"
    TICKER = "ticker"
    TICKER_US = "ticker_us"
    WKN = "wkn"


class ClassificationSystemID(StrEnum):
    """Supported classification systems."""

    GICS = "GICS"
    GECS = "GECS"
    YAHOOCS = "Yahoo Classification System"


class ClassificationLevel(IntEnum):
    """Generic classification hierarchy level."""

    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3
    LEVEL4 = 4
