"""Integration checks for additive API routes with a disposable SQLite fixture."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dashboard_routes import router


@pytest.fixture
def client(tmp_path, monkeypatch):
    path = tmp_path / "aegis.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE cases(case_id TEXT PRIMARY KEY, alert_id TEXT, status TEXT);
        CREATE TABLE investigations(
          investigation_id TEXT PRIMARY KEY, case_id TEXT, classification TEXT,
          control_mode TEXT, overall_risk_score INTEGER, status TEXT
        );
        CREATE TABLE agent_outputs(investigation_id TEXT, agent_name TEXT, output_json TEXT);
        CREATE TABLE hitl_decisions(investigation_id TEXT, case_id TEXT);
        CREATE TABLE audit_events(case_id TEXT, investigation_id TEXT, created_at TEXT);
        INSERT INTO cases VALUES ('CASE-H','ALT-2401','Open');
        INSERT INTO cases VALUES ('CASE-E','ALT-2408','Open');
        INSERT INTO investigations VALUES (
          'INV-H','CASE-H','True Positive','[H] HITL',100,'Completed'
        );
        INSERT INTO investigations VALUES (
          'INV-E','CASE-E','True Positive','[E] Escalation',100,'Completed'
        );
    """)
    con.commit()
    con.close()
    monkeypatch.setenv("AEGIS_DB_PATH", str(path))
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as http:
        yield http


def test_read_endpoints(client):
    assert client.get("/dashboard/overview").status_code == 200
    assert len(client.get("/dashboard/cases").json()["items"]) == 2
    assert len(client.get("/dashboard/investigations").json()["items"]) == 2
    assert len(client.get("/dashboard/queues/human-review").json()["items"]) == 1
    assert len(client.get("/dashboard/queues/escalations").json()["items"]) == 1


def test_hitl_is_recorded(client):
    response = client.post("/dashboard/reviews", json={
        "case_id": "CASE-H", "investigation_id": "INV-H",
        "analyst_id": "demo-analyst", "decision": "approve",
        "rationale": "Validated the synthetic incident evidence",
    })
    assert response.status_code == 201
    assert client.get("/dashboard/queues/human-review").json()["items"] == []
    duplicate = client.post("/dashboard/reviews", json={
        "case_id": "CASE-H", "investigation_id": "INV-H",
        "analyst_id": "demo-analyst", "decision": "reject",
        "rationale": "Should not replace a completed approval",
    })
    assert duplicate.status_code == 409


def test_escalation_action_is_recorded(client):
    response = client.post("/dashboard/escalation-actions", json={
        "case_id": "CASE-E", "investigation_id": "INV-E",
        "analyst_id": "demo-analyst", "action": "assign",
        "assignee": "another-analyst", "rationale": "Investigate suspicious exfiltration",
    })
    assert response.status_code == 201
    rows = client.get("/dashboard/queues/escalations").json()["items"]
    assert rows[0]["escalation_status"] == "assign"
