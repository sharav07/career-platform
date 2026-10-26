"""Export every table of a SQLite database to JSON ({table: [row, ...]}).

Usage: python scripts/sqlite_export.py resume.db > export.json
This is the "source" snapshot for a migration. The Azure VM's resume.db is the
real source of truth, not the checked-in seed.
"""

from __future__ import annotations

import json
import sqlite3
import sys


def export(path: str) -> dict[str, list[dict]]:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    return {t: [dict(r) for r in connection.execute(f"SELECT * FROM {t}")] for t in tables}


if __name__ == "__main__":
    json.dump(export(sys.argv[1]), sys.stdout, indent=1)
    print()
