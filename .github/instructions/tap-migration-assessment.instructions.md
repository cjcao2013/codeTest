---
applyTo: "**/*migration*,**/*assessment*,**/*tap*,**/ASSESSMENT*.md,**/MIGRATION*.md"
---

# TAP Migration Methodology

When helping with TAP migration, follow this structure. Do not skip phases or jump ahead.

---

## Prerequisites (Check First)

Before proceeding, confirm ALL of the following:

- [ ] The project has automated tests (API, UI, performance, or a combination)
- [ ] The project is already managed with a CI/CD pipeline (Azure DevOps, GitHub Actions, Jenkins, etc.)
- [ ] The pipeline currently executes the automated tests

**If any prerequisite is NOT met:**

| Missing | Action |
|---------|--------|
| No automated tests | Recommend a test strategy conversation first. Do not proceed. |
| No pipeline | Advise setting up CI/CD pipeline before migration. Do not proceed. |
| Pipeline exists but doesn't run tests | Fix pipeline test integration first. Do not proceed. |

Only continue when all prerequisites are confirmed.

---

## Phase 1: Project Inventory

Gather the current state before touching anything.

### 1.1 Pipeline Profile

- Pipeline platform (Azure DevOps / GitHub Actions / Jenkins / other)
- Pipeline trigger conditions (PR, merge, scheduled, manual)
- Current agent/runner type (cloud-hosted, self-hosted, local machine)
- Environments covered (dev / staging / prod / etc.)
- Pipeline config file location (e.g., `azure-pipelines.yml`, `.github/workflows/`)

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

**Output:** One-paragraph summary of current state plus completed tables above.

---

## Step 1: Pipeline Migration

**Goal:** Connect the existing pipeline to TAP. Test data and test cases remain locally managed and unchanged.

### Step 1 Checklist

**Environment & Access**
- [ ] TAP project space created and accessible
- [ ] Azure DevOps agent pool confirmed (TAP-designated agents)
- [ ] Agent machine specs verified (sufficient for test types in scope)
- [ ] Required secrets/environment variables configured in pipeline

**Pipeline Configuration**
- [ ] TAP pipeline trigger configured (match current trigger behavior exactly)
- [ ] Test execution command updated to route through TAP agent
- [ ] Artifact/report output path configured for TAP
- [ ] Existing pipeline disabled or redirected (avoid duplicate runs)

**Validation**
- [ ] Dry-run executed on TAP agent
- [ ] All test types passing with same pass rate as before migration
- [ ] Pipeline report visible in TAP dashboard
- [ ] Team notified of new pipeline location

**Step 1 is complete when:** All tests pass on TAP agent with the same results as the previous pipeline.

### Step 1 Risk Checklist

| Risk | Check Before Proceeding |
|------|------------------------|
| Agent environment differs from current runner | Compare OS, language runtime, and dependency versions |
| Secrets not available on TAP agent | Pre-configure all secrets before dry-run |
| Test results format incompatible with TAP | Confirm TAP-supported report formats with TAP team |
| Pipeline triggers differ | Match trigger conditions exactly during transition |

---

## Step 2: Test Data & Case Migration (Optional)

**Goal:** Move locally managed test data and test cases into TAP for centralized management.

**Only start Step 2 after Step 1 is stable.**

### 2.1 Step 2 Readiness Check

- [ ] Step 1 has been running stably (no regressions, consistent pass rate)
- [ ] TAP data/case management features confirmed with TAP team:
  - [ ] Supported upload formats for test data
  - [ ] Supported formats or import method for test cases/test plans
- [ ] Team has capacity to validate after migration

### 2.2 Test Data Migration

For each test data source, document:

```
Source: [file path or system name]
Format: [CSV / Excel / JSON / YAML / DB / other]
Volume: [number of records or files]
TAP-compatible format: [confirm with TAP team]
Transformation needed: [Yes / No — describe if Yes]
```

**Steps:**
- [ ] Export test data from current location
- [ ] Transform to TAP-compatible format (if needed)
- [ ] Upload to TAP test data management
- [ ] Update test execution config to reference TAP data source instead of local
- [ ] Run tests — verify same results with TAP-managed data
- [ ] Decommission local test data source (after validation only)

### 2.3 Test Case / Test Plan Migration

For each test case source, document:

```
Source: [file path or tool name]
Format: [code / Excel / test management tool / other]
Count: [number of cases]
TAP import method: [confirm with TAP team]
Transformation needed: [Yes / No — describe if Yes]
```

**Steps:**
- [ ] Export test cases from current location
- [ ] Transform to TAP format (if needed)
- [ ] Import into TAP test plan management
- [ ] Link test cases to pipeline execution in TAP
- [ ] Run full test suite — verify coverage and pass rate unchanged
- [ ] Decommission local test case source (after validation only)

### 2.4 Step 2 Risk Checklist

| Risk | Check Before Proceeding |
|------|------------------------|
| Test data format not supported by TAP | Confirm supported formats with TAP team before starting |
| Data transformation introduces errors | Validate a sample batch before full migration |
| Test cases lose traceability after import | Map old IDs to new TAP IDs before decommissioning |
| Coverage drops after migration | Compare test count and pass rate before and after |

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

## Step 2: Data/Case Migration
Status: [Complete / In Progress / Not Started / N/A]
[Checklist results + validation outcome]

## Open Questions for TAP Team
[Any unresolved format or capability questions]
```

---

## Rules

- Never start Step 2 before Step 1 is stable.
- Never decommission local data or cases before validating TAP-managed versions produce the same results.
- Never assume TAP supports a specific data format — confirm with TAP team first.
- Never migrate all test types at once — migrate one type at a time to isolate failures.
- If prerequisites are not met, stop and address them before proceeding.
