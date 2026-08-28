"""Name similarity for Matching."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "no-any-return"

# fmt: off


import re

from rapidfuzz.fuzz import ratio


_SECURITY_SUFFIXES = (
    "b",
    "class b",
    "common share",
    "common shares",
    "ord",
    "ordinary share",
    "ordinary shares",
    "publ",
    "(publ.)",
    "share",
    "share from split",
    "shares",
    "shares from split",
)

_LEGAL_SUFFIXES = frozenset({
    "ab",
    "ag",
    "as",
    "a/s",
    "asa",
    "bv",
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
    "sarl",
    "sas",
    "se",
    "spa",
    "srl",
})


def normalize_name(
    name: str,
    *,
    remove_security_suffix: bool = True,
    remove_legal_suffix: bool = True,
) -> str:
    """Normalize a security/company name for comparison."""

    if not name:
        return ""

    value = name.casefold().replace(",", " ")

    if remove_security_suffix:
        value = re.sub(
            rf"[\s-]+(?:{'|'.join(map(re.escape, _SECURITY_SUFFIXES))})$",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()

    if remove_legal_suffix:
        for suffix in _LEGAL_SUFFIXES:
            pattern = r"\s+" + r"[\s.]*".join(re.escape(char) for char in suffix) + r"[\s.]*$"
            if re.search(pattern, value, flags=re.IGNORECASE):
                value = re.sub(
                    pattern,
                    "",
                    value,
                    flags=re.IGNORECASE,
                ).strip()

    return value


def name_similarity(
    name1: str | None,
    name2: str | None,
) -> float:
    """Return normalized name similarity in percent."""

    normalized1 = normalize_name(name1) if name1 else None
    normalized2 = normalize_name(name2) if name2 else None

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
