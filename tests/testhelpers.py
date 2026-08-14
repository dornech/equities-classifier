"""Helpers for test."""


# ruff and mypy per file settings
#

# fmt: off


from pathlib import Path
import json


def load_json(path: Path, filename: str):

    with open(path / filename, encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path, filename: str):

    return (path / filename).read_text(encoding="utf-8")
