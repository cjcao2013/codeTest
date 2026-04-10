# TAP Migration Demo Enhancement — Design Spec

**Date:** 2026-04-10
**Status:** Draft
**Scope:** Replace the bare `rich` test project with a demo-friendly e-commerce test suite, and add per-record progress logging + configurable upload delay to `migrate.py`.

---

## Background

The current demo has two problems:

1. **No test data**: The `rich` library has only Python test functions — no CSV/JSON test data files. The migration report shows `0 data records`, which looks unconvincing.
2. **Instant migration**: 717 records upload silently with a single progress line. The LogViewer shows nothing interesting, killing the demo effect.

This spec addresses both by creating a purpose-built demo project and enhancing the migration output.

---

## Part 1: Demo Project (`demo-project/`)

A fictional **e-commerce order service** test suite. Business-domain names make the content legible to non-engineers.

### Directory Structure

```
demo-project/
├── pyproject.toml
└── tests/
    ├── test_orders.py        # 18 test functions
    ├── test_payments.py      # 14 test functions
    ├── test_users.py         # 10 test functions
    └── data/
        ├── orders.csv        # 20 rows (order_id, customer_name, amount, status, created_at)
        ├── products.json     # 15 items (product_id, name, category, price, stock)
        └── users.csv         # 12 rows (user_id, name, email, role, active)
```

**Totals:** 42 test functions + 47 test data records

### Test Function Names (representative sample)

`test_orders.py`:
- `test_create_order_with_valid_items`
- `test_create_order_fails_when_stock_empty`
- `test_order_total_calculated_correctly`
- `test_cancel_order_before_shipment`
- `test_cancel_order_after_shipment_raises_error`
- `test_order_status_transitions`
- `test_duplicate_order_prevention`
- `test_order_with_discount_code`
- `test_bulk_order_processing`
- `test_order_confirmation_email_sent`
- `test_order_history_pagination`
- `test_order_search_by_customer`
- `test_order_filter_by_status`
- `test_order_export_csv`
- `test_partial_fulfillment_handling`
- `test_backorder_notification`
- `test_order_refund_full`
- `test_order_refund_partial`

`test_payments.py`:
- `test_payment_with_valid_card`
- `test_payment_declined_insufficient_funds`
- `test_payment_timeout_triggers_refund`
- `test_duplicate_payment_prevention`
- `test_refund_processed_within_sla`
- `test_payment_method_validation`
- `test_partial_payment_not_allowed`
- `test_currency_conversion_accuracy`
- `test_payment_receipt_generated`
- `test_fraud_detection_flag`
- `test_chargeback_handling`
- `test_subscription_renewal_payment`
- `test_payment_retry_on_network_error`
- `test_payment_audit_log_written`

`test_users.py`:
- `test_user_registration_valid`
- `test_user_registration_duplicate_email`
- `test_user_login_valid_credentials`
- `test_user_login_invalid_password`
- `test_user_profile_update`
- `test_user_password_reset`
- `test_user_role_assignment`
- `test_user_deactivation`
- `test_user_data_export_gdpr`
- `test_admin_can_view_all_users`

### Test Data (sample rows)

`orders.csv`:
```
order_id,customer_name,amount,status,created_at
ORD-001,Alice Chen,128.50,completed,2024-01-15
ORD-002,Bob Smith,45.00,pending,2024-01-16
...
```

`products.json`:
```json
[
  {"product_id": "PRD-001", "name": "Wireless Headphones", "category": "Electronics", "price": 89.99, "stock": 150},
  ...
]
```

`users.csv`:
```
user_id,name,email,role,active
USR-001,Alice Chen,alice@example.com,customer,true
...
```

### `pyproject.toml`

```toml
[project]
name = "ecommerce-order-service-tests"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## Part 2: Migration Progress Enhancement

### 2a. `src/uploader.py` — Progress callback

Add an optional `on_progress` callback to `upload_records`:

```python
def upload_records(
    records: list[dict],
    endpoint: str,
    token: str,
    on_progress: Callable[[int, int, dict], None] | None = None,
    upload_delay: float = 0.0,
) -> UploadResult:
```

- `on_progress(current, total, record)` — called after each successful or failed upload
- `upload_delay` — seconds to sleep after each record (default `0.0`)
- Existing callers with no callback continue to work unchanged

### 2b. `migrate.py` — Progress output + `--upload-delay` flag

New CLI flag:
```
--upload-delay FLOAT   Seconds to wait between uploads (default: 0.0). Use 0.2–0.5 for demos.
```

Progress output format (printed via `typer.echo`):
```
Uploading test data: 1/47  ORD-001
Uploading test data: 2/47  ORD-002
...
Uploading test data: 47/47  USR-012
Uploading test cases: 1/42  test_create_order_with_valid_items
Uploading test cases: 2/42  test_payment_declined_insufficient_funds
...
Uploading test cases: 42/42  test_admin_can_view_all_users
```

Record label is derived from: `record.get("id") or record.get("name") or ""`.

### 2c. Frontend `MigratePage` — `--upload-delay` field

Add one new optional field to the Migrate form:

| Flag | Type | Default | UI Control |
|------|------|---------|------------|
| `--upload-delay` | float | `0.0` | Number input (step 0.1, min 0, max 2.0) |

---

## Affected Files

| Action | File |
|--------|------|
| Create | `demo-project/pyproject.toml` |
| Create | `demo-project/tests/test_orders.py` |
| Create | `demo-project/tests/test_payments.py` |
| Create | `demo-project/tests/test_users.py` |
| Create | `demo-project/tests/data/orders.csv` |
| Create | `demo-project/tests/data/products.json` |
| Create | `demo-project/tests/data/users.csv` |
| Modify | `tap-migration/src/uploader.py` |
| Modify | `tap-migration/migrate.py` |
| Modify | `frontend/src/pages/MigratePage.tsx` |

---

## Demo Flow (after this change)

1. Start mock-tap (`localhost:9000`), API (`localhost:8000`), frontend (`localhost:5173`)
2. Open Migrate page, fill in:
   - `--project-dir`: `<path>/demo-project`
   - `--env`: path to `.env` with `TAP_API_BASE_URL=http://localhost:9000`
   - `--upload-delay`: `0.3`
3. Click Run → LogViewer shows:
   - Assessment scan summary
   - Uploading test data: 1/47 ... 47/47 (smooth scroll)
   - Uploading test cases: 1/42 ... 42/42
   - Migration report rendered below

Total demo time at 0.3s delay: ~27 seconds of live scrolling output.

---

## Out of Scope

- Changes to `assess.py` or the assess workflow
- Changes to mock-tap API endpoints
- Authentication or multi-user support
- Docker packaging
