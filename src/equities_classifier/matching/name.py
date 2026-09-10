"""Name similarity for Matching."""


# ruff and mypy per file settings
#
# disable mypy errors
# mypy: disable-error-code = "no-any-return"

# fmt: off


import re

from rapidfuzz.fuzz import ratio


_UMLAUT_TRANSLATION = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "é": "e",
        "è": "e",
        "ë": "e",
    }
)

_PREFIX_REPLACEMENTS = {
    "the ": "",
    "cie ": "compagnie ",
}

_MIDFIX_REPLACEMENTS = {
    " info ": " information ",
    " intl ": " international ",
    "&": " and ",
}

_SUFFIX_REPLACEMENTS = {
    "/the": "",
    "and co": "",
}

# note: first longer terms then shorter terms with same ending
_SECURITY_SUFFIXES = (
    "cl a",
    "cl b",
    "class a",
    "class b",
    "a",
    "a reg",
    "b",
    "b reg",
    "common share",
    "common shares",
    "ord",
    "ordinary share",
    "ordinary share - non voting",
    "ordinary shares",
    "ordinary shares - non voting",
    "part zert",
    "pc",
    "publ",
    "(publ)",
    "(publ.)",
    "reg",
    "share",
    "share from split",
    "shares",
    "shares from split",
    "shares subord.vtg",
    "sub vtg shs",
    "vtg shs",
    "shs",
    "shs subord.vtg",
)

_LEGAL_SUFFIXES = frozenset({
    "ab",
    "ag",
    "aktiengesellschaft",
    "as",
    "a/s",
    "asa",
    "bv",
    "corp",
    "corporation",
    "co",
    "cos",
    "company",
    "companies",
    "companies inc",
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
    "société européenne",
    "société en commandite par actions",
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

    value = name.casefold().translate(_UMLAUT_TRANSLATION).replace(",", " ").replace("-", " ")

    for prefix, replacement in _PREFIX_REPLACEMENTS.items():
        if value.startswith(prefix):
            value = replacement + value.removeprefix(prefix)

    for midfix, replacement in _MIDFIX_REPLACEMENTS.items():
        value = value.replace(midfix, replacement).replace("  ", " ")

    for suffix, replacement in _SUFFIX_REPLACEMENTS.items():
        if value.endswith(suffix):
            value = value.removesuffix(suffix) + replacement

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


def name_contains_other_name(
    name1: str | None,
    name2: str | None,
) -> bool:
    """Return normalized name similarity in percent."""

    normalized1 = normalize_name(name1) if name1 else None
    normalized2 = normalize_name(name2) if name2 else None

    if normalized1 and normalized2:
        return normalized1.find(normalized2) == 0 or normalized2.find(normalized1) == 0

    return False
