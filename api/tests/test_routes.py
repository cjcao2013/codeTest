import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from services.db import init_db
from services.runner import runner


@pytest.fixture(autouse=True)
async def reset_runner():
    """Reset the runner singleton between tests to avoid state leakage."""
    runner._active_run_id = None
    runner._runs.clear()
    yield
    runner._active_run_id = None
    runner._runs.clear()


@pytest.fixture
async def client():
    app.state.db = await init_db(":memory:")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await app.state.db.close()


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
