---
applyTo: "**/*migration*,**/*tap*,**/assess*,**/migrate*"
---

# TAP Data Migration

## Overview

This skill guides migration of test data and test cases into TAP (Test Automation Platform).

**Two-phase model:**
- **Phase 1 — Assessment:** Scan the project directory, auto-detect test data/case format and structure, prompt only for gaps, output a feasibility report with Go/Pending/No-go decision.
- **Phase 2 — Execution:** Run Python + uv migration scripts to convert, upload, validate, and report.

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

The migration scripts live in `tap-migration/` within this repo. Copy or reference them from the target project directory before running.
