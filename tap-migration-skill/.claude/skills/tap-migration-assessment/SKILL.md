---
name: tap-migration-assessment
description: Use when migrating an existing pipeline-managed automation project to the TAP platform. Covers two steps: (1) pipeline migration with test data/cases unchanged, (2) optional migration of test data/cases into TAP management.
---

# TAP Migration

## Overview

This skill guides migration of an automation project to TAP (Test Automation Platform).

**Two-step model:**
- **Step 1 — Pipeline Migration:** Connect the existing pipeline to TAP. Test data and test cases remain locally managed. Low risk, fast win.
- **Step 2 — Data/Case Migration (Optional):** Move local test data and test cases into TAP for centralized management.

**Core principle:** Step 1 must be stable before starting Step 2.

---

## What is TAP?

TAP (Test Automation Platform) is an internal automation testing system:

| Capability | Description |
|-----------|-------------|
| **API Automation** | HTTP/REST API test automation |
| **Web UI Automation** | Browser-based UI testing |
| **App UI Automation** | Mobile/desktop app UI testing |
| **Performance Testing** | Load, stress, and performance benchmarks |
| **Test Data Management** | Test data upload and management on platform |
| **Azure Pipeline Integration** | CI/CD pipeline via Azure DevOps agents |
| **Agent Execution** | Tests run on designated agent machines |

---

## Prerequisites (Check Before Starting)

**This skill only applies if ALL of the following are true:**

- [ ] The project has automated tests (API, UI, performance, or a combination)
- [ ] The project is already managed with a CI/CD pipeline (Azure DevOps, GitHub Actions, Jenkins, etc.)
- [ ] The pipeline currently executes the automated tests

**If any prerequisite is NOT met:**

| Missing | Action |
|---------|--------|
| No automated tests | Use a test strategy skill first |
| No pipeline | Set up CI/CD pipeline before using this skill |
| Pipeline exists but doesn't run tests | Fix pipeline test integration first |

Do not proceed until all prerequisites are confirmed.

---

## Phase 1: Project Inventory

Before migrating anything, understand the current state.

### Automated Scan (run first)

If `tap-migration/` is available, run the automated scanner to pre-populate test inventory data:

```bash
cd tap-migration && uv run python assess.py --project-dir <path-to-project>
```

Use the output to fill in sections 1.2 and 1.3 below. Fill remaining gaps manually.

### 1.1 Pipeline Profile

- [ ] Pipeline platform (Azure DevOps / GitHub Actions / Jenkins / other)
- [ ] Pipeline trigger conditions (PR, merge, scheduled, manual)
- [ ] Current agent/runner (cloud-hosted, self-hosted, local machine)
- [ ] Environments covered (dev / staging / prod)
- [ ] Pipeline config file location (e.g., `azure-pipelines.yml`, `.github/workflows/`)

### 1.2 Test Inventory

| Test Type | Count | Framework/Tool | Location |
|-----------|-------|----------------|----------|
| API tests | | | |
| Web UI tests | | | |
| App UI tests | | | |
| Performance tests | | | |

### 1.3 Test Data & Case Management

Identify how test data and test cases are currently managed:

| Item | Current Location | Format | Owner |
|------|-----------------|--------|-------|
| Test data | Local files / DB / external tool | CSV / Excel / JSON / YAML / other | |
| Test cases | Local files / test management tool | Code / Excel / other | |
| Test configs | | | |

**Output:** One-paragraph summary of current state + completed tables above.

---

## Step 1: Pipeline Migration

**Goal:** Connect the existing pipeline to TAP. Test data and test cases remain unchanged.

### Step 1 Checklist

#### Environment & Access
- [ ] TAP project space created and accessible
- [ ] Azure DevOps agent pool confirmed (TAP-designated agents)
- [ ] Agent machine specs verified (sufficient for test types in scope)
- [ ] Required secrets/environment variables configured in pipeline

#### Pipeline Configuration
- [ ] TAP pipeline trigger configured (PR / merge / scheduled — match current behavior)
- [ ] Test execution command updated to route through TAP agent
- [ ] Artifact/report output path configured for TAP
- [ ] Existing pipeline disabled or redirected (avoid duplicate runs)

#### Validation
- [ ] Dry-run executed on TAP agent
- [ ] All test types passing (same pass rate as before migration)
- [ ] Pipeline report visible in TAP dashboard
- [ ] Team notified of new pipeline location

**Step 1 is complete when:** All tests pass on TAP agent with the same results as the previous pipeline.

### Step 1 Risks

| Risk | Mitigation |
|------|-----------|
| Agent environment differs from current runner | Compare OS, language runtime, and dependency versions |
| Secrets not available on TAP agent | Pre-configure all secrets before dry-run |
| Test results format incompatible with TAP | Confirm TAP-supported report formats with TAP team |
| Pipeline triggers differ | Match trigger conditions exactly during transition |

---

## Step 2: Test Data & Case Migration (Optional)

**Goal:** Move locally managed test data and test cases into TAP for centralized management.

**Start Step 2 only after Step 1 is stable.**

### 2.1 Readiness Check

Before starting Step 2:
- [ ] Step 1 has been running stably (no regressions, consistent pass rate)
- [ ] TAP data/case management features confirmed with TAP team:
  - [ ] Supported upload formats for test data
  - [ ] Supported formats or import method for test cases/test plans
- [ ] Team has capacity to validate after migration

### 2.2 Test Data Migration

#### Inventory & Format Analysis

For each test data source:
```
Source: [file path or system name]
Format: [CSV / Excel / JSON / YAML / DB / other]
Volume: [number of records or files]
TAP-compatible format: [confirm with TAP team]
Transformation needed: [Yes / No — describe if Yes]
```

#### Migration Steps
- [ ] Export test data from current location
- [ ] Transform to TAP-compatible format (if needed)
- [ ] Upload to TAP test data management
- [ ] Update test execution config to reference TAP data source instead of local
- [ ] Run tests — verify same results with TAP-managed data
- [ ] Decommission local test data source (after validation)

### 2.3 Test Case / Test Plan Migration

#### Inventory & Format Analysis

For each test case source:
```
Source: [file path or tool name]
Format: [code / Excel / test management tool / other]
Count: [number of cases]
TAP import method: [confirm with TAP team]
Transformation needed: [Yes / No — describe if Yes]
```

#### Migration Steps
- [ ] Export test cases from current location
- [ ] Transform to TAP format (if needed)
- [ ] Import into TAP test plan management
- [ ] Link test cases to pipeline execution in TAP
- [ ] Run full test suite — verify coverage and pass rate unchanged
- [ ] Decommission local test case source (after validation)

### 2.4 Step 2 Risks

| Risk | Mitigation |
|------|-----------|
| Test data format not supported by TAP | Confirm supported formats with TAP team before starting |
| Data transformation introduces errors | Validate a sample before full migration |
| Test cases lose traceability after import | Map old IDs to new TAP IDs before decommissioning |
| Coverage drops after migration | Compare test count and pass rate before/after |

---

## Recommendation

Based on the inventory above, provide a clear recommendation before proceeding to Step 1:

**Go** — All prerequisites met, pipeline is straightforward, no blockers identified.
**Pending** — Prerequisites met but unresolved questions must be answered before starting.
**No-go** — One or more prerequisites missing or blockers that require significant work first.

State the recommendation in one line, followed by the single most important reason.

Example:
> **Recommendation: Go** — pytest project with GitHub Actions already configured; Step 1 can start immediately.

---

## Migration Report Format

Produce a report at the end of each step:

```markdown
# TAP Migration Report: [Project Name]
Date: [YYYY-MM-DD]

## Prerequisites
[Confirmed / Not met — list any blockers]

## Phase 1: Project Inventory
[Summary of pipeline, test types, and current data/case management]

## Step 1: Pipeline Migration
Status: [Complete / In Progress / Blocked]
[Checklist results + dry-run outcome]

## Step 2: Data/Case Migration (if applicable)
Status: [Complete / In Progress / Not Started / N/A]
[Checklist results + validation outcome]

## Open Questions for TAP Team
[Any unresolved format or capability questions]
```

---

## Quick Reference

| Phase | Activity | Output |
|-------|----------|--------|
| Prerequisites | Confirm pipeline exists and runs tests | Go / No-go |
| Phase 1 | Inventory pipeline, tests, data/cases | Current state summary |
| Step 1 | Migrate pipeline to TAP | Tests running on TAP agent |
| Step 2 | Migrate test data and cases to TAP | Centralized management in TAP |

---

## Common Mistakes

| Mistake | Why It Fails |
|---------|-------------|
| Starting Step 2 before Step 1 is stable | Data migration failures compound pipeline issues |
| Skipping the dry-run | Environment differences only surface at execution |
| Decommissioning local data before validation | No rollback path if TAP data has errors |
| Assuming TAP supports current data format | Confirm format compatibility before transforming data |
| Migrating all test types at once | Migrate one test type at a time to isolate failures |
