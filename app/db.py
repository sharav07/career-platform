"""SQLite schema and read access for resume content."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.models import (
    Certification,
    ContactLink,
    Education,
    Experience,
    ExperienceAchievement,
    Project,
    Profile,
    ResumeSeed,
    Skill,
    SkillGroup,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    location TEXT,
    visible INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS profile_links (
    profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    display_order INTEGER NOT NULL,
    label TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (profile_id, display_order)
);
CREATE TABLE IF NOT EXISTS experiences (
    id TEXT PRIMARY KEY,
    employer TEXT NOT NULL,
    title TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    current INTEGER NOT NULL,
    location TEXT,
    description TEXT,
    display_order INTEGER NOT NULL,
    visible INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS experience_achievements (
    id TEXT PRIMARY KEY,
    experience_id TEXT NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    visible INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS skill_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    visible INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    skill_group_id TEXT NOT NULL REFERENCES skill_groups(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    normalized_key TEXT,
    proficiency TEXT,
    emphasis TEXT,
    display_order INTEGER NOT NULL,
    visible INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    contribution TEXT,
    outcome TEXT,
    technologies TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    visible INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS project_links (
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    display_order INTEGER NOT NULL,
    label TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (project_id, display_order)
);
CREATE TABLE IF NOT EXISTS education (
    id TEXT PRIMARY KEY,
    institution TEXT NOT NULL,
    credential TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    details TEXT,
    display_order INTEGER NOT NULL,
    visible INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS certifications (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    issuer TEXT NOT NULL,
    issue_date TEXT,
    expiration_date TEXT,
    verification_url TEXT,
    display_order INTEGER NOT NULL,
    visible INTEGER NOT NULL
);
"""


def initialize_database(path: Path) -> None:
    """Create the v1 SQLite schema if it does not already exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)


def load_resume(database_path: Path) -> ResumeSeed:
    """Load visible resume content from SQLite in explicit display order."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        profile_row = connection.execute(
            "SELECT * FROM profiles WHERE visible = 1 ORDER BY id LIMIT 1"
        ).fetchone()
        if profile_row is None:
            raise ValueError("No visible profile exists")

        profile = Profile(
            id=profile_row["id"],
            name=profile_row["name"],
            headline=profile_row["headline"],
            summary=profile_row["summary"],
            location=profile_row["location"],
            visible=True,
            contact_links=[
                ContactLink(label=row["label"], url=row["url"])
                for row in connection.execute(
                    "SELECT label, url FROM profile_links WHERE profile_id = ? "
                    "ORDER BY display_order, url",
                    (profile_row["id"],),
                ).fetchall()
            ],
        )

        experiences: list[Experience] = []
        for row in connection.execute(
            "SELECT * FROM experiences WHERE visible = 1 ORDER BY display_order, id"
        ):
            achievements = [
                ExperienceAchievement(
                    id=achievement["id"],
                    text=achievement["text"],
                    display_order=achievement["display_order"],
                    visible=True,
                )
                for achievement in connection.execute(
                    "SELECT * FROM experience_achievements "
                    "WHERE experience_id = ? AND visible = 1 "
                    "ORDER BY display_order, id",
                    (row["id"],),
                )
            ]
            experiences.append(
                Experience(
                    id=row["id"],
                    employer=row["employer"],
                    title=row["title"],
                    start_date=row["start_date"],
                    end_date=row["end_date"],
                    current=bool(row["current"]),
                    location=row["location"],
                    description=row["description"],
                    achievements=achievements,
                    display_order=row["display_order"],
                    visible=True,
                )
            )

        skill_groups: list[SkillGroup] = []
        for row in connection.execute(
            "SELECT * FROM skill_groups WHERE visible = 1 ORDER BY display_order, id"
        ):
            skills = [
                Skill(
                    id=skill["id"],
                    name=skill["name"],
                    normalized_key=skill["normalized_key"],
                    proficiency=skill["proficiency"],
                    emphasis=skill["emphasis"],
                    display_order=skill["display_order"],
                    visible=True,
                )
                for skill in connection.execute(
                    "SELECT * FROM skills WHERE skill_group_id = ? AND visible = 1 "
                    "ORDER BY display_order, id",
                    (row["id"],),
                )
            ]
            skill_groups.append(
                SkillGroup(
                    id=row["id"],
                    name=row["name"],
                    skills=skills,
                    display_order=row["display_order"],
                    visible=True,
                )
            )

        projects = [
            Project(
                id=row["id"],
                title=row["title"],
                summary=row["summary"],
                contribution=row["contribution"],
                outcome=row["outcome"],
                technologies=row["technologies"].split("\x1f") if row["technologies"] else [],
                links=[
                    ContactLink(label=link["label"], url=link["url"])
                    for link in connection.execute(
                        "SELECT label, url FROM project_links WHERE project_id = ? "
                        "ORDER BY display_order, url",
                        (row["id"],),
                    )
                ],
                display_order=row["display_order"],
                visible=True,
            )
            for row in connection.execute(
                "SELECT * FROM projects WHERE visible = 1 ORDER BY display_order, id"
            )
        ]

        education = [
            Education(
                id=row["id"],
                institution=row["institution"],
                credential=row["credential"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                details=row["details"],
                display_order=row["display_order"],
                visible=True,
            )
            for row in connection.execute(
                "SELECT * FROM education WHERE visible = 1 ORDER BY display_order, id"
            )
        ]
        certifications = [
            Certification(
                id=row["id"],
                name=row["name"],
                issuer=row["issuer"],
                issue_date=row["issue_date"],
                expiration_date=row["expiration_date"],
                verification_url=row["verification_url"],
                display_order=row["display_order"],
                visible=True,
            )
            for row in connection.execute(
                "SELECT * FROM certifications WHERE visible = 1 ORDER BY display_order, id"
            )
        ]

    return ResumeSeed(
        content_status="production",
        profile=profile,
        experience=experiences,
        skill_groups=skill_groups,
        projects=projects,
        education=education,
        certifications=certifications,
    )
