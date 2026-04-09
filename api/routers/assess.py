from __future__ import annotations
import re
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.db import insert_run, update_run
from services.runner import runner, RunnerError, RunState
from services.validator import validate_path, ValidationError

router = APIRouter()

TAP_MIGRATION_DIR = str(Path(__file__).parent.parent.parent / "tap-migration")

_THRESHOLD_RE = re.compile(r'^[a-zA-Z]+:\d+(,[a-zA-Z]+:\d+)*$')


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

    if not _THRESHOLD_RE.match(req.volume_threshold):
        raise HTTPException(status_code=422, detail="volume_threshold must be in format 'label:number' comma-separated")

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
