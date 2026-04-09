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
