"""Tests for classification systems."""


# ruff and mypy per file settings
# others
# ruff: noqa: PLC2701, RUF105
#
# fmt: off


import pytest

from equities_classifier.classification.systems import (
    GICS_DICT,
    GICS_INVDICT,
    _find_gics_code,
    _normalize_gics_name,
    resolve_gics_motleyfool,
)
from equities_classifier.enums import ClassificationLevel
from equities_classifier.models import ClassificationNode
from equities_classifier.classification.classificationhelper import ClassificationHelper


def test_gics_dict_contains_hierarchy() -> None:
    """Test that GICS dictionary contains all hierarchy levels."""

    assert GICS_DICT["45"] == "information technology"
    assert GICS_DICT["4520"] == "technology hardware and equipment"
    assert GICS_DICT["452020"] == "technology hardware, storage and peripherals"


def test_gics_inverse_dict_contains_level() -> None:
    """Test that inverse GICS dictionary includes classification level."""

    assert GICS_INVDICT["information technology", 1] == "45"
    assert GICS_INVDICT["technology hardware, storage and peripherals", 3,] == "452020"


def test_normalize_gics_name_ampersand() -> None:
    """Test normalization of ampersand and 'and'."""

    assert _normalize_gics_name("Oil & Gas Drilling",) == _normalize_gics_name("Oil and Gas Drilling",)


@pytest.mark.parametrize(
    ("name", "level", "expected"),
    [
        ("Information Technology", 1, "45",),
        ("Technology Hardware, Storage and Peripherals", 3, "452020",),
    ],
)
def test_find_gics_code_exact(
    name: str,
    level: int,
    expected: str,
) -> None:
    """Test exact GICS name lookup."""

    assert _find_gics_code(name, level) == expected


def test_find_gics_code_ampersand_and() -> None:
    """Test equivalent ampersand and 'and' spelling."""

    assert _find_gics_code("Oil & Gas Drilling", 3,) == _find_gics_code("Oil and Gas Drilling", 3,)


def test_find_gics_code_is_level_specific() -> None:
    """Test that GICS lookup does not cross classification levels."""

    assert _find_gics_code("Information Technology", 1,) == "45"
    assert _find_gics_code("Information Technology", 2,) is None


def test_find_gics_code_fuzzy() -> None:
    """Test fuzzy GICS name lookup."""

    assert _find_gics_code("Technology Hardware Storage Peripherals", 3,) == "452020"


def test_find_gics_code_unknown() -> None:
    """Test unknown GICS name."""

    assert _find_gics_code("This is definitely not a GICS classification", 3,) is None


def test_resolve_gics_motleyfool() -> None:
    """Test Motley Fool GICS resolution."""

    nodes = {
        ClassificationLevel.LEVEL1: ClassificationNode(value="Information Technology",),
        ClassificationLevel.LEVEL3: ClassificationNode(value="Technology Hardware, Storage and Peripherals",),
    }

    result = resolve_gics_motleyfool(nodes)

    assert result[ClassificationLevel.LEVEL1].value == "Information Technology"
    assert result[ClassificationLevel.LEVEL1].code == "45"

    assert result[ClassificationLevel.LEVEL2].value == "Technology Hardware & Equipment"
    assert result[ClassificationLevel.LEVEL2].code == "4520"

    assert result[ClassificationLevel.LEVEL3].value == "Technology Hardware, Storage & Peripherals"
    assert result[ClassificationLevel.LEVEL3].code == "452020"


def test_resolve_gics_motleyfool_without_sector() -> None:
    """Test GICS resolution without Motley Fool sector."""

    nodes = {
        ClassificationLevel.LEVEL3: ClassificationNode(value="Technology Hardware, Storage and Peripherals",),
    }

    result = resolve_gics_motleyfool(nodes)

    assert result[ClassificationLevel.LEVEL1].code == "45"
    assert result[ClassificationLevel.LEVEL2].code == "4520"
    assert result[ClassificationLevel.LEVEL3].code == "452020"


def test_resolve_gics_motleyfool_sector_mismatch_corrected() -> None:
    """Test handling of inconsistent Motley Fool sector."""

    nodes = {
        ClassificationLevel.LEVEL1: ClassificationNode(value="Energy",),
        ClassificationLevel.LEVEL3: ClassificationNode(value="Technology Hardware, Storage and Peripherals",),
    }

    result = resolve_gics_motleyfool(nodes)

    # The resolver should correct supplied information.
    assert result[ClassificationLevel.LEVEL1].value == "Information Technology"
    assert ClassificationLevel.LEVEL2 in result
    assert result[ClassificationLevel.LEVEL3].value == "Technology Hardware, Storage & Peripherals"


def test_resolve_gics_motleyfool_sector_mismatch_monkeypatched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test logging of inconsistent Motley Fool sector."""

    calls: list[tuple[str, str]] = []

    def mismatch(
        *args: object,
        **kwargs: object,
    ) -> None:
        calls.append((str(args[-2]), str(args[-1]),))

    monkeypatch.setattr(
        ClassificationHelper,
        "classification_mismatch",
        mismatch,
    )

    nodes = {
        ClassificationLevel.LEVEL1: ClassificationNode(value="Energy",),
        ClassificationLevel.LEVEL3: ClassificationNode(value="Technology Hardware, Storage and Peripherals",),
    }

    resolve_gics_motleyfool(nodes)

    assert calls
