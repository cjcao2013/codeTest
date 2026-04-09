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

### Information Collected

**Test Data / Case Dimension:**

| Question | Purpose |
|----------|---------|
| Where is test data stored? (local files / DB / external tool) | Assess accessibility |
| What format? (CSV / Excel / JSON / YAML / other) | Determine conversion needs |
| Approximate volume? | Estimate migration effort and risk |
| Where are test cases stored? (code / Excel / test management tool) | Same as above |
| How many test cases? | Same as above |

**Project Structure Dimension:**

| Question | Purpose |
|----------|---------|
| Test framework? (pytest / unittest / other) | Script compatibility |
| Dependency management? (requirements.txt / pyproject.toml / other) | uv configuration |
| Any special directory conventions? | Correct path generation in scripts |

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

---

## Phase 2: Execution

### Generated Script Structure

```
tap-migration/
├── pyproject.toml          # uv dependency management
├── .env.example            # TAP API credential placeholders
├── migrate.py              # Main entry point, CLI-driven
├── assess.py               # Re-run assessment (optional)
└── src/
    ├── converter.py        # Format conversion (local → TAP format)
    ├── uploader.py         # TAP API upload calls
    ├── validator.py        # Pre/post migration comparison
    └── reporter.py         # Migration report generation
```

### Execution Flow

```
python migrate.py
  │
  ├── 1. Read local test data/cases
  ├── 2. Convert formats (converter.py)
  ├── 3. Upload to TAP (uploader.py)
  │       └── POST [TAP_API_BASE_URL]/test-data    ← TBD
  │           POST [TAP_API_BASE_URL]/test-cases   ← TBD
  │           Auth: Bearer [TAP_API_TOKEN]         ← TBD
  ├── 4. Validate (validator.py)
  │       └── Compare: local count vs TAP uploaded count
  │           Content spot-check (sample)
  └── 5. Generate report (reporter.py)
```

### TAP API Placeholders

| Purpose | Placeholder |
|---------|-------------|
| Upload test data | `POST [TAP_BASE_URL]/test-data` |
| Upload test cases | `POST [TAP_BASE_URL]/test-cases` |
| Query upload status | `GET [TAP_BASE_URL]/...` |
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
| CLI interface | `argparse` or `typer` |

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
