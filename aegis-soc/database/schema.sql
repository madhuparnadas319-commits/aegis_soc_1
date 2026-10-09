-- AEGIS SOC original runtime schema, reconstructed from the Python orchestrator
-- Synthetic local prototype only. Does not reconstruct lost historical investigations.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL UNIQUE,
    title TEXT,
    severity TEXT,
    source TEXT,
    asset_id TEXT,
    user_id TEXT,
    status TEXT NOT NULL DEFAULT 'New',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);

CREATE TABLE IF NOT EXISTS investigations (
    investigation_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(case_id),
    status TEXT NOT NULL,
    overall_risk_score INTEGER,
    classification TEXT,
    control_mode TEXT,
    escalation_required INTEGER DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_investigations_case ON investigations(case_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_investigations_mode ON investigations(control_mode);

CREATE TABLE IF NOT EXISTS agent_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT NOT NULL REFERENCES investigations(investigation_id),
    agent_name TEXT NOT NULL,
    output_json TEXT NOT NULL,
    confidence INTEGER,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_outputs_investigation ON agent_outputs(investigation_id);

CREATE TABLE IF NOT EXISTS hitl_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL REFERENCES cases(case_id),
    investigation_id TEXT NOT NULL REFERENCES investigations(investigation_id),
    analyst_id TEXT,
    decision TEXT,
    rationale TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hitl_decisions_investigation ON hitl_decisions(investigation_id);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL REFERENCES cases(case_id),
    investigation_id TEXT REFERENCES investigations(investigation_id),
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    control_mode TEXT,
    status TEXT,
    details_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_events_case ON audit_events(case_id, created_at DESC);
