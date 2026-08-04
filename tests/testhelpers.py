"""Helpers for test."""


from pathlib import Path
import json


def load_json(path: Path, filename: str):

    with open(path / filename, encoding="utf-8") as f:
        return json.load(f)
