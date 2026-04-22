---
name: migrating-to-tap
description: Use when migrating a Robot Framework + Excel-driven test project to TAP (Test Automation Platform). Use when asked to migrate, assess, or prepare a Robot Framework project for TAP.
---

# Migrating to TAP

## Core Principle

**You are the client (甲方). TAP adapts to this project — this project does NOT adapt to TAP.**

Never ask "does TAP support X?" — state "TAP must support X, here is the spec."

## The Iron Law

```
UNDERSTAND THE PROJECT FIRST.
NEVER ASSUME ITS STRUCTURE.
EVERY RF + EXCEL PROJECT IS DIFFERENT.
```

## Step 1: Dispatch Parallel Agents to Understand the Project

**REQUIRED: Use `superpowers:dispatching-parallel-agents` for this step.**

Launch 4 agents in parallel to analyze different dimensions simultaneously:

```
Agent 1 — RF Execution Pattern
  Task: Read all .robot and .resource files in Executor/
  Answer: How many RF test cases exist? Is it a single loop executor or individual test cases?
  Detect: Does it use "Run Keyword ${variable}" (dynamic dispatch)?
  Flag: If only 1 RF test case exists, this is a non-standard pattern — the real test cases live in Excel.

Agent 2 — Excel Structure
  Task: List all Excel files. For each: sheet names, column headers, row counts.
  Answer: Which file is the test case registry? Which are test data files?
  Detect: Sensitive columns (password/token/secret/key in name).
  Flag: How many active test cases (ExecutorFlag=Yes or equivalent)?

Agent 3 — Environment & Config
  Task: Read all .json, .yaml, .yml, .env, Jenkinsfile, pipeline config files.
  Answer: What environments exist? What is the exact robot run command with --variable flags?
  Detect: Are there multiple environments (STG/UAT/PROD)?

Agent 4 — Test Data Flow
  Task: Read ExcelHelper.py (or equivalent). Trace how test data flows from Excel into RF.
  Answer: Does it merge all sheets by a common key (e.g. TestCaseId)?
  Detect: Are all sheets joined at runtime, or is each sheet independent?
  Flag: Multi-sheet merge pattern means TAP must store data per sheet, keyed by case ID.
```

Synthesize findings before proceeding. The synthesis must answer:
- Is this standard RF (one .robot file = one test case) or data-driven via Excel?
- What is the actual test case count (in Excel, not in RF)?
- What environments and how are they separated?
- What sensitive data needs vault handling?

## Step 2: Detect the Execution Pattern

Based on Agent 1 findings, classify the project:

**Pattern A — Standard RF** (rare in enterprise QA)
- Multiple test cases across multiple .robot files
- Test data inline or in separate resource files
- TAP can import RF test cases directly

**Pattern B — Single Executor + Excel Registry** (this project's pattern)
- Only 1 RF test case (the loop executor)
- Real test cases defined in Excel (ExecutorFlag column)
- Dynamic keyword dispatch: `Run Keyword OPUS ${OPUS_Flow}`
- **TAP must NOT import RF test cases** — it must import from Excel registry instead
- TAP's "test case" = one row in the Excel registry file

If Pattern B: make this explicit in tap-requirements.md. TAP importing the RF file will only see 1 test case and miss everything.

## Step 3: Run the Scanner

After agent synthesis, run `analyze.py` to get exact column names, sheet names, and counts:

```bash
python ~/.claude/skills/migrating-to-tap/analyze.py /path/to/project
```

The script auto-detects Pattern A vs Pattern B and flags non-standard execution patterns.

## Step 4: Write TAP Requirements

Based on agent synthesis + scanner output, write `tap-requirements.md`.

TAP must provide:

| Requirement | Notes |
|-------------|-------|
| POST /test-cases/import | Import from Excel registry, NOT from .robot files |
| POST /test-data/import | Keyed by env + sheet name + case ID (all sheets merged at runtime) |
| GET /test-data/{env}/{sheet}/{case_id} | Serve to RF at execution time |
| RF execution: exact --variable flags | Must match what's in CI config, no changes to .robot files |
| POST /results/import | Ingest output.xml, link results to Excel case IDs |

Fill every row with actual values from agent synthesis and scanner output.

## Step 5: Convert and Validate

```bash
python ~/.claude/skills/migrating-to-tap/analyze.py /path/to/project --convert-cases
python ~/.claude/skills/migrating-to-tap/analyze.py /path/to/project --convert-data
```

Spot-check 3 cases and 2 sheets before handing off.

## Red Flags — Stop and Re-analyze

- You assumed the project has standard RF test cases without checking
- You assumed file paths or column names without reading the actual files
- You wrote tap-requirements.md before running the parallel agents
- You modified any .robot file
- You're asking TAP "does it support X" instead of telling TAP "it must support X"

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "It looks like a standard RF project" | Run agents first. Enterprise QA projects almost never are. |
| "I can see the Excel files, I know the structure" | You don't know which sheet is the registry vs data until you read the headers. |
| "TAP can probably handle it" | Specify exactly what TAP must handle. Assumptions become bugs. |
| "Only 1 RF test case, must be a mistake" | It's Pattern B. The real cases are in Excel. This is intentional. |
