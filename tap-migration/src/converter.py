from __future__ import annotations
import csv
import json
import re
from pathlib import Path


class ConversionError(Exception):
    pass


_TEST_FUNC_RE = re.compile(r"^\s*def\s+(test_\w+)\s*\(", re.MULTILINE)


def convert_test_data_file(path: Path) -> list[dict]:
    """Convert a local test data file to a list of TAP payload dicts."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _from_csv(path)
    if suffix == ".json":
        return _from_json(path)
    if suffix in (".yaml", ".yml"):
        return _from_yaml(path)
    raise ConversionError(f"Unsupported format: {suffix}")


def convert_test_case_file(path: Path) -> list[dict]:
    """Extract test functions from a Python file as TAP case payloads."""
    source = path.read_text()
    names = _TEST_FUNC_RE.findall(source)
    return [{"id": name, "name": name, "steps": []} for name in names]


def _from_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [
            {"id": row.get("id", ""), "name": row.get("name", ""), "data": dict(row)}
            for row in reader
        ]


def _from_json(path: Path) -> list[dict]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raw = [raw]
    return [
        {"id": str(r.get("id", "")), "name": str(r.get("name", "")), "data": r}
        for r in raw
    ]


def _from_yaml(path: Path) -> list[dict]:
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise ConversionError("PyYAML not installed. Add 'pyyaml' to dependencies.") from e
    raw = yaml.safe_load(path.read_text()) or []
    if not isinstance(raw, list):
        raw = [raw]
    return [
        {"id": str(r.get("id", "")), "name": str(r.get("name", "")), "data": r}
        for r in raw
    ]
