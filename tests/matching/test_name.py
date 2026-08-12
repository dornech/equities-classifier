"""Unit tests for security name similarity."""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E303
# others
# ruff: noqa: RUF105

# fmt: off



import pytest

import math

from equities_classifier.matching.name import name_similarity


# test group with expected ratio


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("Apple Inc.", "Apple Inc.", 100.0),
        ("Apple", "Apple Inc.", 100.0),
        ("Berkshire Hathaway Inc.", "Berkshire Hathaway", 100.0),
    ],
)
def test_name_similarity_normalized_names(
    left: str,
    right: str,
    expected: float,
) -> None:
    """Test similarity of equivalent names after normalization."""

    assert name_similarity(left, right) == pytest.approx(expected)


def test_name_similarity_is_symmetric() -> None:
    """Name similarity must be independent of argument order."""

    left = "Apple Inc."
    right = "Apple Incorporated"

    assert name_similarity(left, right) == pytest.approx(
        name_similarity(right, left)
    )


def test_name_similarity_empty_name() -> None:
    """Empty names must not produce a high similarity."""

    assert math.isclose(name_similarity("", "Apple Inc."), 0.0, abs_tol=1e-9)
    assert math.isclose(name_similarity("Apple Inc.", ""), 0.0, abs_tol=1e-9)


def test_name_similarity_both_empty() -> None:
    """Two empty names must not accidentally match."""

    assert math.isclose(name_similarity("", ""), 0.0, abs_tol=1e-9)


# test group without expected ratio


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("Apple Inc.", "Apple Inc."),
        ("Apple Inc.", "Apple Incorporated"),
        ("Berkshire Hathaway Inc.", "Berkshire Hathaway"),
    ],
)
def test_similar_names_have_high_similarity(
    left: str,
    right: str,
) -> None:
    """Similar security names must have a high similarity."""

    assert name_similarity(left, right) >= 85.0


def test_different_names_have_low_similarity() -> None:
    """Different security names must have a low similarity."""

    assert name_similarity(
        "Apple Inc.",
        "Microsoft Corporation",
    ) < 50.0


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("", "Apple Inc."),
        ("Apple Inc.", ""),
    ],
)
def test_empty_name(
    left: str,
    right: str,
) -> None:
    """An empty name must not match a non-empty name."""

    assert math.isclose(name_similarity(left, right), 0.0, abs_tol=1e-9)
