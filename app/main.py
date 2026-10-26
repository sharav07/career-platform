"""FastAPI application entry point."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import is_postgres
from app.routes import router


def create_app(database_path: str | Path = "resume.db", seed_path: str | Path = "data/resume.json") -> FastAPI:
    """Create the application with paths for runtime content sources."""
    app = FastAPI(title="Career Platform")
    # DATABASE_URL (PostgreSQL, set on Railway) wins over DATABASE_PATH (SQLite, Azure).
    target = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PATH") or database_path
    app.state.database_path = target if is_postgres(target) else Path(target)
    app.state.seed_path = Path(os.getenv("SEED_PATH", seed_path))
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
