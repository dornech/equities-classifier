"""Classification Systems supported by equities_classifier."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: N811, PLR2004, RUF105
#
# disable mypy errors
# mypy: disable-error-code = "arg-type, index, no-any-return"


# fmt: off


from collections.abc import Mapping
from immutabledict import immutabledict

from functools import cache

from rapidfuzz.fuzz import ratio

from equities_classifier.enums import DataSourceID, ClassificationSystemID, ClassificationLevel
from equities_classifier.models import ClassificationSystem, ClassificationNode
from equities_classifier.classification.classificationhelper import ClassificationHelper
from gics import GICS as GICSDefinition


# GECS

GECS = ClassificationSystem(
    id=ClassificationSystemID.GECS,
    display_name="Global Equity Classification Structure",
    short_name="GECS",
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
    nodes: dict[ClassificationLevel, ClassificationNode],
) -> Mapping[ClassificationLevel, ClassificationNode]:
    """Resolve missing GECS super sector."""

    result = dict(nodes)

    sector = result.get(ClassificationLevel.LEVEL2)
    if sector is None:
        return result

    super_sector = MAP_GECS_SUPERSECTOR_FROM_SECTOR.get(sector.value)
    if super_sector is None:
        return result

    result.setdefault(
        ClassificationLevel.LEVEL1,
        ClassificationNode(value=super_sector),
    )

    return result


# GICS


GICS = ClassificationSystem(
    id=ClassificationSystemID.GICS,
    display_name="Global Industry Classification Standard",
    short_name="GICS",
    authorities=("MSCI", "S&P Dow Jones Indices",),
    hierarchy=(
        "Sector",
        "Industry Group",
        "Industry",
        "Sub-Industry",
    ),
    supports_codes=True,
)

_GICS_NAME_SIMILARITY_THRESHOLD = 90.0


def _normalize_gics_name(name: str) -> str:
    """Normalize a GICS name for comparison."""
    return (name.casefold().replace("&", "and").replace("  ", " ").strip())


GICS_DICT: dict[str, str] = {
    code: _normalize_gics_name(definition["name"])
    for code, definition
    in GICSDefinition("").definition.items()
}

GICS_INVDICT: dict[tuple[str, int], str] = {
    (_normalize_gics_name(definition["name"]), len(code) // 2): code
    for code, definition in GICSDefinition("").definition.items()
}


@cache
def _find_gics_code(name: str, level: int) -> str | None:
    """Find GICS code by normalized name."""

    normalized_name = _normalize_gics_name(name)

    code = GICS_INVDICT.get((normalized_name, level))
    if code is not None:
        return code

    best_code: str | None = None
    best_similarity = 0.0

    for (gics_name, gics_level), gics_code in GICS_INVDICT.items():

        if gics_level != level:
            continue

        similarity = ratio(normalized_name, gics_name)
        if similarity > best_similarity:
            best_similarity = similarity
            best_code = gics_code

    if best_similarity < _GICS_NAME_SIMILARITY_THRESHOLD:
        return None

    return best_code


def resolve_gics_motleyfool(
    nodes: Mapping[ClassificationLevel, ClassificationNode],
) -> Mapping[ClassificationLevel, ClassificationNode]:
    """Resolve and validate Motley Fool GICS classification."""

    result = dict(nodes)

    sector_node = result.get(ClassificationLevel.LEVEL1)
    industry_node = result.get(ClassificationLevel.LEVEL3)

    if industry_node is None:
        return result

    # Find GICS industry (level 3) from Motley-Fool industry name and validate.
    industry_code: str | None = _find_gics_code(industry_node.value, 3)
    if industry_code is None:
        ClassificationHelper.classification_element_invalid(
            DataSourceID.MOTLEYFOOL,
            ClassificationSystemID.GICS,
            ClassificationLevel.LEVEL3,
            industry_node.value,
        )
        return result

    # GICS level 3 must consist of six digits.
    if len(industry_code) < 6:
        return result

    # Derive the complete hierarchy from the level-3 code.
    sector_code = industry_code[:2]
    industry_group_code = industry_code[:4]

    # Validate Motley-Fool sector against the sector derived
    # from the GICS industry code.
    if sector_node is not None:
        expected_sector = GICS_DICT.get(sector_code)
        if expected_sector is not None:
            actual_sector = _normalize_gics_name(sector_node.value)
            if actual_sector != expected_sector:
                # Sector and industry disagree. Do not silently
                # create an inconsistent classification.
                ClassificationHelper.classification_mismatch(
                    DataSourceID.MOTLEYFOOL,
                    ClassificationSystemID.GICS,
                    ClassificationLevel.LEVEL1,
                    actual_sector,
                    expected_sector,
                )

    # Replace / enrich level 1 with the canonical GICS value.
    sector_name = GICS_DICT.get(sector_code)
    if sector_name is not None:
        result[ClassificationLevel.LEVEL1] = ClassificationNode(
            value=GICSDefinition(sector_code).sector.name,
            code=sector_code,
        )

    # Level 2 is not supplied by Motley Fool.
    industry_group_name = GICS_DICT.get(industry_group_code)
    if industry_group_name is not None:
        result[ClassificationLevel.LEVEL2] = ClassificationNode(
            value=GICSDefinition(industry_group_code).industry_group.name,
            code=industry_group_code,
        )

    # Level 3 comes from Motley-Fool but gets the canonical GICS code/name.
    industry_name = GICS_DICT.get(industry_code)
    if industry_name is not None:
        result[ClassificationLevel.LEVEL3] = ClassificationNode(
            value=GICSDefinition(industry_code).industry.name,
            code=industry_code,
        )

    return result


def resolve_gics_seekingalpha(
    nodes: Mapping[ClassificationLevel, ClassificationNode],
) -> Mapping[ClassificationLevel, ClassificationNode] | None:
    """Resolve and validate SeekingAlpha GICS classification."""

    result = dict(nodes)

    sector_node = result.get(ClassificationLevel.LEVEL1)
    subindustry_node = result.get(ClassificationLevel.LEVEL4)

    if subindustry_node is None:
        return result

    # validate codes
    if sector_node and sector_node.code != subindustry_node.code[:2]:
        ClassificationHelper.classification_inconsistent(
            DataSourceID.SEEKINGALPHA,
            ClassificationSystemID.GICS,
            ClassificationLevel.LEVEL1,
            sector_node.value,
        )

    # Set GICS subindustry (level 4) from SeekingAlpha and validate
    subindustry_code = subindustry_node.code
    if GICS_INVDICT.get((_normalize_gics_name(subindustry_node.value), 4)) != subindustry_code:
        ClassificationHelper.classification_element_invalid(
            DataSourceID.SEEKINGALPHA,
            ClassificationSystemID.GICS,
            ClassificationLevel.LEVEL4,
            subindustry_node.value,
        )
        return result

    # GICS level 4 must consist of eight digits.
    if subindustry_code and len(subindustry_code) < 8:
        return result

    # Derive the complete hierarchy from the level-4 code.
    industry_code = subindustry_code[:6]
    industry_group_code = subindustry_code[:4]
    sector_code = subindustry_code[:2]

    # Validate SeekingAlpha sector against the sector derived
    # from the GICS industry code.
    if sector_node is not None:
        expected_sector = GICS_DICT.get(sector_code)
        if expected_sector is not None:
            actual_sector = _normalize_gics_name(sector_node.value)
            if actual_sector != expected_sector:
                # Sector and subindustry disagree. Do not silently
                # create an inconsistent classification.
                ClassificationHelper.classification_mismatch(
                    DataSourceID.MOTLEYFOOL,
                    ClassificationSystemID.GICS,
                    ClassificationLevel.LEVEL1,
                    actual_sector,
                    expected_sector,
                )

    # Replace / enrich level 1 with the canonical GICS value.
    sector_name = GICS_DICT.get(sector_code)
    if sector_name is not None:
        result[ClassificationLevel.LEVEL1] = ClassificationNode(
            value=GICSDefinition(sector_code).sector.name,
            code=sector_code,
        )

    # Level 2 is not supplied by SeekingAlpha.
    industry_group_name = GICS_DICT.get(industry_group_code)
    if industry_group_name is not None:
        result[ClassificationLevel.LEVEL2] = ClassificationNode(
            value=GICSDefinition(industry_group_code).industry_group.name,
            code=industry_group_code,
        )

    # Level 3 is not supplied by SeekingAlpha.
    industry_name = GICS_DICT.get(industry_code)
    if industry_name is not None:
        result[ClassificationLevel.LEVEL3] = ClassificationNode(
            value=GICSDefinition(industry_code).industry.name,
            code=industry_code,
        )

    # Level 4 comes from SeekingAlpha but gets the canonical GICS code/name.
    subindustry_name = GICS_DICT.get(subindustry_code)
    if subindustry_name is not None:
        result[ClassificationLevel.LEVEL4] = ClassificationNode(
            value=GICSDefinition(subindustry_code).sub_industry.name,
            code=subindustry_code,
        )

    return result


# Yahoo

YAHOOCS = ClassificationSystem(
    id=ClassificationSystemID.YAHOOCS,
    display_name="Yahoo Classification Standard",
    short_name="Yahoo",
    authorities=("Yahoo",),
    hierarchy=(
        "Sector",
        "Industry",
    ),
    supports_codes=False,
)
