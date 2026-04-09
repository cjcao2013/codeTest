# TAP Data Migration Skill — Design Spec

Date: 2026-04-09
Status: Draft

---

## Overview

A new GitHub Copilot CLI skill (`tap-data-migration`) that guides users through migrating test data and test cases from local projects into the TAP (Test Automation Platform). The skill covers the full lifecycle: feasibility assessment → script generation → execution → validation → report.

**Scope of this version:**
- Test data and test case migration only
- Pipeline migration is deferred to v2

---

## Architecture

Two-phase design with a decision gate between phases.

```
Phase 1: Assessment
  └── Collect project info (test data/case format, project structure)
  └── Output: Feasibility report with risk level + complexity score
  └── Decision gate: Go / Pending / No-go

Phase 2: Execution (Go only)
  └── Generate Python + uv migration scripts
  └── Convert local formats → TAP-compatible formats
  └── Upload via TAP API
  └── Validate (count + content spot-check)
  └── Output: Migration report
```

### User Paths

| Role | Entry | Exit | Output |
|------|-------|------|--------|
| Tech Lead | Phase 1 | Decision gate | Feasibility report |
| Engineer | Phase 1 | Phase 2 complete | Report + scripts + migration report |

---

## Phase 1: Assessment

### Assessment Strategy: Scan-First, Ask-Second

`assess.py` automatically scans `--project-dir` first to derive as much information as possible. Only when a dimension cannot be determined from the file system does it prompt the user.

**Auto-detected (no user input required):**
- Test framework (detect `pytest.ini`, `pyproject.toml [tool.pytest]`, `unittest` imports)
- Dependency management style (`requirements.txt` vs `pyproject.toml`)
- Test data files: location, format (by extension), file count
- Test case files: location, format (by extension), count

**Falls back to user prompt when:**
- Test data is stored in a database or external tool (cannot be scanned)
- Directory structure is non-standard and framework cannot be inferred
- Test cases are managed in an external tool (e.g., Jira, TestRail)

### Information Collected

**Test Data / Case Dimension:**

| Dimension | Source | Fallback Prompt |
|-----------|--------|----------------|
| Test data location | Auto-scan `--project-dir` | "Where is your test data stored?" |
| Test data format | Auto-detect by file extension | "What format is your test data?" |
| Test data volume | Auto-count files/records | "Approximately how many records?" |
| Test case location | Auto-scan for test files | "Where are your test cases stored?" |
| Test case count | Auto-count test functions | "How many test cases approximately?" |

**Project Structure Dimension:**

| Dimension | Source | Fallback Prompt |
|-----------|--------|----------------|
| Test framework | Auto-detect config files | "Which test framework do you use?" |
| Dependency management | Auto-detect `requirements.txt` / `pyproject.toml` | "How do you manage dependencies?" |
| Directory conventions | Auto-scan structure | "Any special directory conventions?" |

### Feasibility Report Format

```markdown
# TAP Migration Feasibility Report
Project: [name] | Date: [YYYY-MM-DD]

## Complexity Score: 🟢 Low / 🟡 Medium / 🔴 High

| Dimension | Status | Notes |
|-----------|--------|-------|
| Test data format | ✅ Directly supported / ⚠️ Needs conversion / ❌ Unsupported | |
| Test case format | ✅ / ⚠️ / ❌ | |
| Data volume | ✅ Small / ⚠️ Medium / 🔴 Large | |
| Project structure | ✅ Standard / ⚠️ Needs adaptation | |

## Risk Items
- [risk 1]
- [risk 2]

## Recommendation
✅ Proceed with migration / ⚠️ Resolve the following before proceeding / ❌ Not recommended at this time

## Pending (confirm with TAP team)
- [ ] TAP supported test data formats: [TBD]
- [ ] TAP test case import API: [TBD]
```

### Decision Gate

| Result | Meaning | Next Step |
|--------|---------|-----------|
| 🟢 Go | Low risk, formats compatible | Proceed to Phase 2 |
| 🟡 Pending | Some items need TAP team confirmation | Resolve open questions first |
| 🔴 No-go | Blockers identified | Provide remediation guidance |

**Scoring rubric:**
- Any dimension marked ❌ → **No-go**
- Two or more dimensions marked ⚠️ with no ❌ → **Pending**
- All dimensions ✅, or at most one ⚠️ → **Go**

**Volume thresholds (default, overridable via `--volume-threshold`):**
- Small (✅): < 500 records / files
- Medium (⚠️): 500 – 5,000 records / files
- Large (🔴): > 5,000 records / files

---

## Phase 2: Execution

### CLI Interface

The skill generates a project with two scripts:

```bash
# Phase 1 — scan project, prompt for gaps, output feasibility report
uv run assess.py --project-dir ./my-tests

# Phase 2 — full migration: convert + upload + validate + report
uv run migrate.py --project-dir ./my-tests --env .env
```

**`assess.py` flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--project-dir` | Yes | Path to the local test project to scan |
| `--report-out` | No | Output path for feasibility report (default: `./tap-assessment-report.md`) |
| `--volume-threshold` | No | Override volume thresholds as `small:N,medium:N` (default: `500,5000`) |

**`migrate.py` flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--project-dir` | Yes | Path to the local test project |
| `--env` | No | Path to `.env` file (default: `.env`) |
| `--dry-run` | No | Run conversion only, skip upload |
| `--report-out` | No | Output path for migration report (default: `./tap-migration-report.md`) |

---

### Generated Script Structure

```
tap-migration/
├── pyproject.toml          # uv dependency management
├── .env.example            # TAP API credential placeholders
├── assess.py               # Phase 1 entry: scan project + generate feasibility report
├── migrate.py              # Phase 2 entry: convert + upload + validate + report
└── src/
    ├── converter.py        # Format conversion (local → TAP format)
    ├── uploader.py         # TAP API upload calls
    ├── validator.py        # Pre/post migration comparison
    └── reporter.py         # Migration report generation
```

### Execution Flow

```
uv run migrate.py --project-dir ./my-tests
  │
  ├── 1. Read local test data/cases from --project-dir
  ├── 2. Convert formats (converter.py)
  │       └── Output: TAP-compatible payload (see Payload Schema)
  ├── 3. Upload to TAP (uploader.py)
  │       └── POST [TAP_API_BASE_URL]/test-data    ← TBD (fill TAP_API_BASE_URL in .env)
  │           POST [TAP_API_BASE_URL]/test-cases   ← TBD
  │           Auth: Bearer $TAP_API_TOKEN          ← TBD (fill in .env)
  ├── 4. Validate (validator.py)
  │       └── Compare: local count vs TAP uploaded count
  │           Spot-check: random 10% sample (min 5 records),
  │           comparing id, name, and one payload field
  └── 5. Generate report (reporter.py)
```

### Environment Variables (`.env.example`)

```
TAP_API_BASE_URL=https://tap.example.com/api   # TBD — fill with TAP team
TAP_API_TOKEN=your-token-here                   # TBD — fill with TAP team
TAP_PROJECT_ID=your-project-id                  # TBD — confirm with TAP team whether needed as path segment, query param, or request body field
```

### TAP Payload Schema (Placeholder)

Converter output must conform to these structures (fill in with TAP team):

**Test data upload payload:**
```json
{
  "id": "TBD",
  "name": "TBD",
  "data": {}
}
```

**Test case upload payload:**
```json
{
  "id": "TBD",
  "name": "TBD",
  "steps": []
}
```

---

### Error Handling Policy

| Scenario | Behavior |
|----------|----------|
| Single record conversion fails | Log error, continue to next record (continue-on-error) |
| Single record upload fails | Log error with record ID, continue to next record |
| Auth failure (401/403) | Abort immediately, report auth error |
| Network timeout | Retry up to 3 times with exponential backoff, then log as failed |
| All records fail | Abort after batch, surface as No-go in report |

Failed records are collected and included in the migration report's Failure Details section.

---

### TAP API Placeholders

| Purpose | Placeholder |
|---------|-------------|
| Upload test data | `POST [TAP_API_BASE_URL]/test-data` |
| Upload test cases | `POST [TAP_API_BASE_URL]/test-cases` |
| Query upload status | `GET [TAP_API_BASE_URL]/...` |
| Auth method | `Bearer Token / API Key / TBD` |

### Migration Report Format

```markdown
# TAP Migration Report
Project: [name] | Date: [YYYY-MM-DD] | Executed by: [user]

## Summary
| Type | Local Count | Uploaded | Failed | Validation |
|------|------------|---------|--------|------------|
| Test data | 100 | 100 | 0 | ✅ |
| Test cases | 50 | 48 | 2 | ⚠️ |

## Failure Details
- [case_id]: reason — format incompatible

## Next Steps
- [ ] Handle failed items
- [ ] Notify TAP team for acceptance
- [ ] Keep local backup until acceptance complete
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Script runtime | Python + uv |
| Dependency management | `pyproject.toml` via uv |
| API calls | `httpx` (async-capable) |
| Config/secrets | `.env` file via `python-dotenv` |
| CLI interface | `typer` |

---

## Out of Scope (v2)

- Pipeline migration to TAP
- Role-adaptive branching (Tech Lead vs Engineer paths — currently both supported via natural decision gate)
- Batch assessment across multiple projects

---

## Open Questions

1. What formats does TAP support for test data upload?
2. What is the TAP test case import API endpoint and payload format?
3. What authentication method does TAP use?
4. Does TAP provide an API to verify upload success/content?
