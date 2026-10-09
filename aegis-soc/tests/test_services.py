"""Tests persisted HITL/escalation actions against an isolated SQLite fixture."""

from __future__ import annotations

import sqlite3

import pytest

from services.hitl_service import record_review, list_pending_reviews
from services.escalation_service import record_escalation_action, list_escalations
from services.store import ActionConflict, InvalidAction


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    path = tmp_path / "aegis.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE cases (case_id TEXT PRIMARY KEY, alert_id TEXT NOT NULL, status TEXT);
        CREATE TABLE investigations (
            investigation_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            control_mode TEXT NOT NULL,
            classification TEXT,
            overall_risk_score INTEGER,
            status TEXT
        );
        INSERT INTO cases VALUES ('CASE-H','ALT-2401','Open');
        INSERT INTO cases VALUES ('CASE-E','ALT-2408','Open');
        INSERT INTO investigations VALUES ('INV-H','CASE-H','[H] HITL','True Positive',100,'Completed');
        INSERT INTO investigations VALUES ('INV-E','CASE-E','[E] Escalation','True Positive',100,'Completed');
    """)
    conn.commit()
    conn.close()
    monkeypatch.setenv("AEGIS_DB_PATH", str(path))
    return path


def test_hitl_is_persisted_and_finalized(demo_database):
    assert len(list_pending_reviews()) == 1
    result = record_review(
        case_id="CASE-H", investigation_id="INV-H", analyst_id="analyst-01",
        decision="approve", rationale="Reviewed evidence and approved next step",
    )
    assert result["decision"] == "approve"
    assert list_pending_reviews() == []
    with pytest.raises(ActionConflict):
        record_review(
            case_id="CASE-H", investigation_id="INV-H", analyst_id="analyst-02",
            decision="reject", rationale="Contradictory final action",
        )


def test_hitl_cannot_review_escalation(demo_database):
    with pytest.raises(InvalidAction):
        record_review(
            case_id="CASE-E", investigation_id="INV-E", analyst_id="analyst-01",
            decision="approve", rationale="Wrong policy branch",
        )


def test_escalation_lifecycle(demo_database):
    initial = list_escalations()
    assert len(initial) == 1
    assert initial[0]["escalation_status"] == "unacknowledged"
    record_escalation_action(
        case_id="CASE-E", investigation_id="INV-E", analyst_id="analyst-01",
        action="assign", assignee="analyst-02", rationale="Critical asset needs review",
    )
    assert list_escalations()[0]["escalation_status"] == "assign"
    record_escalation_action(
        case_id="CASE-E", investigation_id="INV-E", analyst_id="analyst-02",
        action="resolve", rationale="Investigation concluded in synthetic environment",
    )
    with pytest.raises(ActionConflict):
        record_escalation_action(
            case_id="CASE-E", investigation_id="INV-E", analyst_id="analyst-02",
            action="assign", assignee="analyst-03", rationale="Not allowed",
        )
