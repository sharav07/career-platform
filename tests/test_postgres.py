"""PostgreSQL parity tests. Skipped unless TEST_DATABASE_URL points at a scratch database."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connect, load_resume
from app.importer import import_seed
from app.main import create_app

URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")
SEED = Path(__file__).parent / "fixtures" / "resume_fixture.json"


def test_import_and_read_round_trip_on_postgres() -> None:
    import_seed(URL, SEED)
    resume = load_resume(URL)
    assert resume.profile.name == "Casey Example"
    assert resume.experience[0].achievements
    assert resume.projects


def test_import_is_idempotent_on_postgres() -> None:
    import_seed(URL, SEED)
    import_seed(URL, SEED)
    with connect(URL) as connection:
        count = connection.execute("SELECT COUNT(*) AS n FROM profiles").fetchone()["n"]
    assert count == 1


def test_homepage_is_200_from_postgres_and_503_when_unreachable() -> None:
    import_seed(URL, SEED)
    assert TestClient(create_app(database_path=URL, seed_path=SEED)).get("/").status_code == 200
    bad = "postgresql://nobody:wrong@127.0.0.1:1/none"
    degraded = TestClient(create_app(database_path=bad, seed_path=SEED)).get("/")
    assert degraded.status_code == 503
    assert "Projects temporarily unavailable" in degraded.text
