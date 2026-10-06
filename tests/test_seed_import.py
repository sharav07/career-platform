"""Tests for deterministic SQLite seed import."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.db import load_resume
from app.content import load_public_content
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


def test_public_content_uses_database_and_preserves_order(tmp_path: Path) -> None:
    database_path = tmp_path / "resume.db"
    seed_data = json.loads(seed_path().read_text(encoding="utf-8"))
    seed_data["experience"].append(
        {
            **seed_data["experience"][0],
            "id": "experience-earlier",
            "employer": "Earlier Company",
            "display_order": 2,
            "achievements": [
                {
                    **seed_data["experience"][0]["achievements"][0],
                    "id": "achievement-earlier",
                }
            ],
        }
    )
    custom_seed_path = tmp_path / "custom.json"
    custom_seed_path.write_text(json.dumps(seed_data), encoding="utf-8")

    import_seed(database_path, custom_seed_path)
    result = load_public_content(database_path, custom_seed_path)

    assert result.degraded is False
    assert result.notice is None
    assert [item.employer for item in result.resume.experience] == [
        "Example Company",
        "Earlier Company",
    ]


def test_empty_database_returns_seed_profile_and_degraded_notice(tmp_path: Path) -> None:
    database_path = tmp_path / "empty.db"
    database_path.touch()

    result = load_public_content(database_path, seed_path())

    assert result.degraded is True
    assert result.notice
    assert result.resume.profile.name == "Your Name"
    assert result.resume.profile.headline == "Your Professional Headline"
    assert result.resume.profile.summary.startswith("Replace this placeholder")
    assert result.resume.profile.contact_links
    assert result.resume.experience == []
    assert result.resume.projects == []


def test_unavailable_database_returns_seed_profile_and_degraded_notice(tmp_path: Path) -> None:
    database_path = tmp_path / "missing" / "resume.db"

    result = load_public_content(database_path, seed_path())

    assert result.degraded is True
    assert result.notice
    assert result.resume.profile.name == "Your Name"
    assert result.resume.profile.contact_links
    assert result.resume.experience == []
