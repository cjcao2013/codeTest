# TAP Migration Toolkit

Tools and skills for migrating test automation projects to the TAP (Test Automation Platform).

---

## What's in this repo

### Skills (GitHub Copilot CLI / Claude Code)

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `tap-migration-assessment` | Assess whether a project is ready to migrate to TAP (pipeline focus) | Before starting any migration |
| `tap-data-migration` | Migrate test data and test cases into TAP | After assessment confirms Go |

### Scripts

| Directory | Purpose |
|-----------|---------|
| `tap-migration/` | Python + uv scripts for test data/case migration |
| `api/` | FastAPI backend for the web demo |
| `frontend/` | React frontend for the web demo |

---

## Quick Start

### Step 1: Assess migration readiness

Use the `tap-migration-assessment` skill via GitHub Copilot CLI:

```bash
# In your target project
touch ASSESSMENT.md
copilot
```

```
#file:.github/instructions/tap-migration-assessment.instructions.md
扫描项目的测试文件、CI 配置和技术栈，完成 TAP 迁移可行性评估，结果写入 ASSESSMENT.md
```

See `copilot-cli-usage.md` for full trigger options.

---

### Step 2: Migrate test data and cases

```bash
# Copy tap-migration/ scripts to your target project
cp -r tap-migration/ /path/to/your-project/

# Fill in TAP credentials (get from TAP team)
cp tap-migration/.env.example /path/to/your-project/tap-migration/.env
# Edit .env: fill TAP_API_BASE_URL, TAP_API_TOKEN, TAP_PROJECT_ID

# Also fill in TAP API endpoints in migrate.py (lines marked TBD)
```

**Run assessment (Phase 1):**
```bash
cd /path/to/your-project/tap-migration
uv run assess.py --project-dir ../your-tests
```

**Run migration (Phase 2):**
```bash
# Dry run first
uv run migrate.py --project-dir ../your-tests --dry-run

# Full migration
uv run migrate.py --project-dir ../your-tests --env .env
```

---

## TAP API Setup (fill before Phase 2)

In `tap-migration/migrate.py`, replace the placeholder endpoints after confirming with the TAP team:

```python
_TEST_DATA_ENDPOINT = "{TAP_API_BASE_URL}/test-data"   # ← replace
_TEST_CASE_ENDPOINT = "{TAP_API_BASE_URL}/test-cases"  # ← replace
```

In `tap-migration/.env`:
```
TAP_API_BASE_URL=https://tap.example.com/api   # ← replace
TAP_API_TOKEN=your-token                        # ← replace
TAP_PROJECT_ID=your-project-id                  # ← replace
```

---

## Migration Flow

```
Assessment (tap-migration-assessment skill)
    └── Go decision
        └── Phase 1: assess.py scans project → feasibility report
            └── Go decision
                └── Phase 2: migrate.py converts → uploads → validates → report
```

**Pipeline migration** (connecting CI/CD to TAP) is a separate step — see `tap-migration-assessment` skill.

---

## Web Demo (Frontend + API)

A local web interface for running assessments and migrations through a browser.

### What it provides

- **Assess page** — fill in project path, run assessment, watch live logs, view report
- **Migrate page** — configure migration options (including dry-run), run, watch logs, view report
- **History page** — browse past runs, click any row to view its report

### Tech stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + Vite + TypeScript + shadcn/ui + TailwindCSS |
| Backend API | FastAPI + uvicorn + aiosqlite |
| Real-time logs | WebSocket |
| History storage | SQLite |

### Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, uv

```bash
# Terminal 1 — API server
cd api
uv sync --extra dev
uv run uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
# Opens http://localhost:5173
```

> If port 8000 is taken: use `--port 8001` and update `frontend/.env.local` accordingly.
> If port 5173 is taken: use `npm run dev -- --port 5174`.

### Running tests

```bash
# Backend (25 tests)
cd api && uv run pytest -v

# Frontend (11 tests)
cd frontend && npm run test:run
```
