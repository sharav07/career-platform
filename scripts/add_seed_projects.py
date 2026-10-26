"""Insert any project from the seed file that the database does not have yet.

Idempotent: a project whose id already exists is left alone. Used after the
Azure-to-Railway data transfer, to add the "this website, project in progress"
entry that the Azure database did not have. It is a content update, kept
separate from the migration so the migration comparison stays a pure copy.

Usage: DATABASE_URL=... python scripts/add_seed_projects.py data/resume.json
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import connect  # noqa: E402
from app.seed import load_seed  # noqa: E402


def main(seed_path: str) -> int:
    seed = load_seed(seed_path)
    with connect(os.environ["DATABASE_URL"]) as connection:
        for project in seed.projects:
            exists = connection.execute(
                "SELECT COUNT(*) AS n FROM projects WHERE id = ?", (project.id,)
            ).fetchone()["n"]
            if exists:
                print(f"project {project.id!r} already present; skipped")
                continue
            connection.execute(
                "INSERT INTO projects (id, title, summary, contribution, outcome, "
                "technologies, display_order, visible) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
                "INSERT INTO project_links (project_id, display_order, label, url) VALUES (?, ?, ?, ?)",
                [(project.id, i, link.label, str(link.url)) for i, link in enumerate(project.links)],
            )
            print(f"inserted project {project.id!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
