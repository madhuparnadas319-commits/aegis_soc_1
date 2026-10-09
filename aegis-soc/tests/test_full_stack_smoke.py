"""Integration checks with deterministic fake LLM JSON; never claims live Ollama."""
from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from scripts.initialize_database import initialize_database
from api.dashboard_api import app
import agents.multi_agent_orchestrator as engine
import correlation_agent
import incident_summary_agent


@pytest.fixture
def api(tmp_path, monkeypatch):
    db_path = tmp_path / "aegis.db"
    result = initialize_database(db_path)
    assert result["synthetic_cases"] == 8
    monkeypatch.setenv("AEGIS_DB_PATH", str(db_path))
    monkeypatch.setattr(engine, "DB_PATH", db_path)

    def fake_correlation(_system, user_prompt, **kwargs):
        return ({"correlated_events": ["Evidence from synthetic alert"],
                 "attack_pattern": "Reviewed provided evidence",
                 "confidence": 90,
                 "mitre_techniques": [], "evidence_gaps": []},
                {"model": "TEST-STUB-not-Ollama", "latency_seconds": 0.001})

    def fake_summary(_system, user_prompt, **kwargs):
        import json
        data = json.loads(user_prompt)
        return ({"classification": "True Positive" if data["governance"]["risk_score"]>=75 else "Likely False Positive",
                 "severity": data["alert"]["severity"], "confidence": 92,
                 "executive_summary": "Controlled synthetic test result",
                 "evidence_summary": ["No external alert ingestion"],
                 "recommended_actions": ["Review synthetic event"],
                 "analyst_note": "Offline validation only"},
                {"model": "TEST-STUB-not-Ollama", "latency_seconds": 0.001})

    monkeypatch.setattr(correlation_agent, "chat_json", fake_correlation)
    monkeypatch.setattr(incident_summary_agent, "chat_json", fake_summary)
    with TestClient(app) as client:
        yield client, db_path


def test_runtime_routes_and_writes(api):
    client, path = api
    assert client.get("/health").status_code == 200
    dashboard = client.get("/dashboard/overview")
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["database"]["cases"] == 8
    cases = client.get("/dashboard/cases").json()["items"]
    assert len(cases) == 8
    expected = {"ALT-2404": "[A] Autonomous", "ALT-2401": "[H] HITL", "ALT-2408": "[E] Escalation"}
    for alert_id, decision in expected.items():
        response = client.post("/investigate", json={"alert_id": alert_id})
        assert response.status_code == 200, (alert_id,response.text)
        data = response.json()
        assert data["control_mode"] == decision, (alert_id, data)
        assert data["model_metadata"]["correlation"]["model"] == "TEST-STUB-not-Ollama"
        assert data["model_metadata"]["summary"]["model"] == "TEST-STUB-not-Ollama"
        inv_id = data["investigation_id"]
        details = client.get(f"/dashboard/investigations/{inv_id}")
        assert details.status_code == 200
        assert len(client.get(f"/dashboard/investigations/{inv_id}/agent-outputs").json()["items"]) == 5
        ids = client.get("/dashboard/investigations", params={"alert_id":alert_id}).json()["items"]
        assert len(ids) == 1 and ids[0]["investigation_id"] == inv_id
    assert len(client.get("/dashboard/queues/human-review").json()["items"]) == 1
    assert len(client.get("/dashboard/queues/escalations").json()["items"]) == 1
    assert client.get("/dashboard/overview").json()["database"]["investigations"] == 3
    with sqlite3.connect(path) as conn:
        assert conn.execute("select count(*) from agent_outputs").fetchone()[0] == 15
        assert conn.execute("select count(*) from audit_events").fetchone()[0] == 6


def test_db_seed_is_idempotent(api):
    client, path = api
    assert initialize_database(path)["inserted_cases"] == 0
    assert client.get("/dashboard/overview").status_code == 200


def test_bad_alert_rejected(api):
    client, _ = api
    response = client.post("/investigate",json={"alert_id":"ALT-DOES-NOT-EXIST"})
    assert response.status_code == 404
