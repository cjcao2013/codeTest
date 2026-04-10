"""Mock TAP API server — accepts test-data and test-cases uploads."""
from __future__ import annotations
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite

DB_PATH = "mock-tap.db"
BEARER_TOKEN = "demo-token"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS test_data "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS test_cases "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        await db.commit()
    yield


app = FastAPI(title="Mock TAP API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _check_auth(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


@app.post("/test-data", status_code=201)
async def create_test_data(request: Request):
    _check_auth(request)
    body = await request.json()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO test_data (payload) VALUES (?)", (json.dumps(body),))
        await db.commit()
    return {"status": "ok"}


@app.post("/test-cases", status_code=201)
async def create_test_case(request: Request):
    _check_auth(request)
    body = await request.json()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO test_cases (payload) VALUES (?)", (json.dumps(body),))
        await db.commit()
    return {"status": "ok"}


@app.get("/test-data")
async def list_test_data():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, payload, created_at FROM test_data ORDER BY id") as cur:
            rows = await cur.fetchall()
    return [{"id": r[0], "created_at": r[2], **json.loads(r[1])} for r in rows]


@app.get("/test-cases")
async def list_test_cases():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, payload, created_at FROM test_cases ORDER BY id") as cur:
            rows = await cur.fetchall()
    return [{"id": r[0], "created_at": r[2], **json.loads(r[1])} for r in rows]


@app.get("/stats")
async def stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM test_data") as cur:
            data_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM test_cases") as cur:
            case_count = (await cur.fetchone())[0]
    return {"test_data": data_count, "test_cases": case_count}
