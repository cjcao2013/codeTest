# TAP Migration Demo — Frontend Design Spec

**Date:** 2026-04-10  
**Status:** Draft  
**Scope:** Add a React + FastAPI frontend to the existing TAP Migration Toolkit for local demo purposes.

---

## Background

The existing project is a Python CLI toolkit (`tap-migration/`) for migrating test cases to the TAP (Test Automation Platform). It has a solid backend (assess.py, migrate.py, src modules) but no user interface. The goal is to add a frontend that:

1. Lets non-CLI users trigger assessments and migrations through a web form
2. Shows real-time log output during execution
3. Renders the resulting Markdown reports in-browser
4. Keeps a history of past runs

Use case: local demo only (single machine, small audience).

---

## Architecture

```
codeTest/
├── tap-migration/          # Existing backend (unchanged)
├── frontend/               # React + Vite + TailwindCSS + shadcn/ui
│   └── src/
│       ├── pages/
│       │   ├── AssessPage.tsx
│       │   ├── MigratePage.tsx
│       │   └── HistoryPage.tsx
│       ├── components/
│       │   ├── ConfigForm.tsx       # Input form for CLI args
│       │   ├── LogViewer.tsx        # Real-time WebSocket log stream
│       │   ├── ReportViewer.tsx     # Markdown report renderer
│       │   └── HistoryList.tsx      # List of past runs
│       └── App.tsx
└── api/                    # FastAPI
    ├── main.py              # App entry, CORS, router registration
    ├── routers/
    │   ├── assess.py        # POST /api/assess, WS /api/assess/ws/{run_id}
    │   ├── migrate.py       # POST /api/migrate, WS /api/migrate/ws/{run_id}
    │   └── history.py       # GET /api/history, GET /api/history/{run_id}
    └── services/
        └── runner.py        # asyncio subprocess management + log streaming + line buffer
```

---

## Data Flow

```
User fills config form
    → POST /api/assess  (or /api/migrate)
    → API generates run_id (UUID4) before subprocess creation
    → Starts subprocess, runner.py begins buffering all stdout lines in memory (keyed by run_id)
    → Returns run_id to frontend immediately

Frontend connects WebSocket /api/{type}/ws/{run_id}
    → runner.py replays all buffered lines first (handles connect-before-ready race condition)
    → Then switches to live streaming as new lines arrive
    → LogViewer scrolls in real time
    → Buffer is retained until process exits plus 5 minutes, capped at 10,000 lines

Subprocess exits
    → runner.py reads generated Markdown report
    → Saves run record to SQLite (run_id UUID4, type, status, started_at, ended_at, report_path)
    → duration = wall-clock time from subprocess start to exit
    → WebSocket sends "DONE" or "ERROR" sentinel

Frontend receives sentinel
    → Fetches report via GET /api/history/{run_id}
    → ReportViewer renders Markdown
```

---

## Pages

### Assess Page

| Area | Component | Description |
|------|-----------|-------------|
| Left panel | ConfigForm | `project_dir` path input + Run button |
| Right top | LogViewer | WebSocket real-time scrolling log |
| Right bottom | ReportViewer | Rendered feasibility report |

### Migrate Page

| Area | Component | Description |
|------|-----------|-------------|
| Left panel | ConfigForm | See Migrate flags below + Run button |
| Right top | LogViewer | WebSocket real-time scrolling log |
| Right bottom | ReportViewer | Rendered migration report |

**Assess flags** (from `assess.py`):

| Flag | Type | Default | UI Control |
|------|------|---------|------------|
| `--project-dir` | path | required | Text input (required) |
| `--report-out` | path | `./tap-assessment-report.md` | Text input |
| `--volume-threshold` | string | `small:500,medium:5000` | Text input |

**Migrate flags** (from `migrate.py`):

| Flag | Type | Default | UI Control |
|------|------|---------|------------|
| `--project-dir` | path | required | Text input (required) |
| `--env` | path | `.env` | Text input |
| `--dry-run` | bool | false | Toggle switch |
| `--report-out` | path | `./tap-migration-report.md` | Text input |

### History Page

- Table: started_at / type (assess|migrate) / status (success|failed) / duration (wall-clock time from subprocess start to exit)
- Click row → opens report in ReportViewer modal

---

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend framework | React 18 + Vite + TypeScript | Fast HMR, strong ecosystem |
| UI components | shadcn/ui + TailwindCSS | Professional look, zero custom CSS |
| Markdown rendering | react-markdown + remark-gfm | Handles TAP report format |
| Real-time logs | WebSocket via native browser API | Best for streaming, no proxy issues on localhost |
| Backend framework | FastAPI + uvicorn | Native async, WebSocket support, easy Python subprocess integration |
| Subprocess management | asyncio.create_subprocess_exec | Non-blocking, line-by-line stdout capture |
| History storage | SQLite via `aiosqlite` | Zero-setup, handles concurrent writes safely (vs. JSON file) |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/assess` | Start an assessment run, returns `{run_id}` |
| WS | `/api/assess/ws/{run_id}` | Stream stdout for assess run |
| POST | `/api/migrate` | Start a migration run, returns `{run_id}` |
| WS | `/api/migrate/ws/{run_id}` | Stream stdout for migrate run |
| GET | `/api/history` | List all past runs |
| GET | `/api/history/{run_id}` | Get run detail + report content |

---

## Input Validation

All path inputs (`project_dir`, `env`, `report_out`) must be validated before forwarding to the subprocess:
- Resolve to an absolute path
- Reject path traversal attempts (e.g., `../../etc/passwd`)
- For required paths (`project_dir`): verify the path exists and is a directory
- Validation happens in the FastAPI route handler before subprocess creation; return 422 on failure

---

## Concurrency

For this local demo, **maximum 1 concurrent run** is enforced. If a run is already active, the API returns HTTP 409 with `{"detail": "A run is already in progress"}`. The frontend disables the Run button while any run is active.

---

## API Response Schemas

**POST `/api/assess` and `/api/migrate`** — response:
```json
{ "run_id": "<uuid4>" }
```

**GET `/api/history/{run_id}`** — response:
```json
{
  "run_id": "string",
  "type": "assess | migrate",
  "status": "running | success | failed",
  "started_at": "ISO8601",
  "ended_at": "ISO8601 | null",
  "duration_seconds": "float | null",
  "report": "Markdown string | null"
}
```

**GET `/api/history`** — response: array of the above objects (without the `report` field).

---

## Error Handling

- Subprocess non-zero exit → send `{"type": "error", "message": "..."}` over WebSocket
- Invalid config (missing/invalid fields) → 422 from FastAPI before subprocess starts
- WebSocket disconnect mid-run → subprocess continues; client can reconnect and replay buffered lines (buffer retained for 5 minutes after **process exit**, capped at 10,000 lines)
- Report file missing after run → return `report: null` with `status: failed` in history record

---

## Testing

- **Unit:** Test runner.py subprocess management with a mock script
- **Integration:** Test FastAPI routes with httpx + websockets test client
- **E2E:** Manual demo walkthrough (assess → review report → migrate dry-run → review report → check history)

---

## Startup

```bash
# Terminal 1 — API server
cd api && uvicorn main:app --reload --port 8000
# If 8000 is taken: uvicorn main:app --reload --port 8001

# Terminal 2 — Frontend dev server
cd frontend && npm run dev
# Opens at http://localhost:5173
# If 5173 is taken: npm run dev -- --port 5174
```

---

## Out of Scope

- Authentication / multi-user support
- Deployment to a remote server
- Visualization charts or flow diagrams (can be added later)
- Docker packaging
