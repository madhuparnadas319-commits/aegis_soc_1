-- AEGIS SOC dashboard extensions.
-- These tables are additive. Existing cases, investigations, agent_outputs,
-- hitl_decisions and audit_events are not changed or dropped.
CREATE TABLE IF NOT EXISTS aegis_review_actions (
    action_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    investigation_id TEXT NOT NULL,
    analyst_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('approve','reject','request_more_evidence')),
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_aegis_review_investigation
    ON aegis_review_actions(investigation_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_aegis_final_review_once
    ON aegis_review_actions(investigation_id)
    WHERE decision IN ('approve','reject');

CREATE TABLE IF NOT EXISTS aegis_escalation_actions (
    action_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    investigation_id TEXT NOT NULL,
    analyst_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('acknowledge','assign','resolve')),
    rationale TEXT NOT NULL,
    assignee TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_aegis_escalation_investigation
    ON aegis_escalation_actions(investigation_id, created_at);

CREATE TABLE IF NOT EXISTS aegis_app_audit_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    case_id TEXT,
    investigation_id TEXT,
    actor_id TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_aegis_app_audit_created
    ON aegis_app_audit_events(created_at DESC);
