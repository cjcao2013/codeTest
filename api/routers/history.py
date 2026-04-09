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
