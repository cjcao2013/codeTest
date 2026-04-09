# TAP Migration Demo — Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a React + FastAPI web interface to the existing TAP Migration CLI toolkit for local demo use.

**Architecture:** FastAPI backend (`api/`) wraps `tap-migration/assess.py` and `tap-migration/migrate.py` as subprocesses, buffers stdout and streams it via WebSocket, and stores run history in SQLite. React frontend (`frontend/`) provides config forms, real-time log viewer, Markdown report renderer, and history page.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn[standard], aiosqlite, pytest, pytest-asyncio, httpx, anyio; React 18, Vite, TypeScript, TailwindCSS, shadcn/ui, react-markdown, remark-gfm, react-router-dom.

**Spec:** `docs/superpowers/specs/2026-04-10-tap-migration-frontend-design.md`

**Import root convention:** All `api/` Python files use bare module imports (`from services.db import ...`, `from routers import ...`). The working directory for all `api/` commands is `api/`. `pyproject.toml` sets `pythonpath = ["."]` so pytest resolves modules from `api/`.

---

## File Map

### Backend (`api/`)

| File | Responsibility |
|------|---------------|
| `api/pyproject.toml` | Python project config + deps |
| `api/main.py` | FastAPI app entry, CORS, router registration, DB lifespan |
| `api/routers/assess.py` | `POST /api/assess`, `WS /api/assess/ws/{run_id}` |
| `api/routers/migrate.py` | `POST /api/migrate`, `WS /api/migrate/ws/{run_id}` |
| `api/routers/history.py` | `GET /api/history`, `GET /api/history/{run_id}` |
| `api/services/db.py` | SQLite init + CRUD (`aiosqlite`) |
| `api/services/runner.py` | Subprocess launch, stdout buffer, asyncio.Queue streaming, concurrency lock, `on_complete` callback |
| `api/services/validator.py` | Path input validation (resolve, traversal check, existence check) |
| `api/tests/test_db.py` | Unit tests for db service |
| `api/tests/test_validator.py` | Unit tests for validator |
| `api/tests/test_runner.py` | Unit tests for runner with mock script |
| `api/tests/test_routes.py` | Integration tests for all HTTP + WS routes |
| `api/tests/fixtures/echo_script.py` | Mock subprocess script for runner tests |

### Frontend (`frontend/`)

| File | Responsibility |
|------|---------------|
| `frontend/src/lib/types.ts` | Shared TypeScript types |
| `frontend/src/lib/api.ts` | API client functions |
| `frontend/src/components/LogViewer.tsx` | Scrolling log display |
| `frontend/src/components/ReportViewer.tsx` | Markdown renderer |
| `frontend/src/components/ConfigForm.tsx` | Generic config form |
| `frontend/src/components/HistoryList.tsx` | Run history table |
| `frontend/src/pages/AssessPage.tsx` | Assess flow page |
| `frontend/src/pages/MigratePage.tsx` | Migrate flow page |
| `frontend/src/pages/HistoryPage.tsx` | History page with report modal |
| `frontend/src/App.tsx` | React Router + nav |

---

## Task 1: Backend scaffolding

**Files:**
- Create: `api/pyproject.toml`
- Create: `api/main.py`
- Create: `api/routers/__init__.py`, `api/services/__init__.py`, `api/tests/__init__.py`, `api/tests/fixtures/__init__.py`

- [ ] **Step 1: Create `api/pyproject.toml`**

```toml
[project]
name = "tap-migration-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
    "aiosqlite>=0.20",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "anyio[trio]>=4.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 2: Create `api/main.py`**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import assess, migrate, history
from services.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await init_db()
    yield
    await app.state.db.close()


app = FastAPI(title="TAP Migration API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assess.router, prefix="/api")
app.include_router(migrate.router, prefix="/api")
app.include_router(history.router, prefix="/api")
```

- [ ] **Step 3: Create package directories**

```bash
cd /Users/cj/code/codeTest
mkdir -p api/routers api/services api/tests/fixtures
touch api/routers/__init__.py api/services/__init__.py api/tests/__init__.py api/tests/fixtures/__init__.py
```

- [ ] **Step 4: Install dependencies**

```bash
cd api && uv sync --extra dev
```

- [ ] **Step 5: Commit**

```bash
git add api/
git commit -m "chore: scaffold FastAPI backend for TAP migration demo"
```

---

## Task 2: Database service

**Files:**
- Create: `api/services/db.py`
- Create: `api/tests/test_db.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_db.py
import pytest
from services.db import init_db, insert_run, update_run, get_run, list_runs


@pytest.fixture
async def db(tmp_path):
    conn = await init_db(str(tmp_path / "test.db"))
    yield conn
    await conn.close()


async def test_insert_and_get_run(db):
    await insert_run(db, run_id="abc", run_type="assess", started_at="2026-01-01T00:00:00Z")
    run = await get_run(db, "abc")
    assert run["run_id"] == "abc"
    assert run["type"] == "assess"
    assert run["status"] == "running"
    assert run["ended_at"] is None


async def test_list_runs_empty(db):
    runs = await list_runs(db)
    assert runs == []


async def test_list_runs_returns_inserted(db):
    await insert_run(db, run_id="abc", run_type="assess", started_at="2026-01-01T00:00:00Z")
    runs = await list_runs(db)
    assert len(runs) == 1


async def test_update_run_status(db):
    await insert_run(db, run_id="abc", run_type="assess", started_at="2026-01-01T00:00:00Z")
    await update_run(db, run_id="abc", status="success", ended_at="2026-01-01T00:01:00Z",
                     duration_seconds=60.0, report_path="/tmp/report.md")
    run = await get_run(db, "abc")
    assert run["status"] == "success"
    assert run["duration_seconds"] == 60.0
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd api && uv run pytest tests/test_db.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `api/services/db.py`**

```python
from __future__ import annotations
import aiosqlite
from typing import Any

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_seconds REAL,
    report_path TEXT
)
"""


async def init_db(path: str = "tap_runs.db") -> aiosqlite.Connection:
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    await conn.execute(_CREATE_TABLE)
    await conn.commit()
    return conn


async def insert_run(conn: aiosqlite.Connection, *, run_id: str, run_type: str, started_at: str) -> None:
    await conn.execute(
        "INSERT INTO runs (run_id, type, started_at) VALUES (?, ?, ?)",
        (run_id, run_type, started_at),
    )
    await conn.commit()


async def update_run(
    conn: aiosqlite.Connection,
    *,
    run_id: str,
    status: str,
    ended_at: str,
    duration_seconds: float | None,
    report_path: str | None,
) -> None:
    await conn.execute(
        "UPDATE runs SET status=?, ended_at=?, duration_seconds=?, report_path=? WHERE run_id=?",
        (status, ended_at, duration_seconds, report_path, run_id),
    )
    await conn.commit()


async def get_run(conn: aiosqlite.Connection, run_id: str) -> dict[str, Any] | None:
    async with conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)) as cur:
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_runs(conn: aiosqlite.Connection) -> list[dict[str, Any]]:
    async with conn.execute(
        "SELECT run_id, type, status, started_at, ended_at, duration_seconds FROM runs ORDER BY started_at DESC"
    ) as cur:
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd api && uv run pytest tests/test_db.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add api/services/db.py api/tests/test_db.py
git commit -m "feat: add SQLite db service for run history"
```

---

## Task 3: Input validator

**Files:**
- Create: `api/services/validator.py`
- Create: `api/tests/test_validator.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_validator.py
import pytest
from pathlib import Path
from services.validator import validate_path, ValidationError


def test_valid_existing_dir(tmp_path):
    result = validate_path(str(tmp_path), must_exist=True, must_be_dir=True)
    assert result == tmp_path.resolve()


def test_rejects_traversal():
    with pytest.raises(ValidationError, match="traversal"):
        validate_path("../../etc/passwd")


def test_rejects_missing_when_must_exist(tmp_path):
    with pytest.raises(ValidationError, match="does not exist"):
        validate_path(str(tmp_path / "missing"), must_exist=True)


def test_rejects_file_when_must_be_dir(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(ValidationError, match="not a directory"):
        validate_path(str(f), must_be_dir=True)


def test_optional_path_none_returns_none():
    assert validate_path(None) is None
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd api && uv run pytest tests/test_validator.py -v
```

- [ ] **Step 3: Implement `api/services/validator.py`**

```python
from __future__ import annotations
from pathlib import Path


class ValidationError(ValueError):
    pass


def validate_path(
    value: str | None,
    *,
    must_exist: bool = False,
    must_be_dir: bool = False,
) -> Path | None:
    if value is None:
        return None
    if ".." in Path(value).parts:
        raise ValidationError(f"Path traversal not allowed: {value!r}")
    resolved = Path(value).resolve()
    if must_exist and not resolved.exists():
        raise ValidationError(f"Path does not exist: {resolved}")
    if must_be_dir and resolved.exists() and not resolved.is_dir():
        raise ValidationError(f"Path is not a directory: {resolved}")
    return resolved
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd api && uv run pytest tests/test_validator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add api/services/validator.py api/tests/test_validator.py
git commit -m "feat: add path input validator"
```

---

## Task 4: Runner service

**Files:**
- Create: `api/services/runner.py`
- Create: `api/tests/fixtures/echo_script.py`
- Create: `api/tests/test_runner.py`

- [ ] **Step 1: Create mock subprocess script**

```python
# api/tests/fixtures/echo_script.py
import sys
print("line one")
print("line two")
print("line three")
sys.exit(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
```

- [ ] **Step 2: Write failing tests**

```python
# api/tests/test_runner.py
import asyncio
import pytest
from pathlib import Path
from services.runner import RunnerService, RunnerError

FIXTURE_SCRIPT = str(Path(__file__).parent / "fixtures" / "echo_script.py")


@pytest.fixture
def runner():
    svc = RunnerService()
    yield svc
    svc._runs.clear()
    svc._active_run_id = None


async def test_start_run_returns_run_id(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    assert run_id is not None
    await asyncio.sleep(0.5)


async def test_buffer_contains_output(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)
    state = runner.get_state(run_id)
    assert any("line one" in line for line in state.buffer)


async def test_done_flag_set_after_exit(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)
    assert runner.get_state(run_id).done is True


async def test_exit_code_zero_on_success(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)
    assert runner.get_state(run_id).exit_code == 0


async def test_exit_code_nonzero_on_failure(runner):
    run_id = await runner.start(["python", FIXTURE_SCRIPT, "1"])
    await asyncio.sleep(0.5)
    assert runner.get_state(run_id).exit_code == 1


async def test_concurrency_rejected_when_busy(runner):
    await runner.start(["python", FIXTURE_SCRIPT])
    with pytest.raises(RunnerError, match="already in progress"):
        await runner.start(["python", FIXTURE_SCRIPT])
    await asyncio.sleep(0.5)


async def test_on_complete_callback_called(runner):
    called_with = []

    async def cb(run_id, state):
        called_with.append((run_id, state.exit_code))

    run_id = await runner.start(["python", FIXTURE_SCRIPT], on_complete=cb)
    await asyncio.sleep(0.5)
    assert len(called_with) == 1
    assert called_with[0] == (run_id, 0)
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
cd api && uv run pytest tests/test_runner.py -v
```

- [ ] **Step 4: Implement `api/services/runner.py`**

```python
from __future__ import annotations
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional

_MAX_BUFFER = 10_000


class RunnerError(Exception):
    pass


@dataclass
class RunState:
    run_id: str
    run_type: str = "unknown"
    buffer: list[str] = field(default_factory=list)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    done: bool = False
    exit_code: Optional[int] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None


OnComplete = Callable[[str, RunState], Coroutine[Any, Any, None]]


class RunnerService:
    def __init__(self) -> None:
        self._runs: dict[str, RunState] = {}
        self._active_run_id: Optional[str] = None

    def get_state(self, run_id: str) -> Optional[RunState]:
        return self._runs.get(run_id)

    @property
    def is_busy(self) -> bool:
        return self._active_run_id is not None

    async def start(
        self,
        cmd: list[str],
        cwd: Optional[str] = None,
        run_type: str = "unknown",
        on_complete: Optional[OnComplete] = None,
    ) -> str:
        if self.is_busy:
            raise RunnerError("A run is already in progress")
        run_id = str(uuid.uuid4())
        state = RunState(run_id=run_id, run_type=run_type)
        self._runs[run_id] = state
        self._active_run_id = run_id
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        asyncio.create_task(self._read(run_id, process, on_complete))
        return run_id

    async def _read(
        self,
        run_id: str,
        process: asyncio.subprocess.Process,
        on_complete: Optional[OnComplete],
    ) -> None:
        state = self._runs[run_id]
        assert process.stdout is not None
        async for raw in process.stdout:
            line = raw.decode()
            if len(state.buffer) < _MAX_BUFFER:
                state.buffer.append(line)
            await state.queue.put({"type": "log", "line": line})
        await process.wait()
        state.exit_code = process.returncode
        state.done = True
        state.ended_at = datetime.now(timezone.utc)
        sentinel = (
            {"type": "done"}
            if process.returncode == 0
            else {"type": "error", "message": f"Process exited with code {process.returncode}"}
        )
        await state.queue.put(sentinel)
        self._active_run_id = None
        if on_complete is not None:
            await on_complete(run_id, state)


# Singleton used across routers
runner = RunnerService()
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
cd api && uv run pytest tests/test_runner.py -v
```

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add api/services/runner.py api/tests/test_runner.py api/tests/fixtures/
git commit -m "feat: add runner service with subprocess buffering, concurrency lock, and on_complete callback"
```

---

## Task 5: Assess router

**Files:**
- Create: `api/routers/assess.py`
- Create: `api/tests/test_routes.py`

Note: Tests use `httpx.AsyncClient` with ASGI transport to properly trigger the lifespan (DB init).

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_routes.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_assess_missing_project_dir_returns_422(client):
    resp = await client.post("/api/assess", json={})
    assert resp.status_code == 422


async def test_assess_nonexistent_path_returns_422(client, tmp_path):
    resp = await client.post("/api/assess", json={"project_dir": str(tmp_path / "missing")})
    assert resp.status_code == 422


async def test_assess_valid_returns_run_id(client, tmp_path):
    resp = await client.post("/api/assess", json={"project_dir": str(tmp_path)})
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert len(data["run_id"]) == 36  # UUID4


async def test_assess_409_when_busy(client, tmp_path):
    await client.post("/api/assess", json={"project_dir": str(tmp_path)})
    resp = await client.post("/api/assess", json={"project_dir": str(tmp_path)})
    assert resp.status_code == 409
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd api && uv run pytest tests/test_routes.py -k "assess" -v
```

- [ ] **Step 3: Implement `api/routers/assess.py`**

```python
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.db import insert_run, update_run
from services.runner import runner, RunnerError, RunState
from services.validator import validate_path, ValidationError

router = APIRouter()

TAP_MIGRATION_DIR = str(Path(__file__).parent.parent.parent / "tap-migration")


class AssessRequest(BaseModel):
    project_dir: str
    report_out: str = "./tap-assessment-report.md"
    volume_threshold: str = "small:500,medium:5000"


def _find_report_path(buffer: list[str]) -> str | None:
    for line in buffer:
        if "report written to:" in line.lower():
            return line.strip().split(":", 1)[-1].strip()
    return None


@router.post("/assess")
async def start_assess(req: AssessRequest, request: Request):
    try:
        project_dir = validate_path(req.project_dir, must_exist=True, must_be_dir=True)
        report_out = validate_path(req.report_out)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cmd = [
        "uv", "run", "python", "assess.py",
        "--project-dir", str(project_dir),
        "--report-out", str(report_out),
        "--volume-threshold", req.volume_threshold,
    ]

    db = request.app.state.db

    async def on_complete(run_id: str, state: RunState) -> None:
        duration = (state.ended_at - state.started_at).total_seconds() if state.ended_at else None
        status = "success" if state.exit_code == 0 else "failed"
        await update_run(db, run_id=run_id, status=status,
                         ended_at=state.ended_at.isoformat() if state.ended_at else "",
                         duration_seconds=duration,
                         report_path=_find_report_path(state.buffer))

    try:
        run_id = await runner.start(cmd, cwd=TAP_MIGRATION_DIR, run_type="assess", on_complete=on_complete)
    except RunnerError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await insert_run(db, run_id=run_id, run_type="assess",
                     started_at=datetime.now(timezone.utc).isoformat())
    return {"run_id": run_id}


@router.websocket("/assess/ws/{run_id}")
async def assess_ws(websocket: WebSocket, run_id: str):
    await websocket.accept()
    state = runner.get_state(run_id)
    if state is None:
        await websocket.close(code=4004)
        return
    # Replay buffered lines (handles connect-before-ready race)
    for line in list(state.buffer):
        await websocket.send_json({"type": "log", "line": line})
    if state.done:
        sentinel = {"type": "done"} if state.exit_code == 0 else {"type": "error", "message": f"Exited {state.exit_code}"}
        await websocket.send_json(sentinel)
        await websocket.close()
        return
    try:
        while True:
            msg = await state.queue.get()
            await websocket.send_json(msg)
            if msg["type"] in ("done", "error"):
                break
    except WebSocketDisconnect:
        pass
    await websocket.close()
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd api && uv run pytest tests/test_routes.py -k "assess" -v
```

- [ ] **Step 5: Commit**

```bash
git add api/routers/assess.py api/tests/test_routes.py
git commit -m "feat: add assess router with POST and WebSocket endpoints"
```

---

## Task 6: Migrate router

**Files:**
- Create: `api/routers/migrate.py`
- Extend: `api/tests/test_routes.py`

- [ ] **Step 1: Add failing tests**

```python
# append to api/tests/test_routes.py

async def test_migrate_missing_project_dir_returns_422(client):
    resp = await client.post("/api/migrate", json={})
    assert resp.status_code == 422


async def test_migrate_valid_dry_run_returns_run_id(client, tmp_path):
    resp = await client.post("/api/migrate", json={
        "project_dir": str(tmp_path),
        "dry_run": True,
    })
    assert resp.status_code == 200
    assert "run_id" in resp.json()
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd api && uv run pytest tests/test_routes.py -k "migrate" -v
```

- [ ] **Step 3: Implement `api/routers/migrate.py`**

```python
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.db import insert_run, update_run
from services.runner import runner, RunnerError, RunState
from services.validator import validate_path, ValidationError

router = APIRouter()

TAP_MIGRATION_DIR = str(Path(__file__).parent.parent.parent / "tap-migration")


class MigrateRequest(BaseModel):
    project_dir: str
    env: str = ".env"
    dry_run: bool = False
    report_out: str = "./tap-migration-report.md"


def _find_report_path(buffer: list[str]) -> str | None:
    for line in buffer:
        if "report written to:" in line.lower():
            return line.strip().split(":", 1)[-1].strip()
    return None


@router.post("/migrate")
async def start_migrate(req: MigrateRequest, request: Request):
    try:
        project_dir = validate_path(req.project_dir, must_exist=True, must_be_dir=True)
        report_out = validate_path(req.report_out)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cmd = [
        "uv", "run", "python", "migrate.py",
        "--project-dir", str(project_dir),
        "--env", req.env,
        "--report-out", str(report_out),
    ]
    if req.dry_run:
        cmd += ["--dry-run"]

    db = request.app.state.db

    async def on_complete(run_id: str, state: RunState) -> None:
        duration = (state.ended_at - state.started_at).total_seconds() if state.ended_at else None
        status = "success" if state.exit_code == 0 else "failed"
        await update_run(db, run_id=run_id, status=status,
                         ended_at=state.ended_at.isoformat() if state.ended_at else "",
                         duration_seconds=duration,
                         report_path=_find_report_path(state.buffer))

    try:
        run_id = await runner.start(cmd, cwd=TAP_MIGRATION_DIR, run_type="migrate", on_complete=on_complete)
    except RunnerError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await insert_run(db, run_id=run_id, run_type="migrate",
                     started_at=datetime.now(timezone.utc).isoformat())
    return {"run_id": run_id}


@router.websocket("/migrate/ws/{run_id}")
async def migrate_ws(websocket: WebSocket, run_id: str):
    await websocket.accept()
    state = runner.get_state(run_id)
    if state is None:
        await websocket.close(code=4004)
        return
    for line in list(state.buffer):
        await websocket.send_json({"type": "log", "line": line})
    if state.done:
        sentinel = {"type": "done"} if state.exit_code == 0 else {"type": "error", "message": f"Exited {state.exit_code}"}
        await websocket.send_json(sentinel)
        await websocket.close()
        return
    try:
        while True:
            msg = await state.queue.get()
            await websocket.send_json(msg)
            if msg["type"] in ("done", "error"):
                break
    except WebSocketDisconnect:
        pass
    await websocket.close()
```

- [ ] **Step 4: Run all route tests — expect PASS**

```bash
cd api && uv run pytest tests/test_routes.py -v
```

- [ ] **Step 5: Commit**

```bash
git add api/routers/migrate.py api/tests/test_routes.py
git commit -m "feat: add migrate router with POST and WebSocket endpoints"
```

---

## Task 7: History router

**Files:**
- Create: `api/routers/history.py`
- Extend: `api/tests/test_routes.py`

- [ ] **Step 1: Add failing tests**

```python
# append to api/tests/test_routes.py

async def test_history_empty_returns_list(client):
    resp = await client.get("/api/history")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_history_run_id_not_found_returns_404(client):
    resp = await client.get("/api/history/nonexistent-id")
    assert resp.status_code == 404


async def test_history_contains_run_after_assess(client, tmp_path):
    import asyncio
    post = await client.post("/api/assess", json={"project_dir": str(tmp_path)})
    run_id = post.json()["run_id"]
    await asyncio.sleep(0.1)
    runs = (await client.get("/api/history")).json()
    assert any(r["run_id"] == run_id for r in runs)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd api && uv run pytest tests/test_routes.py -k "history" -v
```

- [ ] **Step 3: Implement `api/routers/history.py`**

```python
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/history")
async def list_history(request: Request):
    from services.db import list_runs
    return await list_runs(request.app.state.db)


@router.get("/history/{run_id}")
async def get_history(run_id: str, request: Request):
    from services.db import get_run
    run = await get_run(request.app.state.db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    report = None
    if run.get("report_path"):
        p = Path(run["report_path"])
        if p.exists():
            report = p.read_text()
    return {**run, "report": report}
```

- [ ] **Step 4: Run all tests — expect PASS**

```bash
cd api && uv run pytest -v
```

- [ ] **Step 5: Commit**

```bash
git add api/routers/history.py api/tests/test_routes.py
git commit -m "feat: add history router"
```

---

## Task 8: Frontend scaffolding

**Files:**
- Create: `frontend/` (Vite + React + TypeScript + Tailwind + shadcn/ui)
- Create: `frontend/.env.local`

- [ ] **Step 1: Scaffold Vite React TS project**

```bash
cd /Users/cj/code/codeTest
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

- [ ] **Step 2: Install Tailwind**

```bash
cd frontend
npm install -D tailwindcss @tailwindcss/vite @tailwindcss/typography
```

Replace `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': '/src' },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
  },
})
```

Replace `frontend/src/index.css`:

```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";
```

- [ ] **Step 3: Install shadcn/ui (non-interactive)**

```bash
cd frontend
npx shadcn@latest init --defaults
npx shadcn@latest add button input switch card badge table dialog tabs label
```

- [ ] **Step 4: Install runtime and dev deps**

```bash
cd frontend
npm install react-router-dom react-markdown remark-gfm
npm install -D vitest @testing-library/react @testing-library/jest-dom @vitejs/plugin-react jsdom
```

- [ ] **Step 5: Add test script to `package.json`**

In `frontend/package.json`, add to `"scripts"`:
```json
"test": "vitest",
"test:run": "vitest run"
```

- [ ] **Step 6: Create test setup file**

```typescript
// frontend/src/test-setup.ts
import '@testing-library/jest-dom'
```

- [ ] **Step 7: Create `.env.local`**

```
VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 8: Verify dev server starts**

```bash
cd frontend && npm run dev
# Should open http://localhost:5173
```

- [ ] **Step 9: Commit**

```bash
cd /Users/cj/code/codeTest
git add frontend/
git commit -m "chore: scaffold React + Vite + Tailwind + shadcn/ui frontend"
```

---

## Task 9: Shared types and API client

**Files:**
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 1: Create `frontend/src/lib/types.ts`**

```typescript
export interface RunRecord {
  run_id: string
  type: 'assess' | 'migrate'
  status: 'running' | 'success' | 'failed'
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
}

export interface RunDetail extends RunRecord {
  report: string | null
}

export interface AssessConfig {
  project_dir: string
  report_out?: string
  volume_threshold?: string
}

export interface MigrateConfig {
  project_dir: string
  env?: string
  dry_run?: boolean
  report_out?: string
}

export type WsMessage =
  | { type: 'log'; line: string }
  | { type: 'done' }
  | { type: 'error'; message: string }
```

- [ ] **Step 2: Create `frontend/src/lib/api.ts`**

```typescript
import type { AssessConfig, MigrateConfig, RunRecord, RunDetail } from './types'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function startAssess(config: AssessConfig): Promise<{ run_id: string }> {
  return post('/api/assess', config)
}

export async function startMigrate(config: MigrateConfig): Promise<{ run_id: string }> {
  return post('/api/migrate', config)
}

export async function fetchHistory(): Promise<RunRecord[]> {
  const res = await fetch(`${BASE}/api/history`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function fetchRun(runId: string): Promise<RunDetail> {
  const res = await fetch(`${BASE}/api/history/${runId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function createWs(path: string): WebSocket {
  const wsBase = BASE.replace(/^http/, 'ws')
  return new WebSocket(`${wsBase}${path}`)
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/
git commit -m "feat: add shared TypeScript types and API client"
```

---

## Task 10: LogViewer component

**Files:**
- Create: `frontend/src/components/LogViewer.tsx`
- Create: `frontend/src/components/LogViewer.test.tsx`

- [ ] **Step 1: Write failing test**

```typescript
// frontend/src/components/LogViewer.test.tsx
import { render, screen } from '@testing-library/react'
import { LogViewer } from './LogViewer'

test('renders each log line', () => {
  render(<LogViewer lines={['line one', 'line two']} />)
  expect(screen.getByText('line one')).toBeInTheDocument()
  expect(screen.getByText('line two')).toBeInTheDocument()
})

test('renders empty state when no lines', () => {
  render(<LogViewer lines={[]} />)
  expect(screen.getByText(/waiting/i)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd frontend && npm run test:run -- src/components/LogViewer.test.tsx
```

- [ ] **Step 3: Implement `frontend/src/components/LogViewer.tsx`**

```typescript
import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

interface Props {
  lines: string[]
  className?: string
}

export function LogViewer({ lines, className }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  if (lines.length === 0) {
    return (
      <div className={cn('bg-zinc-950 rounded p-4 text-zinc-500 text-sm font-mono h-64 flex items-center justify-center', className)}>
        Waiting for output…
      </div>
    )
  }

  return (
    <div className={cn('bg-zinc-950 rounded p-4 text-green-400 text-sm font-mono h-64 overflow-y-auto', className)}>
      {lines.map((line, i) => (
        <div key={i} className="whitespace-pre-wrap">{line}</div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd frontend && npm run test:run -- src/components/LogViewer.test.tsx
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/LogViewer.tsx frontend/src/components/LogViewer.test.tsx frontend/src/test-setup.ts frontend/vite.config.ts
git commit -m "feat: add LogViewer component"
```

---

## Task 11: ReportViewer component

**Files:**
- Create: `frontend/src/components/ReportViewer.tsx`
- Create: `frontend/src/components/ReportViewer.test.tsx`

- [ ] **Step 1: Write failing test**

```typescript
// frontend/src/components/ReportViewer.test.tsx
import { render, screen } from '@testing-library/react'
import { ReportViewer } from './ReportViewer'

test('renders markdown headings', () => {
  render(<ReportViewer markdown="# Hello\n\nWorld" />)
  expect(screen.getByRole('heading', { name: 'Hello' })).toBeInTheDocument()
  expect(screen.getByText('World')).toBeInTheDocument()
})

test('renders empty state when markdown is null', () => {
  render(<ReportViewer markdown={null} />)
  expect(screen.getByText(/no report/i)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd frontend && npm run test:run -- src/components/ReportViewer.test.tsx
```

- [ ] **Step 3: Implement `frontend/src/components/ReportViewer.tsx`**

```typescript
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

interface Props {
  markdown: string | null
  className?: string
}

export function ReportViewer({ markdown, className }: Props) {
  if (!markdown) {
    return (
      <div className={cn('rounded border p-6 text-zinc-400 text-sm flex items-center justify-center min-h-32', className)}>
        No report yet.
      </div>
    )
  }

  return (
    <div className={cn('prose prose-zinc prose-sm max-w-none rounded border p-6 overflow-y-auto max-h-96', className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </div>
  )
}
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd frontend && npm run test:run -- src/components/ReportViewer.test.tsx
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ReportViewer.tsx frontend/src/components/ReportViewer.test.tsx
git commit -m "feat: add ReportViewer component with Markdown rendering"
```

---

## Task 12: ConfigForm component

**Files:**
- Create: `frontend/src/components/ConfigForm.tsx`
- Create: `frontend/src/components/ConfigForm.test.tsx`

- [ ] **Step 1: Write failing test**

```typescript
// frontend/src/components/ConfigForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { ConfigForm, type FieldDef } from './ConfigForm'

const fields: FieldDef[] = [
  { name: 'project_dir', label: 'Project Directory', type: 'text', required: true },
  { name: 'dry_run', label: 'Dry Run', type: 'toggle', required: false },
]

test('renders all fields', () => {
  render(<ConfigForm fields={fields} onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByLabelText('Project Directory')).toBeInTheDocument()
  expect(screen.getByLabelText('Dry Run')).toBeInTheDocument()
})

test('calls onSubmit with field values', () => {
  const onSubmit = vi.fn()
  render(<ConfigForm fields={fields} onSubmit={onSubmit} disabled={false} />)
  fireEvent.change(screen.getByLabelText('Project Directory'), { target: { value: '/tmp/proj' } })
  fireEvent.click(screen.getByRole('button', { name: /run/i }))
  expect(onSubmit).toHaveBeenCalledWith({ project_dir: '/tmp/proj', dry_run: false })
})

test('disables submit when disabled=true', () => {
  render(<ConfigForm fields={fields} onSubmit={vi.fn()} disabled={true} />)
  expect(screen.getByRole('button', { name: /running/i })).toBeDisabled()
})

test('blocks submit when required field is empty', () => {
  const onSubmit = vi.fn()
  render(<ConfigForm fields={fields} onSubmit={onSubmit} disabled={false} />)
  fireEvent.click(screen.getByRole('button', { name: /run/i }))
  expect(onSubmit).not.toHaveBeenCalled()
})
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd frontend && npm run test:run -- src/components/ConfigForm.test.tsx
```

- [ ] **Step 3: Implement `frontend/src/components/ConfigForm.tsx`**

```typescript
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

export interface FieldDef {
  name: string
  label: string
  type: 'text' | 'toggle'
  required: boolean
  defaultValue?: string | boolean
  placeholder?: string
}

interface Props {
  fields: FieldDef[]
  onSubmit: (values: Record<string, string | boolean>) => void
  disabled: boolean
  submitLabel?: string
}

export function ConfigForm({ fields, onSubmit, disabled, submitLabel = 'Run' }: Props) {
  const [values, setValues] = useState<Record<string, string | boolean>>(() =>
    Object.fromEntries(
      fields.map((f) => [f.name, f.defaultValue ?? (f.type === 'toggle' ? false : '')])
    )
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    for (const f of fields) {
      if (f.required && !values[f.name]) return
    }
    onSubmit(values)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {fields.map((f) => (
        <div key={f.name} className="space-y-1">
          <Label htmlFor={f.name}>{f.label}</Label>
          {f.type === 'text' ? (
            <Input
              id={f.name}
              value={values[f.name] as string}
              onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
              placeholder={f.placeholder}
            />
          ) : (
            <Switch
              id={f.name}
              checked={values[f.name] as boolean}
              onCheckedChange={(checked) => setValues((v) => ({ ...v, [f.name]: checked }))}
            />
          )}
        </div>
      ))}
      <Button type="submit" disabled={disabled} className="w-full">
        {disabled ? 'Running…' : submitLabel}
      </Button>
    </form>
  )
}
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd frontend && npm run test:run -- src/components/ConfigForm.test.tsx
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ConfigForm.tsx frontend/src/components/ConfigForm.test.tsx
git commit -m "feat: add ConfigForm component"
```

---

## Task 13: AssessPage

**Files:**
- Create: `frontend/src/pages/AssessPage.tsx`

- [ ] **Step 1: Implement `frontend/src/pages/AssessPage.tsx`**

```typescript
import { useState, useCallback } from 'react'
import { ConfigForm, type FieldDef } from '@/components/ConfigForm'
import { LogViewer } from '@/components/LogViewer'
import { ReportViewer } from '@/components/ReportViewer'
import { startAssess, createWs, fetchRun } from '@/lib/api'
import type { WsMessage } from '@/lib/types'

const FIELDS: FieldDef[] = [
  { name: 'project_dir', label: 'Project Directory', type: 'text', required: true, placeholder: '/path/to/project' },
  { name: 'report_out', label: 'Report Output Path', type: 'text', required: false, defaultValue: './tap-assessment-report.md' },
  { name: 'volume_threshold', label: 'Volume Threshold', type: 'text', required: false, defaultValue: 'small:500,medium:5000' },
]

export function AssessPage() {
  const [logs, setLogs] = useState<string[]>([])
  const [report, setReport] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async (values: Record<string, string | boolean>) => {
    setLogs([])
    setReport(null)
    setError(null)
    setRunning(true)
    try {
      const { run_id } = await startAssess({
        project_dir: values.project_dir as string,
        report_out: (values.report_out as string) || undefined,
        volume_threshold: (values.volume_threshold as string) || undefined,
      })
      const ws = createWs(`/api/assess/ws/${run_id}`)
      ws.onmessage = (e) => {
        const msg: WsMessage = JSON.parse(e.data)
        if (msg.type === 'log') {
          setLogs((l) => [...l, msg.line])
        } else if (msg.type === 'done') {
          fetchRun(run_id).then((r) => setReport(r.report))
          setRunning(false)
          ws.close()
        } else if (msg.type === 'error') {
          setError(msg.message)
          setRunning(false)
          ws.close()
        }
      }
      ws.onerror = () => {
        setError('WebSocket connection failed')
        setRunning(false)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setRunning(false)
    }
  }, [])

  return (
    <div className="grid grid-cols-[320px_1fr] gap-6">
      <aside className="space-y-4">
        <h2 className="text-lg font-semibold">Assessment</h2>
        <ConfigForm fields={FIELDS} onSubmit={handleSubmit} disabled={running} />
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </aside>
      <main className="space-y-4">
        <LogViewer lines={logs} />
        <ReportViewer markdown={report} />
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/AssessPage.tsx
git commit -m "feat: add AssessPage"
```

---

## Task 14: MigratePage

**Files:**
- Create: `frontend/src/pages/MigratePage.tsx`

- [ ] **Step 1: Implement `frontend/src/pages/MigratePage.tsx`**

```typescript
import { useState, useCallback } from 'react'
import { ConfigForm, type FieldDef } from '@/components/ConfigForm'
import { LogViewer } from '@/components/LogViewer'
import { ReportViewer } from '@/components/ReportViewer'
import { startMigrate, createWs, fetchRun } from '@/lib/api'
import type { WsMessage } from '@/lib/types'

const FIELDS: FieldDef[] = [
  { name: 'project_dir', label: 'Project Directory', type: 'text', required: true, placeholder: '/path/to/project' },
  { name: 'env', label: '.env File Path', type: 'text', required: false, defaultValue: '.env' },
  { name: 'dry_run', label: 'Dry Run (skip upload)', type: 'toggle', required: false, defaultValue: false },
  { name: 'report_out', label: 'Report Output Path', type: 'text', required: false, defaultValue: './tap-migration-report.md' },
]

export function MigratePage() {
  const [logs, setLogs] = useState<string[]>([])
  const [report, setReport] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async (values: Record<string, string | boolean>) => {
    setLogs([])
    setReport(null)
    setError(null)
    setRunning(true)
    try {
      const { run_id } = await startMigrate({
        project_dir: values.project_dir as string,
        env: (values.env as string) || undefined,
        dry_run: values.dry_run as boolean,
        report_out: (values.report_out as string) || undefined,
      })
      const ws = createWs(`/api/migrate/ws/${run_id}`)
      ws.onmessage = (e) => {
        const msg: WsMessage = JSON.parse(e.data)
        if (msg.type === 'log') {
          setLogs((l) => [...l, msg.line])
        } else if (msg.type === 'done') {
          fetchRun(run_id).then((r) => setReport(r.report))
          setRunning(false)
          ws.close()
        } else if (msg.type === 'error') {
          setError(msg.message)
          setRunning(false)
          ws.close()
        }
      }
      ws.onerror = () => {
        setError('WebSocket connection failed')
        setRunning(false)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setRunning(false)
    }
  }, [])

  return (
    <div className="grid grid-cols-[320px_1fr] gap-6">
      <aside className="space-y-4">
        <h2 className="text-lg font-semibold">Migration</h2>
        <ConfigForm fields={FIELDS} onSubmit={handleSubmit} disabled={running} />
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </aside>
      <main className="space-y-4">
        <LogViewer lines={logs} />
        <ReportViewer markdown={report} />
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/MigratePage.tsx
git commit -m "feat: add MigratePage"
```

---

## Task 15: HistoryList and HistoryPage

**Files:**
- Create: `frontend/src/components/HistoryList.tsx`
- Create: `frontend/src/components/HistoryList.test.tsx`
- Create: `frontend/src/pages/HistoryPage.tsx`

- [ ] **Step 1: Write failing test**

```typescript
// frontend/src/components/HistoryList.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { HistoryList } from './HistoryList'
import type { RunRecord } from '@/lib/types'

const runs: RunRecord[] = [
  { run_id: 'abc', type: 'assess', status: 'success', started_at: '2026-01-01T10:00:00Z', ended_at: '2026-01-01T10:01:00Z', duration_seconds: 60 },
  { run_id: 'def', type: 'migrate', status: 'failed', started_at: '2026-01-01T11:00:00Z', ended_at: null, duration_seconds: null },
]

test('renders run type for each row', () => {
  render(<HistoryList runs={runs} onSelect={vi.fn()} />)
  expect(screen.getByText('assess')).toBeInTheDocument()
  expect(screen.getByText('migrate')).toBeInTheDocument()
})

test('calls onSelect with run_id when row clicked', () => {
  const onSelect = vi.fn()
  render(<HistoryList runs={runs} onSelect={onSelect} />)
  fireEvent.click(screen.getByText('assess').closest('tr')!)
  expect(onSelect).toHaveBeenCalledWith('abc')
})

test('renders empty state when no runs', () => {
  render(<HistoryList runs={[]} onSelect={vi.fn()} />)
  expect(screen.getByText(/no runs/i)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd frontend && npm run test:run -- src/components/HistoryList.test.tsx
```

- [ ] **Step 3: Implement `frontend/src/components/HistoryList.tsx`**

```typescript
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { RunRecord } from '@/lib/types'

interface Props {
  runs: RunRecord[]
  onSelect: (runId: string) => void
}

export function HistoryList({ runs, onSelect }: Props) {
  if (runs.length === 0) {
    return <p className="text-zinc-400 text-sm py-4">No runs yet.</p>
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Started</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Duration</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {runs.map((r) => (
          <TableRow
            key={r.run_id}
            className="cursor-pointer hover:bg-zinc-100"
            onClick={() => onSelect(r.run_id)}
          >
            <TableCell className="font-mono text-xs">
              {new Date(r.started_at).toLocaleString()}
            </TableCell>
            <TableCell>{r.type}</TableCell>
            <TableCell>
              <Badge
                variant={
                  r.status === 'success' ? 'default'
                  : r.status === 'failed' ? 'destructive'
                  : 'secondary'
                }
              >
                {r.status}
              </Badge>
            </TableCell>
            <TableCell>
              {r.duration_seconds != null ? `${r.duration_seconds.toFixed(1)}s` : '—'}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd frontend && npm run test:run -- src/components/HistoryList.test.tsx
```

- [ ] **Step 5: Implement `frontend/src/pages/HistoryPage.tsx`**

```typescript
import { useEffect, useState } from 'react'
import { HistoryList } from '@/components/HistoryList'
import { ReportViewer } from '@/components/ReportViewer'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { fetchHistory, fetchRun } from '@/lib/api'
import type { RunRecord, RunDetail } from '@/lib/types'

export function HistoryPage() {
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [selected, setSelected] = useState<RunDetail | null>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    fetchHistory().then(setRuns).catch(console.error)
  }, [])

  const handleSelect = async (runId: string) => {
    const detail = await fetchRun(runId).catch(() => null)
    setSelected(detail)
    setOpen(true)
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Run History</h2>
      <HistoryList runs={runs} onSelect={handleSelect} />
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Run Report — {selected?.type}</DialogTitle>
          </DialogHeader>
          <ReportViewer markdown={selected?.report ?? null} />
        </DialogContent>
      </Dialog>
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/HistoryList.tsx frontend/src/components/HistoryList.test.tsx frontend/src/pages/HistoryPage.tsx
git commit -m "feat: add HistoryList component and HistoryPage"
```

---

## Task 16: App router and navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Implement `frontend/src/App.tsx`**

```typescript
import { NavLink, Outlet } from 'react-router-dom'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/assess', label: 'Assess' },
  { to: '/migrate', label: 'Migrate' },
  { to: '/history', label: 'History' },
]

export function App() {
  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b bg-white px-6 py-3 flex items-center gap-6">
        <span className="font-bold text-zinc-800">TAP Migration Demo</span>
        <nav className="flex gap-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn('text-sm', isActive ? 'text-zinc-900 font-medium' : 'text-zinc-500 hover:text-zinc-800')
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Implement `frontend/src/main.tsx`**

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { App } from './App'
import { AssessPage } from './pages/AssessPage'
import { MigratePage } from './pages/MigratePage'
import { HistoryPage } from './pages/HistoryPage'
import './index.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/assess" replace /> },
      { path: 'assess', element: <AssessPage /> },
      { path: 'migrate', element: <MigratePage /> },
      { path: 'history', element: <HistoryPage /> },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
```

- [ ] **Step 3: Run all frontend tests**

```bash
cd frontend && npm run test:run
```

Expected: all component tests pass (LogViewer, ReportViewer, ConfigForm, HistoryList)

- [ ] **Step 4: Run all backend tests**

```bash
cd api && uv run pytest -v
```

Expected: all tests pass

- [ ] **Step 5: Smoke test both servers**

```bash
# Terminal 1
cd api && uv run uvicorn main:app --reload --port 8000
# If 8000 is taken: --port 8001 (update VITE_API_BASE_URL in frontend/.env.local accordingly)

# Terminal 2
cd frontend && npm run dev
# Opens http://localhost:5173
# If 5173 is taken: npm run dev -- --port 5174
```

Verify:
- Nav links work (Assess / Migrate / History)
- Assess form shows 3 fields
- Migrate form shows 4 fields including dry-run toggle
- History page loads with empty table

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: wire React Router, nav, and all pages into App"
```

---

## Manual E2E Checklist

Before declaring done:

- [ ] Assess: enter a real project directory, click Run, confirm logs stream in real time, confirm report renders after completion
- [ ] Migrate: enter same directory, enable dry-run, click Run, confirm logs stream, confirm report renders
- [ ] History: navigate to History page, confirm both runs appear with correct type/status/duration
- [ ] Click a history row, confirm report modal opens with correct content
- [ ] Start a second run while one is in progress — confirm UI shows the 409 error message
- [ ] Stop and restart the API server — confirm history persists across restarts

---

## Final Commit

```bash
git add .
git commit -m "feat: complete TAP Migration Demo frontend (React + FastAPI)"
```
