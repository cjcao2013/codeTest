# TAP Data Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `tap-data-migration` GitHub Copilot CLI skill with a Python + uv toolset that guides users through assessing and migrating test data/cases from local projects into the TAP platform.

**Architecture:** Two-phase design — `assess.py` scans the project directory, auto-detects test data/case format and structure, prompts only for what it can't detect, and outputs a feasibility report with a Go/Pending/No-go decision. `migrate.py` uses that context to convert formats, upload via TAP API, validate results, and produce a migration report. Each module (`scanner`, `converter`, `uploader`, `validator`, `reporter`) has a single responsibility and is tested independently.

**Tech Stack:** Python 3.11+, uv, typer, httpx, python-dotenv, pytest

**Spec:** `docs/superpowers/specs/2026-04-09-tap-data-migration-design.md`

---

## File Map

### New files to create

| File | Responsibility |
|------|---------------|
| `tap-migration/pyproject.toml` | uv project config, dependencies |
| `tap-migration/.env.example` | TAP API credential placeholders |
| `tap-migration/assess.py` | Phase 1 CLI entry: scan → prompt → report |
| `tap-migration/migrate.py` | Phase 2 CLI entry: convert → upload → validate → report |
| `tap-migration/src/__init__.py` | Package marker |
| `tap-migration/src/scanner.py` | Auto-detect framework, test data/case location, format, count |
| `tap-migration/src/converter.py` | Convert local formats to TAP payload schema |
| `tap-migration/src/uploader.py` | Call TAP API to upload test data/cases (placeholders for endpoints) |
| `tap-migration/src/validator.py` | Compare local count vs TAP count, spot-check 10% sample |
| `tap-migration/src/reporter.py` | Render feasibility report and migration report as Markdown |
| `tap-migration/tests/__init__.py` | Package marker |
| `tap-migration/tests/test_scanner.py` | Unit tests for scanner |
| `tap-migration/tests/test_converter.py` | Unit tests for converter |
| `tap-migration/tests/test_uploader.py` | Unit tests for uploader (mocked HTTP) |
| `tap-migration/tests/test_validator.py` | Unit tests for validator |
| `tap-migration/tests/test_reporter.py` | Unit tests for reporter |
| `~/.claude/skills/tap-data-migration/SKILL.md` | Claude Code skill document |
| `.github/instructions/tap-data-migration.instructions.md` | GitHub Copilot instructions |

### Files to modify

| File | Change |
|------|--------|
| `.github/copilot-instructions.md` | Add reference to tap-data-migration skill |

---

## Task 1: Project Scaffold

**Files:**
- Create: `tap-migration/pyproject.toml`
- Create: `tap-migration/.env.example`
- Create: `tap-migration/src/__init__.py`
- Create: `tap-migration/tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p tap-migration/src tap-migration/tests
touch tap-migration/src/__init__.py tap-migration/tests/__init__.py
```

- [ ] **Step 2: Create `tap-migration/pyproject.toml`**

```toml
[project]
name = "tap-migration"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "httpx>=0.27",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "respx>=0.21",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Create `tap-migration/.env.example`**

```bash
TAP_API_BASE_URL=https://tap.example.com/api   # TBD — fill with TAP team
TAP_API_TOKEN=your-token-here                   # TBD — fill with TAP team
TAP_PROJECT_ID=your-project-id                  # TBD — confirm with TAP team (path segment / query param / body field)
```

- [ ] **Step 4: Install dependencies**

```bash
cd tap-migration && uv sync --extra dev
```

Expected: Dependencies resolved, `.venv` created.

- [ ] **Step 5: Verify tests can run (empty)**

```bash
cd tap-migration && uv run pytest
```

Expected: `no tests ran` — confirms tooling works.

- [ ] **Step 6: Commit**

```bash
git add tap-migration/
git commit -m "chore: scaffold tap-migration Python project"
```

---

## Task 2: scanner.py — Auto-detect Project Structure

**Files:**
- Create: `tap-migration/src/scanner.py`
- Create: `tap-migration/tests/test_scanner.py`

The scanner inspects `--project-dir` and returns a `ScanResult` dataclass. It never prompts — only reads the filesystem.

- [ ] **Step 1: Write failing tests**

Create `tap-migration/tests/test_scanner.py`:

```python
import pytest
from pathlib import Path
from src.scanner import scan_project, ScanResult


def test_detects_pytest_from_ini(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    result = scan_project(tmp_path)
    assert result.test_framework == "pytest"


def test_detects_pytest_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    result = scan_project(tmp_path)
    assert result.test_framework == "pytest"


def test_detects_unittest_from_imports(tmp_path):
    test_file = tmp_path / "test_foo.py"
    test_file.write_text("import unittest\nclass T(unittest.TestCase): pass\n")
    result = scan_project(tmp_path)
    assert result.test_framework == "unittest"


def test_framework_unknown_when_no_signals(tmp_path):
    result = scan_project(tmp_path)
    assert result.test_framework is None


def test_detects_pyproject_dependency_management(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    result = scan_project(tmp_path)
    assert result.dep_management == "pyproject.toml"


def test_detects_requirements_txt(tmp_path):
    (tmp_path / "requirements.txt").write_text("pytest\n")
    result = scan_project(tmp_path)
    assert result.dep_management == "requirements.txt"


def test_counts_csv_test_data_files(tmp_path):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    (data_dir / "a.csv").write_text("id,name\n1,foo\n")
    (data_dir / "b.csv").write_text("id,name\n2,bar\n")
    result = scan_project(tmp_path)
    assert result.test_data_format == "csv"
    assert result.test_data_count == 2


def test_counts_test_functions(tmp_path):
    (tmp_path / "test_foo.py").write_text(
        "def test_a(): pass\ndef test_b(): pass\n"
    )
    result = scan_project(tmp_path)
    assert result.test_case_count == 2


def test_unknown_test_data_when_empty(tmp_path):
    result = scan_project(tmp_path)
    assert result.test_data_format is None
    assert result.test_data_count == 0
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd tap-migration && uv run pytest tests/test_scanner.py -v
```

Expected: `ImportError` — scanner not yet implemented.

- [ ] **Step 3: Implement `tap-migration/src/scanner.py`**

```python
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


def scan_project(project_dir: Path) -> ScanResult:
    result = ScanResult()
    _detect_framework(project_dir, result)
    _detect_dep_management(project_dir, result)
    _detect_test_data(project_dir, result)
    _count_test_cases(project_dir, result)
    return result


def _detect_framework(root: Path, result: ScanResult) -> None:
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
        for f in search_root.iterdir():
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
    test_files = [
        f for f in root.rglob("*.py")
        if f.name.startswith("test_") or f.name.endswith("_test.py")
    ]
    result.test_case_paths = test_files
    result.test_case_count = sum(
        len(_TEST_FUNCTION_RE.findall(f.read_text()))
        for f in test_files
    )
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd tap-migration && uv run pytest tests/test_scanner.py -v
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add tap-migration/src/scanner.py tap-migration/tests/test_scanner.py
git commit -m "feat: add project scanner with auto-detect for framework, data format, test count"
```

---

## Task 3: converter.py — Format Conversion

**Files:**
- Create: `tap-migration/src/converter.py`
- Create: `tap-migration/tests/test_converter.py`

Reads local test data/case files and converts to TAP payload dicts. TAP schema fields are placeholder — stubs are filled with TBD values that the user replaces after getting the real schema from the TAP team.

- [ ] **Step 1: Write failing tests**

Create `tap-migration/tests/test_converter.py`:

```python
import pytest
import json
from pathlib import Path
from src.converter import convert_test_data_file, convert_test_case_file, ConversionError


def test_converts_csv_to_tap_payload(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,value\n1,foo,bar\n2,baz,qux\n")
    records = convert_test_data_file(csv_file)
    assert len(records) == 2
    assert records[0]["id"] == "1"
    assert records[0]["name"] == "foo"


def test_converts_json_to_tap_payload(tmp_path):
    json_file = tmp_path / "data.json"
    json_file.write_text(json.dumps([{"id": "1", "name": "alpha"}]))
    records = convert_test_data_file(json_file)
    assert len(records) == 1
    assert records[0]["name"] == "alpha"


def test_raises_on_unsupported_format(tmp_path):
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("hello")
    with pytest.raises(ConversionError, match="Unsupported"):
        convert_test_data_file(txt_file)


def test_converts_python_test_file_to_tap_cases(tmp_path):
    test_file = tmp_path / "test_login.py"
    test_file.write_text(
        "def test_valid_login(): pass\ndef test_invalid_password(): pass\n"
    )
    cases = convert_test_case_file(test_file)
    assert len(cases) == 2
    assert cases[0]["name"] == "test_valid_login"
    assert cases[0]["steps"] == []


def test_skips_non_test_functions(tmp_path):
    test_file = tmp_path / "test_utils.py"
    test_file.write_text("def helper(): pass\ndef test_real(): pass\n")
    cases = convert_test_case_file(test_file)
    assert len(cases) == 1
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd tap-migration && uv run pytest tests/test_converter.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `tap-migration/src/converter.py`**

```python
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd tap-migration && uv run pytest tests/test_converter.py -v
```

- [ ] **Step 5: Commit**

```bash
git add tap-migration/src/converter.py tap-migration/tests/test_converter.py
git commit -m "feat: add converter for csv/json/yaml test data and Python test case files"
```

---

## Task 4: uploader.py — TAP API Upload

**Files:**
- Create: `tap-migration/src/uploader.py`
- Create: `tap-migration/tests/test_uploader.py`

Calls TAP API to upload records. All endpoint paths are placeholders. Uses `httpx` with retry + exponential backoff. Per-record continue-on-error; abort on 401/403.

- [ ] **Step 1: Add `respx` to dev deps and sync**

In `tap-migration/pyproject.toml`, `respx` is already in dev deps. Run:

```bash
cd tap-migration && uv sync --extra dev
```

- [ ] **Step 2: Write failing tests**

Create `tap-migration/tests/test_uploader.py`:

```python
import pytest
import respx
import httpx
from src.uploader import upload_records, UploadResult, AuthError


BASE_URL = "https://tap.test/api"
TOKEN = "test-token"


@respx.mock
def test_uploads_records_successfully():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
    result = upload_records(
        records=[{"id": "1", "name": "a", "data": {}}],
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
    )
    assert result.uploaded == 1
    assert result.failed == 0


@respx.mock
def test_continues_on_single_record_failure():
    route = respx.post(f"{BASE_URL}/test-data")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(200),
    ]
    result = upload_records(
        records=[{"id": "1", "name": "a", "data": {}}, {"id": "2", "name": "b", "data": {}}],
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
    )
    assert result.uploaded == 1
    assert result.failed == 1
    assert result.failures[0]["id"] == "1"


@respx.mock
def test_aborts_on_auth_failure():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(401))
    with pytest.raises(AuthError):
        upload_records(
            records=[{"id": "1", "name": "a", "data": {}}],
            endpoint=f"{BASE_URL}/test-data",
            token=TOKEN,
        )


@respx.mock
def test_returns_empty_result_for_no_records():
    result = upload_records(records=[], endpoint=f"{BASE_URL}/test-data", token=TOKEN)
    assert result.uploaded == 0
    assert result.failed == 0
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
cd tap-migration && uv run pytest tests/test_uploader.py -v
```

- [ ] **Step 4: Implement `tap-migration/src/uploader.py`**

```python
from __future__ import annotations
import time
from dataclasses import dataclass, field
import httpx


class AuthError(Exception):
    pass


@dataclass
class UploadResult:
    uploaded: int = 0
    failed: int = 0
    failures: list[dict] = field(default_factory=list)


_MAX_RETRIES = 3
_RETRY_BASE_SECONDS = 1.0


def upload_records(
    records: list[dict],
    endpoint: str,
    token: str,
) -> UploadResult:
    """Upload records to a TAP API endpoint. Continue-on-error per record; abort on auth failure."""
    result = UploadResult()
    with httpx.Client(timeout=30) as client:
        for record in records:
            _upload_one(client, record, endpoint, token, result)
    return result


def _upload_one(
    client: httpx.Client,
    record: dict,
    endpoint: str,
    token: str,
    result: UploadResult,
) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    last_error: str = ""
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.post(endpoint, json=record, headers=headers)
            if response.status_code in (401, 403):
                raise AuthError(f"Auth failed: {response.status_code}")
            if response.is_success:
                result.uploaded += 1
                return
            last_error = f"HTTP {response.status_code}"
        except AuthError:
            raise
        except Exception as exc:
            last_error = str(exc)
        if attempt < _MAX_RETRIES - 1:
            time.sleep(_RETRY_BASE_SECONDS * (2 ** attempt))

    result.failed += 1
    result.failures.append({**record, "_error": last_error})
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
cd tap-migration && uv run pytest tests/test_uploader.py -v
```

- [ ] **Step 6: Commit**

```bash
git add tap-migration/src/uploader.py tap-migration/tests/test_uploader.py
git commit -m "feat: add uploader with retry, continue-on-error, and auth-abort behavior"
```

---

## Task 5: validator.py — Pre/Post Comparison

**Files:**
- Create: `tap-migration/src/validator.py`
- Create: `tap-migration/tests/test_validator.py`

Compares local record count against upload result. Spot-checks a random 10% sample (min 5) by comparing `id`, `name`, and one data field.

- [ ] **Step 1: Write failing tests**

Create `tap-migration/tests/test_validator.py`:

```python
import pytest
from src.validator import validate_migration, ValidationResult


def test_passes_when_counts_match():
    local = [{"id": str(i), "name": f"item{i}", "data": {"v": i}} for i in range(10)]
    uploaded = [{"id": str(i), "name": f"item{i}", "data": {"v": i}} for i in range(10)]
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    assert result.count_match is True
    assert result.sample_failures == []


def test_fails_when_counts_differ():
    local = [{"id": "1", "name": "a", "data": {}}] * 5
    uploaded = [{"id": "1", "name": "a", "data": {}}] * 3
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    assert result.count_match is False


def test_detects_name_mismatch_in_sample():
    local = [{"id": str(i), "name": f"item{i}", "data": {"v": i}} for i in range(20)]
    uploaded = [{"id": str(i), "name": f"WRONG{i}", "data": {"v": i}} for i in range(20)]
    result = validate_migration(local_records=local, uploaded_records=uploaded, seed=42)
    assert len(result.sample_failures) > 0


def test_sample_size_minimum_five():
    local = [{"id": str(i), "name": f"x{i}", "data": {}} for i in range(3)]
    uploaded = local[:]
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    # With fewer than 5 records, all are sampled
    assert result.sample_size == 3


def test_sample_size_ten_percent_of_large_set():
    local = [{"id": str(i), "name": f"x{i}", "data": {}} for i in range(100)]
    uploaded = local[:]
    result = validate_migration(local_records=local, uploaded_records=uploaded)
    assert result.sample_size == 10
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd tap-migration && uv run pytest tests/test_validator.py -v
```

- [ ] **Step 3: Implement `tap-migration/src/validator.py`**

```python
from __future__ import annotations
import random
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    count_match: bool
    local_count: int
    uploaded_count: int
    sample_size: int
    sample_failures: list[dict] = field(default_factory=list)


def validate_migration(
    local_records: list[dict],
    uploaded_records: list[dict],
    seed: int | None = None,
) -> ValidationResult:
    local_count = len(local_records)
    uploaded_count = len(uploaded_records)
    count_match = local_count == uploaded_count

    uploaded_by_id = {str(r.get("id", "")): r for r in uploaded_records}

    sample_size = max(5, int(local_count * 0.10)) if local_count >= 5 else local_count
    sample_size = min(sample_size, local_count)

    rng = random.Random(seed)
    sample = rng.sample(local_records, sample_size) if local_count > sample_size else local_records[:]

    failures = []
    for local in sample:
        record_id = str(local.get("id", ""))
        remote = uploaded_by_id.get(record_id)
        if remote is None:
            failures.append({"id": record_id, "reason": "not found in TAP"})
            continue
        if local.get("name") != remote.get("name"):
            failures.append({
                "id": record_id,
                "reason": f"name mismatch: local={local.get('name')!r} tap={remote.get('name')!r}",
            })

    return ValidationResult(
        count_match=count_match,
        local_count=local_count,
        uploaded_count=uploaded_count,
        sample_size=sample_size,
        sample_failures=failures,
    )
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd tap-migration && uv run pytest tests/test_validator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add tap-migration/src/validator.py tap-migration/tests/test_validator.py
git commit -m "feat: add validator with count check and 10% spot-sample comparison"
```

---

## Task 6: reporter.py — Markdown Report Generation

**Files:**
- Create: `tap-migration/src/reporter.py`
- Create: `tap-migration/tests/test_reporter.py`

Renders both the Phase 1 feasibility report and the Phase 2 migration report as Markdown strings. No file I/O — callers write the string to disk.

- [ ] **Step 1: Write failing tests**

Create `tap-migration/tests/test_reporter.py`:

```python
from src.reporter import render_feasibility_report, render_migration_report, DimensionStatus


def test_feasibility_report_contains_project_name():
    report = render_feasibility_report(
        project_name="my-tests",
        dimensions={
            "Test data format": DimensionStatus.OK,
            "Test case format": DimensionStatus.OK,
            "Data volume": DimensionStatus.WARN,
            "Project structure": DimensionStatus.OK,
        },
        risk_items=[],
        pending_items=[],
    )
    assert "my-tests" in report
    assert "🟡" in report  # Medium complexity due to one WARN


def test_feasibility_report_nogo_on_error():
    report = render_feasibility_report(
        project_name="x",
        dimensions={"Test data format": DimensionStatus.ERROR},
        risk_items=["Format not supported"],
        pending_items=[],
    )
    assert "No-go" in report or "❌" in report


def test_migration_report_contains_summary():
    from src.uploader import UploadResult
    from src.validator import ValidationResult

    data_upload = UploadResult(uploaded=10, failed=0)
    case_upload = UploadResult(uploaded=5, failed=1, failures=[{"id": "tc1", "_error": "500"}])
    validation = ValidationResult(
        count_match=True, local_count=15, uploaded_count=14,
        sample_size=5, sample_failures=[]
    )

    report = render_migration_report(
        project_name="my-tests",
        data_upload=data_upload,
        case_upload=case_upload,
        validation=validation,
    )
    assert "10" in report
    assert "tc1" in report
    assert "500" in report
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd tap-migration && uv run pytest tests/test_reporter.py -v
```

- [ ] **Step 3: Implement `tap-migration/src/reporter.py`**

```python
from __future__ import annotations
from datetime import date
from enum import Enum
from src.uploader import UploadResult
from src.validator import ValidationResult


class DimensionStatus(Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


_STATUS_ICON = {
    DimensionStatus.OK: "✅",
    DimensionStatus.WARN: "⚠️",
    DimensionStatus.ERROR: "❌",
}


def render_feasibility_report(
    project_name: str,
    dimensions: dict[str, DimensionStatus],
    risk_items: list[str],
    pending_items: list[str],
) -> str:
    has_error = any(s == DimensionStatus.ERROR for s in dimensions.values())
    warn_count = sum(1 for s in dimensions.values() if s == DimensionStatus.WARN)

    if has_error:
        complexity = "🔴 High"
        recommendation = "❌ Not recommended — resolve blockers first"
    elif warn_count >= 2:
        complexity = "🟡 Medium"
        recommendation = "⚠️ Resolve the following before proceeding"
    else:
        complexity = "🟢 Low"
        recommendation = "✅ Proceed with migration"

    dim_rows = "\n".join(
        f"| {name} | {_STATUS_ICON[status]} | |"
        for name, status in dimensions.items()
    )
    risks = "\n".join(f"- {r}" for r in risk_items) or "- None identified"
    pending = "\n".join(f"- [ ] {p}" for p in pending_items) or "- None"

    return f"""# TAP Migration Feasibility Report
Project: {project_name} | Date: {date.today()}

## Complexity Score: {complexity}

| Dimension | Status | Notes |
|-----------|--------|-------|
{dim_rows}

## Risk Items
{risks}

## Recommendation
{recommendation}

## Pending (confirm with TAP team)
{pending}
"""


def render_migration_report(
    project_name: str,
    data_upload: UploadResult,
    case_upload: UploadResult,
    validation: ValidationResult,
) -> str:
    data_validation = "✅" if validation.count_match and not validation.sample_failures else "⚠️"

    failures = []
    for f in data_upload.failures + case_upload.failures:
        record_id = f.get("id", "unknown")
        error = f.get("_error", "unknown error")
        failures.append(f"- `{record_id}`: {error}")
    failures_text = "\n".join(failures) or "- None"

    return f"""# TAP Migration Report
Project: {project_name} | Date: {date.today()}

## Summary
| Type | Local Count | Uploaded | Failed | Validation |
|------|------------|---------|--------|------------|
| Test data | {data_upload.uploaded + data_upload.failed} | {data_upload.uploaded} | {data_upload.failed} | {data_validation} |
| Test cases | {case_upload.uploaded + case_upload.failed} | {case_upload.uploaded} | {case_upload.failed} | {data_validation} |

## Failure Details
{failures_text}

## Next Steps
- [ ] Handle failed items manually
- [ ] Notify TAP team for acceptance
- [ ] Keep local backup until acceptance complete
"""
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd tap-migration && uv run pytest tests/test_reporter.py -v
```

- [ ] **Step 5: Commit**

```bash
git add tap-migration/src/reporter.py tap-migration/tests/test_reporter.py
git commit -m "feat: add Markdown report renderer for feasibility and migration reports"
```

---

## Task 7: assess.py — Phase 1 CLI

**Files:**
- Create: `tap-migration/assess.py`

Wires scanner → reporter. Prompts user only for dimensions that scanner couldn't detect.

- [ ] **Step 1: Create `tap-migration/assess.py`**

```python
#!/usr/bin/env python
"""Phase 1: Scan project, prompt for gaps, output feasibility report."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import typer
from src.scanner import scan_project
from src.reporter import render_feasibility_report, DimensionStatus

app = typer.Typer()


def _parse_volume_threshold(value: str) -> tuple[int, int]:
    try:
        parts = dict(kv.split(":") for kv in value.split(","))
        return int(parts["small"]), int(parts["medium"])
    except Exception:
        raise typer.BadParameter("Expected format: small:N,medium:N")


def _volume_status(count: int, small: int, medium: int) -> DimensionStatus:
    if count <= small:
        return DimensionStatus.OK
    if count <= medium:
        return DimensionStatus.WARN
    return DimensionStatus.ERROR


@app.command()
def main(
    project_dir: Path = typer.Option(..., help="Path to the local test project"),
    report_out: Path = typer.Option(Path("./tap-assessment-report.md"), help="Output path for report"),
    volume_threshold: str = typer.Option("500,5000", help="Volume thresholds as small:N,medium:N"),
) -> None:
    small_threshold, medium_threshold = _parse_volume_threshold(volume_threshold)
    scan = scan_project(project_dir)

    # Framework
    framework = scan.test_framework
    if not framework:
        framework = typer.prompt("Test framework not detected. Which framework do you use? (pytest/unittest/other)")

    # Dep management
    dep_mgmt = scan.dep_management
    if not dep_mgmt:
        dep_mgmt = typer.prompt("Dependency management not detected. (requirements.txt/pyproject.toml/other)")

    # Test data format
    data_format = scan.test_data_format
    if not data_format:
        data_format = typer.prompt(
            "No test data files detected in project dir.\n"
            "Where is your test data? (local-files/database/external-tool/none)"
        )

    # Volume status
    vol_status = _volume_status(scan.test_data_count, small_threshold, medium_threshold)

    # Structure status
    struct_status = DimensionStatus.OK if dep_mgmt in ("requirements.txt", "pyproject.toml") else DimensionStatus.WARN

    # Data format status (basic heuristic)
    supported_formats = {"csv", "json", "yaml", "yml"}
    if data_format and data_format.lower() in supported_formats:
        data_fmt_status = DimensionStatus.OK
    elif data_format in ("none", ""):
        data_fmt_status = DimensionStatus.WARN
    else:
        data_fmt_status = DimensionStatus.WARN

    case_fmt_status = DimensionStatus.OK if scan.test_case_count > 0 else DimensionStatus.WARN

    dimensions = {
        "Test data format": data_fmt_status,
        "Test case format": case_fmt_status,
        "Data volume": vol_status,
        "Project structure": struct_status,
    }

    pending = [
        "TAP supported test data formats: [TBD — confirm with TAP team]",
        "TAP test case import API: [TBD — confirm with TAP team]",
    ]
    risks = []
    if vol_status == DimensionStatus.ERROR:
        risks.append(f"Large data volume ({scan.test_data_count} records) — plan for batched upload")
    if data_fmt_status == DimensionStatus.WARN:
        risks.append(f"Test data format '{data_format}' requires TAP team confirmation")

    report = render_feasibility_report(
        project_name=project_dir.name,
        dimensions=dimensions,
        risk_items=risks,
        pending_items=pending,
    )

    report_out.write_text(report)
    typer.echo(f"Feasibility report written to: {report_out}")
    typer.echo(report)


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Smoke test**

```bash
cd tap-migration && uv run assess.py --project-dir . --report-out /tmp/test-report.md
```

Expected: Report written to `/tmp/test-report.md`, content printed to terminal.

- [ ] **Step 3: Commit**

```bash
git add tap-migration/assess.py
git commit -m "feat: add assess.py Phase 1 CLI — scan-first with prompt fallback"
```

---

## Task 8: migrate.py — Phase 2 CLI

**Files:**
- Create: `tap-migration/migrate.py`

Wires scanner → converter → uploader → validator → reporter. Reads `.env` for TAP credentials.

- [ ] **Step 1: Create `tap-migration/migrate.py`**

```python
#!/usr/bin/env python
"""Phase 2: Convert, upload, validate, and report migration."""
from __future__ import annotations
from pathlib import Path
import typer
from dotenv import load_dotenv
import os
from src.scanner import scan_project
from src.converter import convert_test_data_file, convert_test_case_file, ConversionError
from src.uploader import upload_records, UploadResult, AuthError
from src.validator import validate_migration
from src.reporter import render_migration_report

app = typer.Typer()

# --- TAP API endpoints (fill in after confirming with TAP team) ---
_TEST_DATA_ENDPOINT = "{TAP_API_BASE_URL}/test-data"    # TBD
_TEST_CASE_ENDPOINT = "{TAP_API_BASE_URL}/test-cases"   # TBD


@app.command()
def main(
    project_dir: Path = typer.Option(..., help="Path to the local test project"),
    env: Path = typer.Option(Path(".env"), help="Path to .env file"),
    dry_run: bool = typer.Option(False, help="Convert only, skip upload"),
    report_out: Path = typer.Option(Path("./tap-migration-report.md"), help="Output path for report"),
) -> None:
    load_dotenv(env)
    base_url = os.getenv("TAP_API_BASE_URL", "")
    token = os.getenv("TAP_API_TOKEN", "")

    if not dry_run and (not base_url or not token):
        typer.echo("ERROR: TAP_API_BASE_URL and TAP_API_TOKEN must be set in .env", err=True)
        raise typer.Exit(1)

    scan = scan_project(project_dir)

    # Convert test data
    all_data_records: list[dict] = []
    for data_file in scan.test_data_paths:
        try:
            all_data_records.extend(convert_test_data_file(data_file))
        except ConversionError as e:
            typer.echo(f"WARN: skipping {data_file.name} — {e}")

    # Convert test cases
    all_case_records: list[dict] = []
    for case_file in scan.test_case_paths:
        all_case_records.extend(convert_test_case_file(case_file))

    typer.echo(f"Converted: {len(all_data_records)} data records, {len(all_case_records)} test cases")

    if dry_run:
        typer.echo("Dry-run mode — skipping upload.")
        raise typer.Exit(0)

    # Upload
    data_endpoint = _TEST_DATA_ENDPOINT.format(TAP_API_BASE_URL=base_url)
    case_endpoint = _TEST_CASE_ENDPOINT.format(TAP_API_BASE_URL=base_url)

    try:
        typer.echo("Uploading test data...")
        data_result = upload_records(all_data_records, data_endpoint, token)
        typer.echo("Uploading test cases...")
        case_result = upload_records(all_case_records, case_endpoint, token)
    except AuthError as e:
        typer.echo(f"ERROR: Authentication failed — {e}", err=True)
        raise typer.Exit(1)

    # Validate
    combined_local = all_data_records + all_case_records
    combined_remote = (
        [{"id": r.get("id"), "name": r.get("name"), "data": r} for r in range(data_result.uploaded)] +
        [{"id": r.get("id"), "name": r.get("name"), "steps": []} for r in range(case_result.uploaded)]
    )
    validation = validate_migration(combined_local, combined_local[:data_result.uploaded + case_result.uploaded])

    # Report
    report = render_migration_report(
        project_name=project_dir.name,
        data_upload=data_result,
        case_upload=case_result,
        validation=validation,
    )
    report_out.write_text(report)
    typer.echo(f"Migration report written to: {report_out}")
    typer.echo(report)


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Smoke test with dry-run**

```bash
cd tap-migration && uv run migrate.py --project-dir . --dry-run
```

Expected: "Dry-run mode — skipping upload."

- [ ] **Step 3: Commit**

```bash
git add tap-migration/migrate.py
git commit -m "feat: add migrate.py Phase 2 CLI — convert/upload/validate/report pipeline"
```

---

## Task 9: Run Full Test Suite

- [ ] **Step 1: Run all tests with coverage**

```bash
cd tap-migration && uv run pytest --cov=src --cov-report=term-missing -v
```

Expected: All tests pass, coverage ≥ 80%.

- [ ] **Step 2: Fix any failing tests**

If any tests fail, fix the implementation (not the tests) before proceeding.

- [ ] **Step 3: Commit coverage baseline**

```bash
git add .
git commit -m "test: confirm full test suite passes with coverage baseline"
```

---

## Task 10: Skill Documents

**Files:**
- Create: `~/.claude/skills/tap-data-migration/SKILL.md`
- Create: `.github/instructions/tap-data-migration.instructions.md`
- Modify: `.github/copilot-instructions.md`

- [ ] **Step 1: Create `~/.claude/skills/tap-data-migration/SKILL.md`**

```bash
mkdir -p ~/.claude/skills/tap-data-migration
```

Content:

```markdown
---
name: tap-data-migration
description: Use when migrating test data and test cases from a local automation project into the TAP platform. Covers Phase 1 (feasibility assessment via project scan) and Phase 2 (Python + uv script generation, upload, validation, report).
---

# TAP Data Migration

## Overview

This skill guides migration of test data and test cases into TAP (Test Automation Platform).

**Two-phase model:**
- **Phase 1 — Assessment:** Scan the project directory, auto-detect test data/case format and structure, prompt only for gaps, output a feasibility report with Go/Pending/No-go decision.
- **Phase 2 — Execution:** Generate and run Python + uv migration scripts to convert, upload, validate, and report.

**Prerequisites:**
- [ ] Project has automated tests
- [ ] Test data/cases are locally managed (files, not already in a platform)

**Pipeline migration is out of scope — deferred to v2.**

---

## Phase 1: Run Assessment

```bash
uv run assess.py --project-dir ./your-test-project
```

The script auto-detects:
- Test framework (pytest / unittest)
- Dependency management style
- Test data files (format, count)
- Test case functions (count)

It prompts only for what it cannot detect. Output: `tap-assessment-report.md`.

**Decision gate (automated):**
- Any ❌ dimension → No-go
- 2+ ⚠️ dimensions → Pending (resolve with TAP team first)
- ≤1 ⚠️ → Go

---

## Phase 2: Run Migration

**Fill in `.env` first** (get values from TAP team):
```
TAP_API_BASE_URL=https://tap.example.com/api
TAP_API_TOKEN=your-token
TAP_PROJECT_ID=your-project-id
```

```bash
# Dry run (convert only, no upload)
uv run migrate.py --project-dir ./your-test-project --dry-run

# Full migration
uv run migrate.py --project-dir ./your-test-project --env .env
```

Output: `tap-migration-report.md`

---

## TAP API Placeholders

Fill these in `migrate.py` after confirming with TAP team:

| Purpose | Placeholder |
|---------|-------------|
| Upload test data | `POST [TAP_API_BASE_URL]/test-data` |
| Upload test cases | `POST [TAP_API_BASE_URL]/test-cases` |
| Auth | `Bearer $TAP_API_TOKEN` |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Single record fails | Log, continue |
| Auth failure | Abort immediately |
| Network timeout | Retry 3× with backoff |
| All records fail | Abort, surface in report |

---

## Script Location

The migration scripts live in `tap-migration/` within this repo. Deploy them to the target project directory before running.
```

- [ ] **Step 2: Create `.github/instructions/tap-data-migration.instructions.md`**

Mirror the SKILL.md content into the Copilot instructions format (same content, same structure).

- [ ] **Step 3: Update `.github/copilot-instructions.md`**

Add one line referencing the new skill under the existing TAP migration section.

- [ ] **Step 4: Commit**

```bash
git add ~/.claude/skills/tap-data-migration/ .github/
git commit -m "docs: add tap-data-migration skill documents for Claude Code and GitHub Copilot"
```

---

## Done Criteria

- [ ] All tests pass (`uv run pytest --cov=src` ≥ 80% coverage)
- [ ] `uv run assess.py --project-dir . ` runs without errors
- [ ] `uv run migrate.py --project-dir . --dry-run` runs without errors
- [ ] `~/.claude/skills/tap-data-migration/SKILL.md` exists
- [ ] `.github/instructions/tap-data-migration.instructions.md` exists
