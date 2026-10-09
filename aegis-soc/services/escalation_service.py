"""Durable escalation handling for investigations routed [E] Escalation.

This module records human actions locally. It DOES NOT perform firewall,
account-lockout, ticketing, or other external security operations.
"""

from __future__ import annotations

from typing import Any

from database.connection import db_session
from services.store import (
    ActionConflict, InvalidAction, ensure_text, new_id,
    prepare_storage, require_investigation, utc_now, write_audit, update_case_status,
)


_ALLOWED = {"acknowledge", "assign", "resolve"}


def record_escalation_action(
    *, case_id: str, investigation_id: str, analyst_id: str,
    action: str, rationale: str, assignee: str | None = None,
) -> dict[str, Any]:
    case_id = ensure_text("case_id", case_id)
    investigation_id = ensure_text("investigation_id", investigation_id)
    analyst_id = ensure_text("analyst_id", analyst_id)
    rationale = ensure_text("rationale", rationale)
    if action not in _ALLOWED:
        raise InvalidAction(f"Invalid escalation action: {action!r}")
    if action == "assign" and not (assignee and assignee.strip()):
        raise InvalidAction("assign requires a nonempty assignee")
    assignee = assignee.strip() if assignee else None

    with db_session() as conn:
        prepare_storage(conn)
        investigation = require_investigation(
            conn, case_id=case_id, investigation_id=investigation_id
        )
        if investigation["control_mode"] != "[E] Escalation":
            raise InvalidAction("Only [E] Escalation investigations can use this action.")
        last = conn.execute(
            "SELECT action FROM aegis_escalation_actions WHERE investigation_id = ? "
            "ORDER BY created_at DESC, rowid DESC LIMIT 1",
            (investigation_id,),
        ).fetchone()
        if last and last["action"] == "resolve":
            raise ActionConflict("This escalation has already been resolved.")
        record = {
            "action_id": new_id("ESC"), "case_id": case_id,
            "investigation_id": investigation_id, "analyst_id": analyst_id,
            "action": action, "rationale": rationale, "assignee": assignee,
            "created_at": utc_now(),
        }
        conn.execute(
            "INSERT INTO aegis_escalation_actions "
            "(action_id,case_id,investigation_id,analyst_id,action,rationale,assignee,created_at) "
            "VALUES (:action_id,:case_id,:investigation_id,:analyst_id,:action,:rationale,:assignee,:created_at)",
            record,
        )
        write_audit(
            conn, event_type="escalation.action", case_id=case_id,
            investigation_id=investigation_id, actor_id=analyst_id,
            details={"action": action, "rationale": rationale, "assignee": assignee},
        )
        if action == "resolve":
            update_case_status(conn, case_id, "Escalation Resolved")
        return record


def list_escalations(*, limit: int = 100) -> list[dict[str, Any]]:
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    with db_session() as conn:
        prepare_storage(conn)
        rows = conn.execute(
            """
            WITH latest AS (
                SELECT i.*, ROW_NUMBER() OVER (
                    PARTITION BY i.case_id ORDER BY i.rowid DESC
                ) AS rank_in_case FROM investigations i
            )
            SELECT i.investigation_id, i.case_id, c.alert_id, i.classification,
                   i.overall_risk_score AS risk_score, i.control_mode,
                   COALESCE((
                     SELECT a.action FROM aegis_escalation_actions a
                     WHERE a.investigation_id = i.investigation_id
                     ORDER BY a.created_at DESC, a.rowid DESC LIMIT 1
                   ), 'unacknowledged') AS escalation_status
            FROM latest i JOIN cases c ON c.case_id = i.case_id
            WHERE i.rank_in_case = 1 AND i.control_mode = '[E] Escalation'
            ORDER BY risk_score DESC, i.investigation_id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_escalation_actions(*, limit: int = 100) -> list[dict[str, Any]]:
    from services.store import fetch_app_rows
    return fetch_app_rows("aegis_escalation_actions", limit=limit)
