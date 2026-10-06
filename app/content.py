"""Read-only public content access with a seed-backed profile fallback."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.db import load_resume
from app.models import ResumeSeed
from app.seed import load_seed


@dataclass(frozen=True)
class ContentResult:
    resume: ResumeSeed
    degraded: bool
    notice: str | None = None


def _profile_only(seed: ResumeSeed) -> ResumeSeed:
    return seed.model_copy(
        update={
            "experience": [],
            "skill_groups": [],
            "projects": [],
            "education": [],
            "certifications": [],
        }
    )


def load_public_content(database_path: Path, seed_path: Path) -> ContentResult:
    """Load full SQLite content or a seed-backed profile-only fallback."""
    try:
        return ContentResult(
            resume=load_resume(database_path),
            degraded=False,
        )
    except (OSError, sqlite3.Error, ValueError):
        seed = load_seed(seed_path)
        return ContentResult(
            resume=_profile_only(seed),
            degraded=True,
            notice="The rest of the resume is temporarily unavailable.",
        )
