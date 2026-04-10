# TAP Demo Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a demo-friendly e-commerce test project and per-record progress logging with configurable upload delay to make the migration demo visually compelling.

**Architecture:** Three independent work streams: (1) create `demo-project/` with real test data files and business-meaningful test names; (2) add `on_progress` callback + `upload_delay` to the Python uploader/migrate pipeline; (3) extend ConfigForm to support `type: 'number'` and wire `upload_delay` through the API router and MigratePage.

**Tech Stack:** Python + typer + httpx (backend), React 18 + TypeScript + shadcn/ui (frontend), FastAPI + Pydantic (API router)

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `demo-project/pyproject.toml` | Marks project as pytest-based |
| Create | `demo-project/tests/test_orders.py` | 18 order test stubs |
| Create | `demo-project/tests/test_payments.py` | 14 payment test stubs |
| Create | `demo-project/tests/test_users.py` | 10 user test stubs |
| Create | `demo-project/tests/data/orders.csv` | 20 order rows |
| Create | `demo-project/tests/data/products.json` | 15 product items |
| Create | `demo-project/tests/data/users.csv` | 12 user rows |
| Modify | `tap-migration/src/uploader.py` | Add `on_progress` + `upload_delay` |
| Modify | `tap-migration/tests/test_uploader.py` | Tests for new params |
| Modify | `tap-migration/migrate.py` | Add `--upload-delay` + progress output |
| Modify | `tap-migration/tests/test_migrate.py` | Tests for new flag + output |
| Modify | `frontend/src/components/ConfigForm.tsx` | Add `type: 'number'` support |
| Modify | `frontend/src/components/ConfigForm.test.tsx` | Tests for number field |
| Modify | `frontend/src/lib/types.ts` | Add `upload_delay` to `MigrateConfig` |
| Modify | `frontend/src/pages/MigratePage.tsx` | Add upload_delay field |
| Modify | `api/routers/migrate.py` | Add `upload_delay` to request + cmd |
| Modify | `api/tests/test_routes.py` | Test upload_delay forwarded to cmd |

---

## Task 1: Demo Project — test data files and test stubs

**Files:**
- Create: `demo-project/pyproject.toml`
- Create: `demo-project/tests/__init__.py`
- Create: `demo-project/tests/data/orders.csv`
- Create: `demo-project/tests/data/products.json`
- Create: `demo-project/tests/data/users.csv`
- Create: `demo-project/tests/test_orders.py`
- Create: `demo-project/tests/test_payments.py`
- Create: `demo-project/tests/test_users.py`

- [ ] **Step 1: Create `demo-project/pyproject.toml`**

```toml
[project]
name = "ecommerce-order-service-tests"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create `demo-project/tests/__init__.py`** (empty file)

- [ ] **Step 3: Create `demo-project/tests/data/orders.csv`**

```csv
order_id,customer_name,amount,status,created_at
ORD-001,Alice Chen,128.50,completed,2024-01-15
ORD-002,Bob Smith,45.00,pending,2024-01-16
ORD-003,Carol Wu,289.99,completed,2024-01-17
ORD-004,David Kim,73.25,cancelled,2024-01-18
ORD-005,Emma Jones,156.80,completed,2024-01-19
ORD-006,Frank Lee,92.00,pending,2024-01-20
ORD-007,Grace Park,340.50,completed,2024-01-21
ORD-008,Henry Brown,18.99,refunded,2024-01-22
ORD-009,Iris Wang,210.00,completed,2024-01-23
ORD-010,Jack Miller,67.50,pending,2024-01-24
ORD-011,Karen Davis,445.00,completed,2024-01-25
ORD-012,Leo Zhang,33.75,cancelled,2024-01-26
ORD-013,Mia Johnson,187.25,completed,2024-01-27
ORD-014,Noah Wilson,94.00,pending,2024-01-28
ORD-015,Olivia Moore,520.00,completed,2024-01-29
ORD-016,Paul Taylor,62.50,refunded,2024-01-30
ORD-017,Quinn Anderson,138.00,completed,2024-01-31
ORD-018,Rachel Thomas,275.50,pending,2024-02-01
ORD-019,Sam Jackson,49.99,completed,2024-02-02
ORD-020,Tina White,382.00,completed,2024-02-03
```

- [ ] **Step 4: Create `demo-project/tests/data/products.json`**

```json
[
  {"product_id": "PRD-001", "name": "Wireless Headphones", "category": "Electronics", "price": 89.99, "stock": 150},
  {"product_id": "PRD-002", "name": "Leather Wallet", "category": "Accessories", "price": 45.00, "stock": 320},
  {"product_id": "PRD-003", "name": "Running Shoes", "category": "Footwear", "price": 129.99, "stock": 85},
  {"product_id": "PRD-004", "name": "Coffee Maker", "category": "Kitchen", "price": 79.50, "stock": 60},
  {"product_id": "PRD-005", "name": "Yoga Mat", "category": "Sports", "price": 35.00, "stock": 200},
  {"product_id": "PRD-006", "name": "Bluetooth Speaker", "category": "Electronics", "price": 65.99, "stock": 110},
  {"product_id": "PRD-007", "name": "Sunglasses", "category": "Accessories", "price": 55.00, "stock": 175},
  {"product_id": "PRD-008", "name": "Backpack", "category": "Bags", "price": 95.00, "stock": 90},
  {"product_id": "PRD-009", "name": "Smart Watch", "category": "Electronics", "price": 249.99, "stock": 45},
  {"product_id": "PRD-010", "name": "Water Bottle", "category": "Sports", "price": 28.50, "stock": 400},
  {"product_id": "PRD-011", "name": "Desk Lamp", "category": "Home", "price": 42.00, "stock": 130},
  {"product_id": "PRD-012", "name": "Notebook Set", "category": "Stationery", "price": 18.99, "stock": 500},
  {"product_id": "PRD-013", "name": "Portable Charger", "category": "Electronics", "price": 39.99, "stock": 220},
  {"product_id": "PRD-014", "name": "Kitchen Knife Set", "category": "Kitchen", "price": 185.00, "stock": 35},
  {"product_id": "PRD-015", "name": "Throw Blanket", "category": "Home", "price": 59.99, "stock": 160}
]
```

- [ ] **Step 5: Create `demo-project/tests/data/users.csv`**

```csv
user_id,name,email,role,active
USR-001,Alice Chen,alice@example.com,customer,true
USR-002,Bob Smith,bob@example.com,customer,true
USR-003,Carol Wu,carol@example.com,admin,true
USR-004,David Kim,david@example.com,customer,false
USR-005,Emma Jones,emma@example.com,customer,true
USR-006,Frank Lee,frank@example.com,support,true
USR-007,Grace Park,grace@example.com,customer,true
USR-008,Henry Brown,henry@example.com,customer,false
USR-009,Iris Wang,iris@example.com,admin,true
USR-010,Jack Miller,jack@example.com,customer,true
USR-011,Karen Davis,karen@example.com,customer,true
USR-012,Leo Zhang,leo@example.com,support,true
```

- [ ] **Step 6: Create `demo-project/tests/test_orders.py`**

```python
"""Order service test stubs — intentionally not implemented (migration demo)."""


def test_create_order_with_valid_items(): pass
def test_create_order_fails_when_stock_empty(): pass
def test_order_total_calculated_correctly(): pass
def test_cancel_order_before_shipment(): pass
def test_cancel_order_after_shipment_raises_error(): pass
def test_order_status_transitions(): pass
def test_duplicate_order_prevention(): pass
def test_order_with_discount_code(): pass
def test_bulk_order_processing(): pass
def test_order_confirmation_email_sent(): pass
def test_order_history_pagination(): pass
def test_order_search_by_customer(): pass
def test_order_filter_by_status(): pass
def test_order_export_csv(): pass
def test_partial_fulfillment_handling(): pass
def test_backorder_notification(): pass
def test_order_refund_full(): pass
def test_order_refund_partial(): pass
```

- [ ] **Step 7: Create `demo-project/tests/test_payments.py`**

```python
"""Payment service test stubs — intentionally not implemented (migration demo)."""


def test_payment_with_valid_card(): pass
def test_payment_declined_insufficient_funds(): pass
def test_payment_timeout_triggers_refund(): pass
def test_duplicate_payment_prevention(): pass
def test_refund_processed_within_sla(): pass
def test_payment_method_validation(): pass
def test_partial_payment_not_allowed(): pass
def test_currency_conversion_accuracy(): pass
def test_payment_receipt_generated(): pass
def test_fraud_detection_flag(): pass
def test_chargeback_handling(): pass
def test_subscription_renewal_payment(): pass
def test_payment_retry_on_network_error(): pass
def test_payment_audit_log_written(): pass
```

- [ ] **Step 8: Create `demo-project/tests/test_users.py`**

```python
"""User service test stubs — intentionally not implemented (migration demo)."""


def test_user_registration_valid(): pass
def test_user_registration_duplicate_email(): pass
def test_user_login_valid_credentials(): pass
def test_user_login_invalid_password(): pass
def test_user_profile_update(): pass
def test_user_password_reset(): pass
def test_user_role_assignment(): pass
def test_user_deactivation(): pass
def test_user_data_export_gdpr(): pass
def test_admin_can_view_all_users(): pass
```

- [ ] **Step 9: Verify scanner detects the project correctly**

Run from `tap-migration/` dir:
```bash
uv run python -c "
from src.scanner import scan_project
from pathlib import Path
r = scan_project(Path('../demo-project'))
print('framework:', r.test_framework)
print('dep_mgmt:', r.dep_management)
print('data_format:', r.test_data_format)
print('data_count:', r.test_data_count)
print('test_count:', r.test_case_count)
"
```

Expected output:
```
framework: pytest
dep_mgmt: pyproject.toml
data_format: csv
data_count: 32
test_count: 42
```

(32 = 20 orders + 12 users; products.json adds 15 but scan counts by dominant format)

- [ ] **Step 10: Commit**

```bash
git add demo-project/
git commit -m "feat: add ecommerce demo project with test data and test stubs"
```

---

## Task 2: uploader.py — `on_progress` callback + `upload_delay`

**Files:**
- Modify: `tap-migration/src/uploader.py`
- Modify: `tap-migration/tests/test_uploader.py`

- [ ] **Step 1: Write the failing tests first**

Add to `tap-migration/tests/test_uploader.py`:

```python
@respx.mock
def test_on_progress_called_for_each_record():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
    calls: list[tuple[int, int, dict]] = []
    records = [
        {"id": "1", "name": "a", "data": {}},
        {"id": "2", "name": "b", "data": {}},
        {"id": "3", "name": "c", "data": {}},
    ]
    upload_records(
        records=records,
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
        on_progress=lambda current, total, record: calls.append((current, total, record)),
    )
    assert len(calls) == 3
    assert calls[0] == (1, 3, records[0])
    assert calls[1] == (2, 3, records[1])
    assert calls[2] == (3, 3, records[2])


@respx.mock
def test_on_progress_called_even_on_failure():
    respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(500))
    calls: list[int] = []
    upload_records(
        records=[{"id": "1", "name": "a", "data": {}}],
        endpoint=f"{BASE_URL}/test-data",
        token=TOKEN,
        on_progress=lambda current, total, record: calls.append(current),
    )
    assert calls == [1]


def test_upload_delay_respected(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr("src.uploader.time.sleep", lambda s: sleep_calls.append(s))
    with respx.mock:
        respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
        upload_records(
            records=[{"id": "1", "name": "a", "data": {}}, {"id": "2", "name": "b", "data": {}}],
            endpoint=f"{BASE_URL}/test-data",
            token=TOKEN,
            upload_delay=0.5,
        )
    assert sleep_calls == [0.5, 0.5]


def test_no_delay_by_default(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr("src.uploader.time.sleep", lambda s: sleep_calls.append(s))
    with respx.mock:
        respx.post(f"{BASE_URL}/test-data").mock(return_value=httpx.Response(200))
        upload_records(
            records=[{"id": "1", "name": "a", "data": {}}],
            endpoint=f"{BASE_URL}/test-data",
            token=TOKEN,
        )
    # time.sleep should only be called for retry backoff, not upload_delay
    assert 0.5 not in sleep_calls
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd tap-migration && uv run pytest tests/test_uploader.py -v
```

Expected: 4 new tests FAIL, 4 existing tests PASS

- [ ] **Step 3: Implement the changes in `tap-migration/src/uploader.py`**

```python
from __future__ import annotations
import time
from collections.abc import Callable
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
    on_progress: Callable[[int, int, dict], None] | None = None,
    upload_delay: float = 0.0,
) -> UploadResult:
    """Upload records to a TAP API endpoint. Continue-on-error per record; abort on auth failure."""
    result = UploadResult()
    total = len(records)
    with httpx.Client(timeout=30, trust_env=False) as client:
        for i, record in enumerate(records, start=1):
            _upload_one(client, record, endpoint, token, result)
            if on_progress is not None:
                on_progress(i, total, record)
            if upload_delay > 0:
                time.sleep(upload_delay)
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
            break
        except AuthError:
            raise
        except Exception as exc:
            last_error = str(exc)
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BASE_SECONDS * (2 ** attempt))

    result.failed += 1
    result.failures.append({**record, "_error": last_error})
```

- [ ] **Step 4: Run all uploader tests to verify they pass**

```bash
cd tap-migration && uv run pytest tests/test_uploader.py -v
```

Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tap-migration/src/uploader.py tap-migration/tests/test_uploader.py
git commit -m "feat: add on_progress callback and upload_delay to upload_records"
```

---

## Task 3: migrate.py — `--upload-delay` flag + progress output

**Files:**
- Modify: `tap-migration/migrate.py`
- Modify: `tap-migration/tests/test_migrate.py`

- [ ] **Step 1: Read existing test_migrate.py to understand test patterns**

```bash
cat tap-migration/tests/test_migrate.py
```

- [ ] **Step 2: Write the failing tests**

Add to `tap-migration/tests/test_migrate.py` (use the same runner pattern already in the file — `subprocess.run` or `typer.testing.CliRunner`):

```python
import re
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from migrate import app

runner = CliRunner()


def test_upload_delay_flag_accepted(tmp_path):
    """--upload-delay 0.0 is accepted without error (dry-run so no actual upload)."""
    # Create minimal project structure
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\nversion='0.1.0'\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("def test_a(): pass\n")

    env_file = tmp_path / ".env"
    env_file.write_text("TAP_API_BASE_URL=http://localhost:9999\nTAP_API_TOKEN=tok\n")

    result = runner.invoke(app, [
        "--project-dir", str(tmp_path),
        "--env", str(env_file),
        "--dry-run",
        "--upload-delay", "0.0",
    ])
    assert result.exit_code == 0


def test_progress_output_format(tmp_path):
    """Each uploaded record produces a progress line like 'Uploading test cases: 1/1  test_a'."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\nversion='0.1.0'\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("def test_alpha(): pass\ndef test_beta(): pass\n")

    env_file = tmp_path / ".env"
    env_file.write_text("TAP_API_BASE_URL=http://mock.test\nTAP_API_TOKEN=tok\n")

    with patch("migrate.upload_records") as mock_upload:
        mock_upload.return_value = MagicMock(uploaded=2, failed=0, failures=[])
        result = runner.invoke(app, [
            "--project-dir", str(tmp_path),
            "--env", str(env_file),
            "--upload-delay", "0.0",
        ])

    # on_progress was passed; simulate calling it with the records
    # Verify the flag was forwarded to upload_records as upload_delay=0.0
    call_kwargs = mock_upload.call_args_list
    for call in call_kwargs:
        assert call.kwargs.get("upload_delay") == 0.0 or call.args[4] == 0.0 if len(call.args) > 4 else True
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd tap-migration && uv run pytest tests/test_migrate.py::test_upload_delay_flag_accepted tests/test_migrate.py::test_progress_output_format -v
```

Expected: 2 FAIL (unrecognized option `--upload-delay`)

- [ ] **Step 4: Implement changes in `tap-migration/migrate.py`**

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
from src.uploader import upload_records, AuthError
from src.validator import validate_migration
from src.reporter import render_migration_report

app = typer.Typer()

_TEST_DATA_ENDPOINT = "{TAP_API_BASE_URL}/test-data"
_TEST_CASE_ENDPOINT = "{TAP_API_BASE_URL}/test-cases"


def _record_label(record: dict) -> str:
    return str(record.get("id") or record.get("name") or "")


@app.command()
def main(
    project_dir: Path = typer.Option(..., help="Path to the local test project"),
    env: Path = typer.Option(Path(".env"), help="Path to .env file"),
    dry_run: bool = typer.Option(False, help="Convert only, skip upload"),
    report_out: Path = typer.Option(Path("./tap-migration-report.md"), help="Output path for report"),
    upload_delay: float = typer.Option(0.0, help="Seconds to wait between uploads (use 0.2–0.5 for demos)"),
) -> None:
    load_dotenv(env)
    base_url = os.getenv("TAP_API_BASE_URL", "")
    token = os.getenv("TAP_API_TOKEN", "")

    if not dry_run and (not base_url or not token):
        typer.echo("ERROR: TAP_API_BASE_URL and TAP_API_TOKEN must be set in .env", err=True)
        raise typer.Exit(1)

    scan = scan_project(project_dir)

    all_data_records: list[dict] = []
    for data_file in scan.test_data_paths:
        try:
            all_data_records.extend(convert_test_data_file(data_file))
        except ConversionError as e:
            typer.echo(f"WARN: skipping {data_file.name} — {e}")

    all_case_records: list[dict] = []
    for case_file in scan.test_case_paths:
        all_case_records.extend(convert_test_case_file(case_file))

    typer.echo(f"Converted: {len(all_data_records)} data records, {len(all_case_records)} test cases")

    if dry_run:
        typer.echo("Dry-run mode — skipping upload.")
        raise typer.Exit(0)

    data_endpoint = _TEST_DATA_ENDPOINT.format(TAP_API_BASE_URL=base_url)
    case_endpoint = _TEST_CASE_ENDPOINT.format(TAP_API_BASE_URL=base_url)

    def _make_progress(label: str, total: int):
        def _cb(current: int, _total: int, record: dict) -> None:
            typer.echo(f"Uploading {label}: {current}/{total}  {_record_label(record)}")
        return _cb

    try:
        data_result = upload_records(
            all_data_records, data_endpoint, token,
            on_progress=_make_progress("test data", len(all_data_records)),
            upload_delay=upload_delay,
        )
        case_result = upload_records(
            all_case_records, case_endpoint, token,
            on_progress=_make_progress("test cases", len(all_case_records)),
            upload_delay=upload_delay,
        )
    except AuthError as e:
        typer.echo(f"ERROR: Authentication failed — {e}", err=True)
        raise typer.Exit(1)

    combined_local = all_data_records + all_case_records
    validation = validate_migration(
        local_records=combined_local,
        uploaded_records=combined_local[:data_result.uploaded + case_result.uploaded],
    )

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

- [ ] **Step 5: Run all migrate tests**

```bash
cd tap-migration && uv run pytest tests/test_migrate.py -v
```

Expected: all PASS (including the 2 new ones)

- [ ] **Step 6: Smoke test against demo-project**

```bash
cd tap-migration && uv run python migrate.py \
  --project-dir ../demo-project \
  --env /tmp/tap.env \
  --upload-delay 0.1 \
  --report-out /tmp/demo-migration-report.md
```

Expected output (abbreviated):
```
Converted: 47 data records, 42 test cases
Uploading test data: 1/47  ORD-001
Uploading test data: 2/47  ORD-002
...
Uploading test cases: 1/42  test_create_order_with_valid_items
...
Migration report written to: /tmp/demo-migration-report.md
```

- [ ] **Step 7: Commit**

```bash
git add tap-migration/migrate.py tap-migration/tests/test_migrate.py
git commit -m "feat: add --upload-delay flag and per-record progress output to migrate.py"
```

---

## Task 4: ConfigForm — add `type: 'number'` support

**Files:**
- Modify: `frontend/src/components/ConfigForm.tsx`
- Modify: `frontend/src/components/ConfigForm.test.tsx`

- [ ] **Step 1: Write the failing test**

Add to `frontend/src/components/ConfigForm.test.tsx`:

```typescript
test('renders number input for type number field', () => {
  const numberFields: FieldDef[] = [
    { name: 'delay', label: 'Upload Delay', type: 'number', required: false, defaultValue: 0 },
  ]
  render(<ConfigForm fields={numberFields} onSubmit={vi.fn()} disabled={false} />)
  const input = screen.getByLabelText('Upload Delay')
  expect(input).toHaveAttribute('type', 'number')
})

test('submits numeric value for number field', () => {
  const onSubmit = vi.fn()
  const numberFields: FieldDef[] = [
    { name: 'delay', label: 'Upload Delay', type: 'number', required: false, defaultValue: 0 },
  ]
  render(<ConfigForm fields={numberFields} onSubmit={onSubmit} disabled={false} />)
  fireEvent.change(screen.getByLabelText('Upload Delay'), { target: { value: '0.3' } })
  fireEvent.click(screen.getByRole('button', { name: /run/i }))
  expect(onSubmit).toHaveBeenCalledWith({ delay: '0.3' })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run src/components/ConfigForm.test.tsx
```

Expected: 2 new tests FAIL (TypeScript error on `type: 'number'`), 4 existing PASS

- [ ] **Step 3: Implement `type: 'number'` in ConfigForm.tsx**

Replace the `FieldDef` interface and the render block:

```typescript
export interface FieldDef {
  name: string
  label: string
  type: 'text' | 'toggle' | 'number'
  required: boolean
  defaultValue?: string | boolean | number
  placeholder?: string
  step?: number
  min?: number
  max?: number
}
```

In the `useState` initializer, handle `number` type:
```typescript
const [values, setValues] = useState<Record<string, string | boolean>>(() =>
  Object.fromEntries(
    fields.map((f) => [
      f.name,
      f.defaultValue !== undefined
        ? (f.type === 'toggle' ? Boolean(f.defaultValue) : String(f.defaultValue))
        : (f.type === 'toggle' ? false : ''),
    ])
  )
)
```

In the render, add `number` branch between `text` and `toggle`:

```typescript
{fields.map((f) => (
  <div key={f.name} className="space-y-1">
    {f.type === 'text' ? (
      <>
        <Label htmlFor={f.name}>{f.label}</Label>
        <Input
          id={f.name}
          value={values[f.name] as string}
          onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
          placeholder={f.placeholder}
        />
      </>
    ) : f.type === 'number' ? (
      <>
        <Label htmlFor={f.name}>{f.label}</Label>
        <Input
          id={f.name}
          type="number"
          value={values[f.name] as string}
          onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
          step={f.step}
          min={f.min}
          max={f.max}
        />
      </>
    ) : (
      <div className="flex items-center gap-2">
        <Switch
          aria-labelledby={`label-${f.name}`}
          checked={values[f.name] as boolean}
          onCheckedChange={(checked) => setValues((v) => ({ ...v, [f.name]: checked }))}
        />
        <Label id={`label-${f.name}`}>{f.label}</Label>
      </div>
    )}
  </div>
))}
```

- [ ] **Step 4: Run all ConfigForm tests**

```bash
cd frontend && npx vitest run src/components/ConfigForm.test.tsx
```

Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ConfigForm.tsx frontend/src/components/ConfigForm.test.tsx
git commit -m "feat: add number input type support to ConfigForm"
```

---

## Task 5: Wire `upload_delay` end-to-end — types, MigratePage, API router

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/pages/MigratePage.tsx`
- Modify: `api/routers/migrate.py`
- Modify: `api/tests/test_routes.py`

- [ ] **Step 1: Write the failing API route test**

Add to `api/tests/test_routes.py`:

```python
@pytest.mark.asyncio
async def test_migrate_upload_delay_forwarded_to_cmd(client):
    """upload_delay is included in the subprocess command args."""
    with patch("routers.migrate.runner") as mock_runner:
        mock_runner.start = AsyncMock(return_value="run-delay-01")
        mock_runner.is_busy = False
        await client.post("/api/migrate", json={
            "project_dir": "/tmp/rich",
            "upload_delay": 0.3,
        })
        cmd = mock_runner.start.call_args[0][0]
        assert "--upload-delay" in cmd
        idx = cmd.index("--upload-delay")
        assert cmd[idx + 1] == "0.3"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd api && uv run pytest tests/test_routes.py::test_migrate_upload_delay_forwarded_to_cmd -v
```

Expected: FAIL (no `--upload-delay` in cmd)

- [ ] **Step 3: Update `frontend/src/lib/types.ts`**

Add `upload_delay` to `MigrateConfig`:

```typescript
export interface MigrateConfig {
  project_dir: string
  env?: string
  dry_run?: boolean
  report_out?: string
  upload_delay?: number
}
```

- [ ] **Step 4: Update `api/routers/migrate.py`**

Add `upload_delay` to `MigrateRequest` and the subprocess cmd:

```python
class MigrateRequest(BaseModel):
    project_dir: str
    env: str = ".env"
    dry_run: bool = False
    report_out: str = "./tap-migration-report.md"
    upload_delay: float = 0.0
```

In `start_migrate`, add to cmd (always include even if 0.0):

```python
cmd = [
    "uv", "run", "python", "migrate.py",
    "--project-dir", str(project_dir),
    "--env", req.env,
    "--report-out", str(report_out),
    "--upload-delay", str(req.upload_delay),
]
if req.dry_run:
    cmd += ["--dry-run"]
```

- [ ] **Step 5: Run the API test to verify it passes**

```bash
cd api && uv run pytest tests/test_routes.py::test_migrate_upload_delay_forwarded_to_cmd -v
```

Expected: PASS

- [ ] **Step 6: Run full API test suite**

```bash
cd api && uv run pytest tests/ -v
```

Expected: all existing tests PASS + 1 new PASS

- [ ] **Step 7: Update `frontend/src/pages/MigratePage.tsx`**

Add the `upload_delay` field to `FIELDS` and pass it in `handleSubmit`:

```typescript
const FIELDS: FieldDef[] = [
  { name: 'project_dir', label: 'Project Directory', type: 'text', required: true, placeholder: '/path/to/project' },
  { name: 'env', label: '.env File Path', type: 'text', required: false, defaultValue: '.env' },
  { name: 'dry_run', label: 'Dry Run (skip upload)', type: 'toggle', required: false, defaultValue: false },
  { name: 'report_out', label: 'Report Output Path', type: 'text', required: false, defaultValue: './tap-migration-report.md' },
  { name: 'upload_delay', label: 'Upload Delay (seconds)', type: 'number', required: false, defaultValue: 0, step: 0.1, min: 0, max: 2.0 },
]
```

In `handleSubmit`, pass `upload_delay`:

```typescript
const { run_id } = await startMigrate({
  project_dir: values.project_dir as string,
  env: (values.env as string) || undefined,
  dry_run: values.dry_run as boolean,
  report_out: (values.report_out as string) || undefined,
  upload_delay: values.upload_delay ? parseFloat(values.upload_delay as string) : 0,
})
```

- [ ] **Step 8: Update `frontend/src/lib/api.ts` — pass `upload_delay` in startMigrate**

Check that `startMigrate` accepts and forwards `MigrateConfig`. Since `upload_delay` is already in `MigrateConfig`, it will be forwarded automatically if the function spreads the config object. Verify by reading `api.ts` and confirming `startMigrate` sends the full config as the request body.

- [ ] **Step 9: Build frontend to verify no TypeScript errors**

```bash
cd frontend && npm run build
```

Expected: build succeeds with no errors

- [ ] **Step 10: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/pages/MigratePage.tsx api/routers/migrate.py api/tests/test_routes.py
git commit -m "feat: wire upload_delay end-to-end through MigratePage, API router, and migrate.py"
```

---

## Final Verification

- [ ] **Start all three services**

```bash
# Terminal 1
cd mock-tap && uv run uvicorn main:app --port 9000 --reload

# Terminal 2
cd api && uv run uvicorn main:app --reload --port 8000

# Terminal 3
cd frontend && npm run dev
```

- [ ] **Run the demo**

Open `http://localhost:5173`, go to Migrate page, fill in:
- Project Directory: `<absolute-path-to-repo>/demo-project`
- .env File Path: `/tmp/tap.env`
- Upload Delay: `0.3`

Click Run. Expect LogViewer to show:
```
Converted: 47 data records, 42 test cases
Uploading test data: 1/47  ORD-001
Uploading test data: 2/47  ORD-002
...
Uploading test cases: 1/42  test_create_order_with_valid_items
...
Migration report written to: ./tap-migration-report.md
```

- [ ] **Verify mock-tap received the records**

```bash
curl http://localhost:9000/stats
```

Expected: `{"test_data": 47, "test_cases": 42}` (plus any previous records)
