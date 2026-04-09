# TAP Migration Assistant

This repository is focused on planning and executing the migration of test automation projects to the TAP (Test Automation Platform).

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

When asked to assist with TAP migration, always follow the structured methodology defined in `.github/instructions/tap-migration-assessment.instructions.md`.

The migration follows a two-step model:
- **Step 1 — Pipeline Migration:** Connect the existing CI/CD pipeline to TAP. Test data and test cases remain locally managed. Low risk, fast to complete.
- **Step 2 — Data/Case Migration (Optional):** Move local test data and test cases into TAP for centralized management. Only after Step 1 is stable.

**Prerequisite:** The project must already have automated tests managed by a CI/CD pipeline. If not, do not proceed — address the missing prerequisite first.

Do not skip phases, jump to recommendations, or start Step 2 before Step 1 is complete and stable.

For test data and test case migration to TAP, follow `.github/instructions/tap-data-migration.instructions.md`.
