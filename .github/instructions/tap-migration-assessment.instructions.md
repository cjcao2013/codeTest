---
applyTo: "**/*migration*,**/*assessment*,**/*tap*,**/ASSESSMENT*.md,**/MIGRATION*.md"
---

# TAP Migration Assessment Methodology

When performing a TAP migration feasibility assessment, always complete all six phases in order. Do not skip to recommendations without evidence.

---

## Phase 1: Project Profile

Gather the following before any evaluation:

- Project type (web app, mobile app, backend service, microservice, monolith, etc.)
- Tech stack: language, framework, runtime, test runner
- Existing test inventory:
  - API tests: count, current framework (RestAssured, Postman, pytest-requests, etc.)
  - Web UI tests: count, current framework (Selenium, Playwright, Cypress, WebdriverIO, etc.)
  - App UI tests: count, platform (iOS / Android / desktop), current framework (Appium, XCUITest, Espresso, etc.)
  - Performance tests: count, current tool (JMeter, k6, Locust, Gatling, etc.)
- Current CI/CD system (Azure DevOps, GitHub Actions, Jenkins, GitLab CI, etc.)
- Number of environments (dev / staging / UAT / prod, etc.)
- Team size and test ownership (dedicated QA team, developer-owned, etc.)

Output: A project profile summary paragraph plus a table of the above.

---

## Phase 2: TAP Capability Mapping

For each test type present in the project, assess TAP's support level.

Use these support statuses only:
- **Supported** — confirmed by TAP team or known capability
- **Partial** — TAP supports it with limitations or workarounds required
- **Not Supported** — confirmed gap
- **Unknown** — not yet confirmed; must be flagged for TAP team

Fill in the following table:

| Test Type | Project Has? | TAP Support | Gap / Notes |
|-----------|-------------|-------------|-------------|
| API Automation | Yes / No | Supported / Partial / Not Supported / Unknown | |
| Web UI Automation | Yes / No | Supported / Partial / Not Supported / Unknown | |
| App UI Automation | Yes / No | Supported / Partial / Not Supported / Unknown | |
| Performance Testing | Yes / No | Supported / Partial / Not Supported / Unknown | |
| Test Data Management | Yes / No | Supported / Partial / Not Supported / Unknown | |
| Azure Pipeline Trigger | Yes / No | Supported / Partial / Not Supported / Unknown | |

Any "Unknown" item must appear in the "Open Questions for TAP Team" section of the final report. Never issue a final GO recommendation while unknowns remain unresolved.

---

## Phase 3: Risk Scoring

Score each factor from 1 (low risk) to 5 (high risk). Be conservative — when uncertain, score higher.

### Technical Risk (max 25)

| Factor | Score (1–5) | Evidence |
|--------|-------------|----------|
| Test framework coupling (hard to port) | | |
| Test code quality and maintainability | | |
| External dependencies (mocks, stubs, third-party services) | | |
| Environment-specific configuration complexity | | |
| Language or framework mismatch with TAP's supported stack | | |

### Operational Risk (max 25)

| Factor | Score (1–5) | Evidence |
|--------|-------------|----------|
| Azure agent availability and environment parity | | |
| Team familiarity with TAP | | |
| Test data sensitivity or compliance constraints | | |
| Pipeline dependency complexity | | |
| Daily test execution volume | | |

### Risk Level Interpretation

- **Combined score 10–20**: LOW — Full migration recommended
- **Combined score 21–34**: MEDIUM — Phased migration; address gaps before committing
- **Combined score 35–50**: HIGH — Defer migration; resolve blockers first

---

## Phase 4: Gap Analysis

For every "Partial" or "Not Supported" in Phase 2, and every score of 4 or 5 in Phase 3, document a gap entry:

```
Gap: [short title]
Description: [what is missing or problematic]
Impact: HIGH / MEDIUM / LOW
Mitigation options:
  1. [Option A]
  2. [Option B]
Requires TAP team input: Yes / No
```

List gaps in order of impact (HIGH first).

---

## Phase 5: Recommendation

Based on Phases 1–4, issue exactly one of:

### GO — Full Migration
Conditions: All capabilities confirmed, risk score below 20, no HIGH-impact gaps remaining.
Include: Suggested migration timeline and test type priority order.

### PHASED GO — Staged Migration
Conditions: Most capabilities confirmed, risk score 20–34, HIGH gaps have mitigation paths.
Include: Which test types migrate in Phase 1 vs later phases, and what must be resolved before Phase 2 begins.
Default phase order: API tests → Test data → Web UI tests → App UI tests → Performance tests.

### NO-GO — Defer Migration
Conditions: Critical capability gaps (Unknowns or Not Supported on core test types), risk score above 34, HIGH gaps with no clear mitigation.
Include: Exact conditions that must be resolved before re-assessment.

Do not issue a GO or PHASED GO recommendation when unresolved Unknowns remain.

---

## Phase 6: Migration Plan (GO and PHASED GO only)

### Default Test Migration Order

Unless project-specific risk factors justify a different order:
1. API tests (lowest migration risk)
2. Test data setup and teardown
3. Web UI tests
4. App UI tests
5. Performance tests

### Azure Pipeline Setup Checklist

- Identify the correct Azure DevOps project and agent pool
- Confirm agent machine specs meet performance test requirements
- Set up environment variables and secrets in pipeline
- Define trigger conditions (PR, merge to main, scheduled)
- Confirm TAP report output format integrates with Azure dashboards
- Schedule a dry run on agent machines before go-live

### Phased Timeline Template

Adjust based on volume and team capacity:

```
Phase 1 (Week 1–2): Environment setup + API test migration
Phase 2 (Week 3–4): Web/App UI test migration
Phase 3 (Week 5+):  Performance tests + full pipeline validation
```

---

## Final Report Format

Always deliver the assessment as a structured markdown report:

```markdown
# TAP Migration Assessment: [Project Name]
Date: [YYYY-MM-DD]
Assessor: [Name]

## 1. Project Profile
[Summary from Phase 1]

## 2. Capability Mapping
[Table from Phase 2]

## 3. Risk Score
Technical: X / 25 | Operational: Y / 25 | Combined: Z / 50
Risk Level: LOW / MEDIUM / HIGH

## 4. Gap Analysis
[Gap entries, HIGH impact first]

## 5. Recommendation
[GO / PHASED GO / NO-GO + rationale]

## 6. Migration Plan
[Priority order + Azure checklist + timeline — only if GO or PHASED GO]

## 7. Open Questions for TAP Team
[All Unknown items from Phase 2 and any Phase 4 items requiring team input]
```

---

## TAP Team Consultation Template

Use this when escalating unknowns:

```
Project: [Name]
Assessment Date: [Date]

Questions for TAP Team:

1. Does TAP support [test type] for [framework/language]?
   Context: This project uses [specific tool and version].

2. What are the agent machine specs for performance test execution?
   Context: This project runs [X] concurrent users in load tests.

3. Are there known limitations for [specific scenario]?

Please respond with: Supported / Partial (describe constraints) / Not Supported
```

---

## Rules

- Never skip a phase to save time.
- Never issue a recommendation before completing Phase 3 risk scoring.
- Never assume TAP supports something — mark it Unknown and ask.
- Never issue GO while any Unknown capability remains unresolved.
- If the project has no existing tests, do not use this assessment — recommend a test strategy conversation first.
