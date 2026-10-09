"""Initialize AEGIS SOC's native SQLite schema and its eight synthetic cases.

Safe by default: creates missing tables, inserts absent fixture cases and never
truncates, deletes, overwrites or fabricates historical investigations.
Run from project root: python -m scripts.initialize_database
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from database.connection import get_database_path

ROOT = Path(__file__).resolve().parents[1]


def initialize_database(path: Path | None = None) -> dict[str, int | str]:
    destination = (path or get_database_path()).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    extra = (ROOT / "database" / "app_extensions.sql").read_text(encoding="utf-8")
    data = json.loads((ROOT / "data" / "alerts.json").read_text(encoding="utf-8"))
    alerts = data["alerts"] if isinstance(data, dict) else data
    if not isinstance(alerts, list):
        raise ValueError("data/alerts.json must contain a list of synthetic alerts")

    # Check for schema compatibility *before* applying any changes.
    if destination.is_file():
        with sqlite3.connect(destination) as existing:
            rows = existing.execute("PRAGMA table_info(cases)").fetchall()
            if rows and not {"case_id", "alert_id", "status", "updated_at"}.issubset(
                {row[1] for row in rows}
            ):
                raise ValueError("Existing cases schema is incompatible; refusing to overwrite it")
            inv = existing.execute("PRAGMA table_info(investigations)").fetchall()
            if inv and not {"investigation_id", "case_id", "status", "started_at",
                             "classification", "control_mode", "overall_risk_score"}.issubset(
                {row[1] for row in inv}
            ):
                raise ValueError("Existing investigations schema is incompatible; refusing to overwrite it")

    with sqlite3.connect(destination) as con:
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript(schema)
        con.executescript(extra)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        seeded = 0
        for alert in alerts:
            alert_id = str(alert["alert_id"])
            suffix = alert_id.removeprefix("ALT-")
            case_id = f"CASE-{suffix}"
            before = con.total_changes
            con.execute(
                """INSERT OR IGNORE INTO cases
                (case_id,alert_id,title,severity,source,asset_id,user_id,status,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (case_id, alert_id, alert.get("title"), alert.get("severity"),
                 alert.get("source"), alert.get("asset_id"), alert.get("user_id"),
                 "New", now, now),
            )
            seeded += con.total_changes - before
        con.commit()
        result = {
            "database": str(destination),
            "synthetic_cases": con.execute("SELECT count(*) FROM cases").fetchone()[0],
            "inserted_cases": seeded,
            "investigations": con.execute("SELECT count(*) FROM investigations").fetchone()[0],
        }
        return result


def main() -> None:
    print(json.dumps(initialize_database(), indent=2))


if __name__ == "__main__":
    main()
