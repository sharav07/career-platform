"""FastAPI application entry point."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router


def create_app(database_path: str | Path = "resume.db", seed_path: str | Path = "data/resume.json") -> FastAPI:
    """Create the application with paths for runtime content sources."""
    app = FastAPI(title="Career Platform")
    app.state.database_path = Path(os.getenv("DATABASE_PATH", database_path))
    app.state.seed_path = Path(os.getenv("SEED_PATH", seed_path))
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
