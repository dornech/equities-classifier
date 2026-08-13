"""Classification Systems supported by equities_classifier."""


# ruff and mypy per file settings
#

# fmt: off


from collections.abc import Mapping
from immutabledict import immutabledict

from equities_classifier.enums import (
    ClassificationSystemID,
    ClassificationLevel,
)
from equities_classifier.models import (
    ClassificationSystem,
    ClassificationNode,
)


GICS = ClassificationSystem(
    id=ClassificationSystemID.GICS,
    display_name="Global Industry Classification Standard",
    authorities=(
        "MSCI",
        "S&P Dow Jones Indices",
    ),
    hierarchy=(
        "Sector",
        "Industry Group",
        "Industry",
        "Sub-Industry",
    ),
    supports_codes=True,
)


GECS = ClassificationSystem(
    id=ClassificationSystemID.GECS,
    display_name="Global Equity Classification Structure",
    authorities=("Morningstar",),
    hierarchy=(
        "Super Sector",
        "Sector",
        "Industry",
    ),
    supports_codes=False,
)


MAP_GECS_SUPERSECTOR_FROM_SECTOR: immutabledict[str, str] = immutabledict({
    "Basic Materials": "Cyclical",
    "Consumer Cyclical": "Cyclical",
    "Financial Services": "Cyclical",
    "RealEstate": "Cyclical",
    "Communication Services": "Sensitive",
    "Energy": "Sensitive",
    "Industrials": "Sensitive",
    "Technology": "Sensitive",
    "Healthcare": "Defensive",
    "Consumer Defensive": "Defensive",
    "Utilities": "Defensive",
})


def resolve_gecs_supersector(
    nodes: Mapping[ClassificationLevel, ClassificationNode],
) -> Mapping[ClassificationLevel, ClassificationNode]:
    """Resolve missing GECS super sector."""

    result = dict(nodes)

    sector = result.get(ClassificationLevel.LEVEL2)
    if sector is None:
        return result

    super_sector = MAP_GECS_SUPERSECTOR_FROM_SECTOR.get(sector.value,)
    if super_sector is None:
        return result

    result.setdefault(
        ClassificationLevel.LEVEL1,
        ClassificationNode(level=ClassificationLevel.LEVEL1, value=super_sector,),
    )

    return result
