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
