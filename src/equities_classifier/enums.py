from enum import IntEnum, StrEnum


class SecurityIdentifierType(StrEnum):
    """Security identifier type"""

    ISIN = "isin"
    FIGI = "figi"
    COMPOSITE_FIGI = "composite_figi"
    SHARE_CLASS_FIGI = "share_class_figi"
    TICKER = "ticker"
    CUSIP = "cusip"
    SEDOL = "sedol"
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
