from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class ScanResult:
    test_framework: str | None = None
    dep_management: str | None = None
    test_data_format: str | None = None
    test_data_count: int = 0
    test_data_paths: list[Path] = field(default_factory=list)
    test_case_count: int = 0
    test_case_paths: list[Path] = field(default_factory=list)


_DATA_EXTENSIONS = {
    ".csv": "csv",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xlsx": "excel",
    ".xls": "excel",
}

_TEST_FUNCTION_RE = re.compile(r"^\s*def\s+(test_\w+)\s*\(", re.MULTILINE)
_ROBOT_TEST_CASE_RE = re.compile(r"^\*{3}\s*Test Cases\s*\*{3}", re.MULTILINE)
_ROBOT_TEST_NAME_RE = re.compile(r"^(\S[^\n]+)$", re.MULTILINE)
_CUCUMBER_SCENARIO_RE = re.compile(r"^\s*Scenario(?:\s+Outline)?:", re.MULTILINE)


def scan_project(project_dir: Path) -> ScanResult:
    result = ScanResult()
    _detect_framework(project_dir, result)
    _detect_dep_management(project_dir, result)
    _detect_test_data(project_dir, result)
    _count_test_cases(project_dir, result)
    return result


def _detect_framework(root: Path, result: ScanResult) -> None:
    robot_files = list(root.rglob("*.robot"))
    if robot_files:
        result.test_framework = "robot_framework"
        return
    feature_files = list(root.rglob("*.feature"))
    if feature_files:
        result.test_framework = "cucumber"
        return
    if (root / "pytest.ini").exists():
        result.test_framework = "pytest"
        return
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and "[tool.pytest" in pyproject.read_text():
        result.test_framework = "pytest"
        return
    for py_file in root.rglob("*.py"):
        if "import unittest" in py_file.read_text():
            result.test_framework = "unittest"
            return


def _detect_dep_management(root: Path, result: ScanResult) -> None:
    if (root / "pyproject.toml").exists():
        result.dep_management = "pyproject.toml"
    elif (root / "requirements.txt").exists():
        result.dep_management = "requirements.txt"


def _detect_test_data(root: Path, result: ScanResult) -> None:
    data_dirs = [
        d for d in root.rglob("*")
        if d.is_dir() and "data" in d.name.lower()
    ]
    search_roots = data_dirs if data_dirs else [root]

    counts: dict[str, int] = {}
    paths: list[Path] = []
    for search_root in search_roots:
        for f in search_root.rglob("*"):
            if f.is_file() and f.suffix in _DATA_EXTENSIONS:
                fmt = _DATA_EXTENSIONS[f.suffix]
                counts[fmt] = counts.get(fmt, 0) + 1
                paths.append(f)

    if counts:
        dominant = max(counts, key=lambda k: counts[k])
        result.test_data_format = dominant
        result.test_data_count = sum(counts.values())
        result.test_data_paths = paths


def _count_test_cases(root: Path, result: ScanResult) -> None:
    robot_files = list(root.rglob("*.robot"))
    if robot_files:
        result.test_case_paths = robot_files
        result.test_case_count = sum(
            _count_robot_cases(f) for f in robot_files
        )
        return

    feature_files = list(root.rglob("*.feature"))
    if feature_files:
        result.test_case_paths = feature_files
        result.test_case_count = sum(
            len(_CUCUMBER_SCENARIO_RE.findall(f.read_text()))
            for f in feature_files
        )
        return

    test_files = [
        f for f in root.rglob("*.py")
        if f.name.startswith("test_") or f.name.endswith("_test.py")
    ]
    result.test_case_paths = test_files
    result.test_case_count = sum(
        len(_TEST_FUNCTION_RE.findall(f.read_text()))
        for f in test_files
    )


def _count_robot_cases(robot_file: Path) -> int:
    """Count test case names in a .robot file (lines starting non-whitespace inside a Test Cases block)."""
    text = robot_file.read_text()
    in_test_cases = False
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^\*{3}\s*Test Cases\s*\*{3}", line):
            in_test_cases = True
            continue
        if re.match(r"^\*{3}", line):
            in_test_cases = False
            continue
        if in_test_cases and stripped and not line.startswith(" ") and not line.startswith("\t"):
            count += 1
    return count
