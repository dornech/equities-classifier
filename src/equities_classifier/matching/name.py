"""Name similarity for Matching."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "no-any-return"

# fmt: off


import re

from rapidfuzz.fuzz import ratio


_LEGAL_SUFFIXES = frozenset({
    "ag",
    "asa",
    "corp",
    "corporation",
    "co",
    "company",
    "inc",
    "incorporated",
    "limited",
    "ltd",
    "nv",
    "plc",
    "sa",
    "se",
    "spa",
    "srl",
})


def normalize_name(name: str | None) -> str:
    """Normalize a security/company name for comparison."""

    if not name:
        return ""

    value = name.casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    words = value.split()

    words = [
        word
        for word in words
        if word not in _LEGAL_SUFFIXES
    ]

    return " ".join(words)


def name_similarity(
    name1: str | None,
    name2: str | None,
) -> float:
    """Return normalized name similarity in percent."""

    normalized1 = normalize_name(name1)
    normalized2 = normalize_name(name2)

    if not normalized1 or not normalized2:
        return 0.0

    return ratio(normalized1, normalized2)


def names_are_similar(
    name1: str | None,
    name2: str | None,
    threshold: float = 85.0,
) -> bool:
    """Return whether two names are sufficiently similar."""

    return name_similarity(name1, name2) >= threshold
