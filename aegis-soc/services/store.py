"""Additive persistence helpers for application-level AEGIS decisions.

Existing investigation/audit records are never rewritten by this module.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from database.connection import db_session


class RecordNotFound(ValueError):
    """The supplied case or investigation ID does not exist."""


class InvalidAction(ValueError):
    """The requested governance action is not permitted."""


class ActionConflict(ValueError):
    """A mutually exclusive action has already been recorded."""


_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "database" / "app_extensions.sql"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def prepare_storage(conn: sqlite3.Connection) -> None:
    """Create only new AEGIS app extension tables, if absent."""
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))


def require_investigation(
    conn: sqlite3.Connection, *, case_id: str, investigation_id: str
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT i.investigation_id, i.case_id, i.control_mode, c.alert_id "
        "FROM investigations i JOIN cases c ON c.case_id = i.case_id "
        "WHERE i.investigation_id = ? AND i.case_id = ?",
        (investigation_id, case_id),
    ).fetchone()
    if row is None:
        raise RecordNotFound(
            f"Investigation {investigation_id!r} does not belong to case {case_id!r}."
        )
    return dict(row)


def ensure_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidAction(f"{name} must be a nonempty string.")
    return value.strip()


def write_audit(
    conn: sqlite3.Connection,
    *,
    event_type: str,
    case_id: str | None,
    investigation_id: str | None,
    actor_id: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "event_id": new_id("AUD"),
        "event_type": event_type,
        "case_id": case_id,
        "investigation_id": investigation_id,
        "actor_id": actor_id,
        "detail_json": json.dumps(details, sort_keys=True),
        "created_at": utc_now(),
    }
    conn.execute(
        "INSERT INTO aegis_app_audit_events "
        "(event_id,event_type,case_id,investigation_id,actor_id,detail_json,created_at) "
        "VALUES (:event_id,:event_type,:case_id,:investigation_id,:actor_id,:detail_json,:created_at)",
        record,
    )
    return record


def fetch_app_rows(table: str, *, limit: int = 100) -> list[dict[str, Any]]:
    allowed = {
        "aegis_review_actions",
        "aegis_escalation_actions",
        "aegis_app_audit_events",
    }
    if table not in allowed:
        raise InvalidAction("Unsupported app table")
    if not 1 <= limit <= 1000:
        raise InvalidAction("limit must be between 1 and 1000")
    with db_session() as conn:
        prepare_storage(conn)
        result = conn.execute(
            f"SELECT * FROM {table} ORDER BY created_at DESC, rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in result]


def update_case_status(conn: sqlite3.Connection, case_id: str, status: str) -> None:
    """Reflect a recorded analyst outcome without rewriting investigation history.

    Supports earlier stripped-down development fixtures that lacked updated_at.
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(cases)")}
    if not {"case_id", "status"}.issubset(columns):
        return
    if "updated_at" in columns:
        conn.execute("UPDATE cases SET status = ?, updated_at = ? WHERE case_id = ?",
                     (status, utc_now(), case_id))
    else:
        conn.execute("UPDATE cases SET status = ? WHERE case_id = ?", (status, case_id))
