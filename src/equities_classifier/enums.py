"""Enumerations used by business domain model of equities_classifier."""


from enum import IntEnum, StrEnum


class SecurityIdentifierType(StrEnum):
    """Security identifier type
    possible types see f. e. https://www.openfigi.com/api/documentation#v3-id-type-values
    """

    CINS = "cins"
    CUSIP = "cusip"
    ISIN = "isin"
    SHARE_CLASS_FIGI = "SHARE_CLASS_FIGI"
    SEDOL = "sedol"
    TICKER = "ticker"
    WKN = "wkn"


class ClassificationSystemID(StrEnum):
    """Supported classification systems."""

    GICS = "gics"
    GECS = "gecs"


class ClassificationLevel(IntEnum):
    """Generic classification hierarchy level."""

    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3
    LEVEL4 = 4
