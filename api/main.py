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
