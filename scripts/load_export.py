"""Load a SQLite export (see sqlite_export.py) into the database named by DATABASE_URL.

Used as the Railway pre-deploy command. It only loads when the target has no
profile yet, so a redeploy never overwrites data that already lives in PostgreSQL.

Usage: python scripts/load_export.py data/migrations/azure-export.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import connect, initialize_database  # noqa: E402

# Parents before children so foreign keys are satisfied.
ORDER = [
    "profiles",
    "profile_links",
    "experiences",
    "experience_achievements",
    "skill_groups",
    "skills",
    "projects",
    "project_links",
    "education",
    "certifications",
]


def main(export_path: str) -> int:
    target = os.environ["DATABASE_URL"]
    data = json.loads(Path(export_path).read_text(encoding="utf-8"))
    initialize_database(target)
    with connect(target) as connection:
        existing = connection.execute("SELECT COUNT(*) AS n FROM profiles").fetchone()["n"]
        if existing:
            print(f"target already has {existing} profile row(s); not loading")
            return 0
        for table in ORDER:
            rows = data.get(table, [])
            if not rows:
                continue
            columns = list(rows[0].keys())
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
            connection.executemany(sql, [tuple(r[c] for c in columns) for r in rows])
            print(f"loaded {len(rows):>3} rows into {table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
