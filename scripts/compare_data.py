"""Compare a SQLite export (source) with a live database (target): counts and content.

Usage: DATABASE_URL=... python scripts/compare_data.py data/migrations/azure-export.json
Prints per-table row counts and a SHA-256 of the sorted rows for each side.
Exit code 1 if anything differs.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import connect  # noqa: E402


def digest(rows: list[dict]) -> str:
    canonical = sorted(json.dumps(r, sort_keys=True, default=str) for r in rows)
    return hashlib.sha256("\n".join(canonical).encode()).hexdigest()[:12]


def main(export_path: str) -> int:
    source = json.loads(Path(export_path).read_text(encoding="utf-8"))
    differs = False
    print(f"{'table':26} {'src':>4} {'dst':>4}  {'src hash':12} {'dst hash':12} match")
    with connect(os.environ["DATABASE_URL"]) as connection:
        for table, src_rows in source.items():
            dst_rows = [dict(r) for r in connection.execute(f"SELECT * FROM {table}")]
            a, b = digest(src_rows), digest(dst_rows)
            same = a == b
            differs |= not same
            print(f"{table:26} {len(src_rows):>4} {len(dst_rows):>4}  {a:12} {b:12} {'OK' if same else 'DIFF'}")
    return 1 if differs else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
