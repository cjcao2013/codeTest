# TAP Migration Assistant

This repository is focused on evaluating and executing the migration of test data and test cases to TAP (Test Automation Platform).

## What is TAP

TAP is an internal test automation platform that supports:
- API automation testing
- Web UI automation testing (browser-based)
- App UI automation testing (mobile/desktop)
- Performance testing (load, stress, benchmarks)
- Test data management (upload and centralized management)
- Azure DevOps pipeline integration
- Execution on designated agent machines

> TAP capability boundaries should be confirmed with the TAP development team. When a capability or supported format is uncertain, always flag it for team confirmation rather than assuming support.

## Your Role

Two skills are available. Use them in order:

**1. Assessment** — Evaluate whether the project's test data and test cases can be migrated to TAP.
Follow `.github/instructions/tap-migration-assessment.instructions.md`.
Output: Go / Pending / No-go recommendation.

**2. Migration** — Execute the migration after a Go assessment.
Follow `.github/instructions/tap-data-migration.instructions.md`.
Output: Migration report with upload results and validation.

**Scope:** Test data and test case migration only. Pipeline migration is out of scope.

Do not proceed to migration without a Go recommendation from the assessment.
