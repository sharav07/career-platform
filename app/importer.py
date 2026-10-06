"""Import the checked-in resume seed into SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.db import initialize_database
from app.seed import load_seed


def import_seed(database_path: str | Path, seed_path: str | Path) -> None:
    """Validate and atomically replace the single public resume dataset."""
    database = Path(database_path)
    seed = load_seed(seed_path)
    initialize_database(database)

    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            for table in (
                "profile_links",
                "experience_achievements",
                "experiences",
                "skills",
                "skill_groups",
                "project_links",
                "projects",
                "education",
                "certifications",
                "profiles",
            ):
                connection.execute(f"DELETE FROM {table}")

            profile = seed.profile
            connection.execute(
                "INSERT INTO profiles "
                "(id, name, headline, summary, location, visible) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    profile.id,
                    profile.name,
                    profile.headline,
                    profile.summary,
                    profile.location,
                    int(profile.visible),
                ),
            )
            connection.executemany(
                "INSERT INTO profile_links "
                "(profile_id, display_order, label, url) VALUES (?, ?, ?, ?)",
                [
                    (profile.id, index, link.label, str(link.url))
                    for index, link in enumerate(profile.contact_links)
                ],
            )

            for experience in seed.experience:
                connection.execute(
                    "INSERT INTO experiences "
                    "(id, employer, title, start_date, end_date, current, "
                    "location, description, display_order, visible) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        experience.id,
                        experience.employer,
                        experience.title,
                        experience.start_date,
                        experience.end_date,
                        int(experience.current),
                        experience.location,
                        experience.description,
                        experience.display_order,
                        int(experience.visible),
                    ),
                )
                connection.executemany(
                    "INSERT INTO experience_achievements "
                    "(id, experience_id, text, display_order, visible) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            achievement.id,
                            experience.id,
                            achievement.text,
                            achievement.display_order,
                            int(achievement.visible),
                        )
                        for achievement in experience.achievements
                    ],
                )

            for group in seed.skill_groups:
                connection.execute(
                    "INSERT INTO skill_groups (id, name, display_order, visible) "
                    "VALUES (?, ?, ?, ?)",
                    (group.id, group.name, group.display_order, int(group.visible)),
                )
                connection.executemany(
                    "INSERT INTO skills "
                    "(id, skill_group_id, name, normalized_key, proficiency, "
                    "emphasis, display_order, visible) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        (
                            skill.id,
                            group.id,
                            skill.name,
                            skill.normalized_key,
                            skill.proficiency,
                            skill.emphasis,
                            skill.display_order,
                            int(skill.visible),
                        )
                        for skill in group.skills
                    ],
                )

            for project in seed.projects:
                connection.execute(
                    "INSERT INTO projects "
                    "(id, title, summary, contribution, outcome, technologies, "
                    "display_order, visible) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        project.id,
                        project.title,
                        project.summary,
                        project.contribution,
                        project.outcome,
                        "\x1f".join(project.technologies),
                        project.display_order,
                        int(project.visible),
                    ),
                )
                connection.executemany(
                    "INSERT INTO project_links "
                    "(project_id, display_order, label, url) VALUES (?, ?, ?, ?)",
                    [
                        (project.id, index, link.label, str(link.url))
                        for index, link in enumerate(project.links)
                    ],
                )

            connection.executemany(
                "INSERT INTO education "
                "(id, institution, credential, start_date, end_date, details, "
                "display_order, visible) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        item.id,
                        item.institution,
                        item.credential,
                        item.start_date,
                        item.end_date,
                        item.details,
                        item.display_order,
                        int(item.visible),
                    )
                    for item in seed.education
                ],
            )
            connection.executemany(
                "INSERT INTO certifications "
                "(id, name, issuer, issue_date, expiration_date, "
                "verification_url, display_order, visible) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        item.id,
                        item.name,
                        item.issuer,
                        item.issue_date,
                        item.expiration_date,
                        str(item.verification_url) if item.verification_url else None,
                        item.display_order,
                        int(item.visible),
                    )
                    for item in seed.certifications
                ],
            )
