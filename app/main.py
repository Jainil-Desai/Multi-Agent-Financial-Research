from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rich.logging import RichHandler
import logging

from app.config import settings
from app.database.connection import init_db
from app.api.routes import router


logging.basicConfig(
    level=settings.log_level,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("finresearch")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting up — initialising database...")
    await init_db()
    log.info("Database ready.")
    yield
    log.info("Shutting down.")


app = FastAPI(
    title="Multi-Agent Financial Research System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
