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
│       │   └── MigratePage.tsx
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
        └── runner.py        # asyncio subprocess management + log streaming
```

---

## Data Flow

```
User fills config form
    → POST /api/assess  (or /api/migrate)
    → API creates run_id, starts subprocess (assess.py / migrate.py)
    → Returns run_id to frontend

Frontend connects WebSocket /api/{type}/ws/{run_id}
    → runner.py reads subprocess stdout line-by-line
    → Each line pushed over WebSocket
    → LogViewer scrolls in real time

Subprocess exits
    → runner.py reads generated Markdown report
    → Saves run record to history.json (run_id, type, status, timestamp, report_path)
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
| Left panel | ConfigForm | `project_dir`, `.env` path, `--dry-run` toggle + Run button |
| Right top | LogViewer | WebSocket real-time scrolling log |
| Right bottom | ReportViewer | Rendered migration report |

### History Page

- Table: timestamp / type (assess|migrate) / status (success|failed) / duration
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
| History storage | Local JSON file | Sufficient for local demo; no database setup needed |

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

## Error Handling

- Subprocess non-zero exit → send `{"type": "error", "message": "..."}` over WebSocket
- Invalid config (missing required fields) → 422 from FastAPI before subprocess starts
- WebSocket disconnect mid-run → subprocess continues; client can reconnect and replay buffered lines
- Report file missing after run → return empty report with error status in history

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

# Terminal 2 — Frontend dev server
cd frontend && npm run dev
# Opens at http://localhost:5173
```

---

## Out of Scope

- Authentication / multi-user support
- Deployment to a remote server
- Visualization charts or flow diagrams (can be added later)
- Docker packaging
