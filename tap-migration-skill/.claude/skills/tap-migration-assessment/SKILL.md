---
name: tap-migration-assessment
description: Use when evaluating whether a project's test data and test cases can be migrated to TAP. Scans the project, assesses compatibility, and outputs a Go / Pending / No-go recommendation.
---

# TAP Migration Assessment

## Overview

This skill evaluates whether a project's test data and test cases are ready to migrate into TAP (Test Automation Platform).

**Scope:** Test data and test case migration only. Pipeline migration is out of scope.

**Output:** A structured assessment report with a clear Go / Pending / No-go recommendation.

---

## Prerequisites (Check Before Starting)

- [ ] The project has automated tests
- [ ] Test data and/or test cases are locally managed (files, not already in a platform)

If neither condition is met, stop — there is nothing to migrate.

---

## Phase 1: Automated Scan

Run the scanner to collect facts about the project:

```bash
cd tap-migration && uv run python assess.py --project-dir <path-to-project>
```

The scanner detects:
- Test framework (pytest / unittest / Robot Framework / Cucumber)
- Dependency management style
- Test data files — format and count
- Test case count

Use the output to fill in the inventory below. Fill gaps manually where the scanner cannot detect.

---

## Phase 2: Inventory

### Test Cases

| Framework | Count | Location |
|-----------|-------|----------|
| | | |

### Test Data

| Format | Count / Volume | Location |
|--------|---------------|----------|
| | | |

**Flag any of the following:**
- Test data stored in a database (not files)
- Test cases defined in an external tool (e.g. Excel, Jira, TestRail)
- Parameterized tests where data drives the test logic

---

## Phase 3: Compatibility Check

Assess each dimension:

| Dimension | Status | Notes |
|-----------|--------|-------|
| Test framework supported by TAP | ✅ / ⚠️ / ❌ | pytest, unittest, Robot Framework, Cucumber |
| Test data format readable by TAP | ✅ / ⚠️ / ❌ | CSV, JSON, YAML supported; Excel needs conversion |
| Test data volume manageable | ✅ / ⚠️ / ❌ | Flag if >5000 records |
| Test cases in migratable format | ✅ / ⚠️ / ❌ | Code-based or file-based; tool-based needs export |

**Status guide:**
- ✅ Ready — no action needed
- ⚠️ Needs attention — resolvable before migration
- ❌ Blocker — must be resolved before proceeding

---

## Recommendation

Based on the inventory and compatibility check, give a single clear recommendation:

**Go** — No blockers, all dimensions ✅ or ⚠️ with clear resolution path.
**Pending** — One or more ⚠️ items need resolution before migration can start.
**No-go** — One or more ❌ blockers that require significant work or TAP team input.

State the recommendation in one line, followed by the single most important reason.

Example:
> **Recommendation: Go** — pytest project with 42 test cases and CSV test data; all formats supported by TAP.

---

## Assessment Report Format

```markdown
# TAP Migration Assessment: [Project Name]
Date: [YYYY-MM-DD]

## Prerequisites
[Met / Not met]

## Inventory
[Test framework, test case count, test data format and volume]

## Compatibility
[Table with ✅ / ⚠️ / ❌ per dimension]

## Recommendation
[Go / Pending / No-go — one line + reason]

## Open Questions for TAP Team
[Any unresolved format or capability questions]
```

---

## Common Mistakes

| Mistake | Why It Matters |
|---------|---------------|
| Assuming TAP supports all data formats | Confirm CSV/JSON/YAML; Excel usually needs conversion |
| Skipping volume check | Large datasets need batched upload strategy |
| Missing tool-based test cases | Cases in Jira/TestRail need export before migration |
