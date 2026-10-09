"""Read-only database inventory for AEGIS troubleshooting."""

from __future__ import annotations

import json

from database.connection import db_session, get_database_path


def main() -> None:
    with db_session(read_only=True) as conn:
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        result = {}
        for table in tables:
            safe = '"' + table.replace('"', '""') + '"'
            result[table] = {
                "rows": conn.execute(f"SELECT COUNT(*) FROM {safe}").fetchone()[0],
                "columns": [row[1] for row in conn.execute(f"PRAGMA table_info({safe})")],
            }
        print(json.dumps({"database": str(get_database_path()), "tables": result}, indent=2))


if __name__ == "__main__":
    main()
