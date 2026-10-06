"""Tests for deterministic SQLite seed import."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.db import load_resume
from app.importer import import_seed


def seed_path() -> Path:
    return Path(__file__).parents[1] / "data" / "resume.json"


def test_import_populates_all_resume_sections(tmp_path: Path) -> None:
    database_path = tmp_path / "resume.db"

    import_seed(database_path, seed_path())
    resume = load_resume(database_path)

    assert resume.profile.name == "Your Name"
    assert resume.experience
    assert resume.experience[0].achievements
    assert resume.skill_groups
    assert resume.projects
    assert resume.education
    assert resume.certifications


def test_import_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "resume.db"

    import_seed(database_path, seed_path())
    first_resume = load_resume(database_path)
    import_seed(database_path, seed_path())
    second_resume = load_resume(database_path)

    with sqlite3.connect(database_path) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "profiles",
                "experiences",
                "experience_achievements",
                "skill_groups",
                "skills",
                "projects",
                "education",
                "certifications",
            )
        }

    assert first_resume == second_resume
    assert all(count == 1 for count in counts.values())


def test_invalid_seed_does_not_write_partial_data(tmp_path: Path) -> None:
    database_path = tmp_path / "resume.db"
    invalid_seed_path = tmp_path / "invalid.json"
    invalid_seed_path.write_text(json.dumps({"profile": {}}), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid resume seed"):
        import_seed(database_path, invalid_seed_path)

    assert not database_path.exists()
