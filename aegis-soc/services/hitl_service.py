"""Durable analyst review for investigations routed to [H] HITL."""

from __future__ import annotations

import sqlite3
from typing import Any

from database.connection import db_session
from services.store import (
    ActionConflict, InvalidAction, ensure_text, new_id,
    prepare_storage, require_investigation, utc_now, write_audit, update_case_status,
)


_ALLOWED = {"approve", "reject", "request_more_evidence"}


def record_review(
    *, case_id: str, investigation_id: str, analyst_id: str,
    decision: str, rationale: str,
) -> dict[str, Any]:
    """Record analyst action; restrict to HITL and prevent contradictory finals."""
    case_id = ensure_text("case_id", case_id)
    investigation_id = ensure_text("investigation_id", investigation_id)
    analyst_id = ensure_text("analyst_id", analyst_id)
    rationale = ensure_text("rationale", rationale)
    if decision not in _ALLOWED:
        raise InvalidAction(f"Invalid review decision: {decision!r}")

    with db_session() as conn:
        prepare_storage(conn)
        investigation = require_investigation(
            conn, case_id=case_id, investigation_id=investigation_id
        )
        if investigation["control_mode"] != "[H] HITL":
            raise InvalidAction("Only [H] HITL investigations may be reviewed here.")
        prior_final = conn.execute(
            "SELECT decision FROM aegis_review_actions WHERE investigation_id = ? "
            "AND decision IN ('approve','reject') LIMIT 1",
            (investigation_id,),
        ).fetchone()
        if prior_final:
            raise ActionConflict(f"Review already finalized as {prior_final['decision']}.")
        action = {
            "action_id": new_id("REV"), "case_id": case_id,
            "investigation_id": investigation_id, "analyst_id": analyst_id,
            "decision": decision, "rationale": rationale, "created_at": utc_now(),
        }
        try:
            conn.execute(
                "INSERT INTO aegis_review_actions "
                "(action_id,case_id,investigation_id,analyst_id,decision,rationale,created_at) "
                "VALUES (:action_id,:case_id,:investigation_id,:analyst_id,:decision,:rationale,:created_at)",
                action,
            )
        except sqlite3.IntegrityError as exc:
            raise ActionConflict("This investigation already has a final review.") from exc
        write_audit(
            conn, event_type="hitl.review", case_id=case_id,
            investigation_id=investigation_id, actor_id=analyst_id,
            details={"decision": decision, "rationale": rationale},
        )
        if decision in {"approve", "reject"}:
            update_case_status(conn, case_id, "HITL Approved" if decision == "approve" else "HITL Rejected")
        return action


def list_pending_reviews(*, limit: int = 100) -> list[dict[str, Any]]:
    """The latest investigation per case that still needs an analyst decision."""
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
            SELECT i.investigation_id, i.case_id, c.alert_id, i.control_mode,
                   i.classification, i.overall_risk_score AS risk_score, i.status
            FROM latest i JOIN cases c ON c.case_id = i.case_id
            WHERE i.rank_in_case = 1 AND i.control_mode = '[H] HITL'
              AND NOT EXISTS (
                SELECT 1 FROM aegis_review_actions a
                WHERE a.investigation_id = i.investigation_id
                  AND a.decision IN ('approve','reject')
              )
            ORDER BY i.risk_score DESC, i.investigation_id DESC LIMIT ?
            """.replace("ORDER BY i.risk_score DESC", "ORDER BY risk_score DESC"),
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_reviews(*, limit: int = 100) -> list[dict[str, Any]]:
    from services.store import fetch_app_rows
    return fetch_app_rows("aegis_review_actions", limit=limit)
