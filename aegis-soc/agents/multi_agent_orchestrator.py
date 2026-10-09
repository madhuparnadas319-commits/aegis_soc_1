import json
import os
import sqlite3
import sys
import uuid

from datetime import datetime
from pathlib import Path


from context_loader import build_case_context

from correlation_agent import (
    run_correlation,
)

from threat_intel_agent import (
    run_threat_intel,
)

from asset_context_agent import (
    run_asset_context,
)

from risk_governance_agent import (
    run_risk_governance,
)

from incident_summary_agent import (
    run_incident_summary,
)


ROOT = Path(__file__).resolve().parent.parent
_db_setting = os.getenv("AEGIS_DB_PATH", "").strip()
DB_PATH = Path(_db_setting).expanduser() if _db_setting else ROOT / "database" / "aegis.db"
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
DB_PATH = DB_PATH.resolve()


def now():
    return datetime.now().isoformat(
        timespec="seconds"
    )


def persist_agent_output(
    conn,
    investigation_id,
    agent_name,
    output,
    confidence=None,
):
    conn.execute(
        """
        INSERT INTO agent_outputs (
            investigation_id,
            agent_name,
            output_json,
            confidence,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            investigation_id,
            agent_name,
            json.dumps(
                output,
                ensure_ascii=False,
            ),
            confidence,
            now(),
        ),
    )


def add_audit(
    conn,
    case_id,
    actor,
    action,
    control_mode,
    status,
    details=None,
):
    investigation_id = (details or {}).get("investigation_id")
    conn.execute(
        """
        INSERT INTO audit_events (
            case_id,
            investigation_id,
            actor,
            action,
            control_mode,
            status,
            details_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            investigation_id,
            actor,
            action,
            control_mode,
            status,
            json.dumps(
                details or {},
                ensure_ascii=False,
            ),
            now(),
        ),
    )


def run_pipeline(alert_id):
    context = build_case_context(
        alert_id
    )

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    case_row = conn.execute(
        """
        SELECT case_id
        FROM cases
        WHERE alert_id = ?
        """,
        (alert_id,),
    ).fetchone()

    if case_row is None:
        conn.close()

        raise ValueError(
            f"No database case exists for "
            f"{alert_id}"
        )

    case_id = case_row[0]

    investigation_id = (
        "INV-"
        + uuid.uuid4()
        .hex[:8]
        .upper()
    )

    started_at = now()

    conn.execute(
        """
        INSERT INTO investigations (
            investigation_id,
            case_id,
            status,
            started_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            investigation_id,
            case_id,
            "Running",
            started_at,
        ),
    )

    add_audit(
        conn,
        case_id,
        "SOC Orchestrator",
        "Multi-agent investigation started",
        "SYSTEM",
        "Running",
        {
            "investigation_id":
                investigation_id
        },
    )

    conn.commit()

    try:
        # =========================================
        # AGENT 1: CORRELATION
        # =========================================

        print(
            "[1/5] Correlation Agent..."
        )

        correlation_result = (
            run_correlation(
                context
            )
        )

        correlation = (
            correlation_result["output"]
        )

        persist_agent_output(
            conn,
            investigation_id,
            "Correlation Agent",
            correlation_result,
            correlation.get(
                "confidence"
            ),
        )

        # =========================================
        # AGENT 2: THREAT INTELLIGENCE
        # =========================================

        print(
            "[2/5] Threat Intelligence Agent..."
        )

        threat_intel = (
            run_threat_intel(
                context
            )
        )

        persist_agent_output(
            conn,
            investigation_id,
            "Threat Intelligence Agent",
            threat_intel,
            threat_intel.get(
                "confidence"
            ),
        )

        # =========================================
        # AGENT 3: ASSET CONTEXT
        # =========================================

        print(
            "[3/5] Asset Context Agent..."
        )

        asset_context = (
            run_asset_context(
                context
            )
        )

        persist_agent_output(
            conn,
            investigation_id,
            "Asset Context Agent",
            asset_context,
        )

        # =========================================
        # AGENT 4: RISK & GOVERNANCE
        # =========================================

        print(
            "[4/5] Risk & Governance Agent..."
        )

        governance = (
            run_risk_governance(
                context,
                correlation,
                threat_intel,
                asset_context,
            )
        )

        persist_agent_output(
            conn,
            investigation_id,
            "Risk & Governance Agent",
            governance,
        )

        # =========================================
        # AGENT 5: INCIDENT SUMMARY
        # =========================================

        print(
            "[5/5] Incident Summary Agent..."
        )

        summary_result = (
            run_incident_summary(
                context,
                correlation,
                threat_intel,
                asset_context,
                governance,
            )
        )

        summary = (
            summary_result["output"]
        )

        persist_agent_output(
            conn,
            investigation_id,
            "Incident Summary Agent",
            summary_result,
            summary.get(
                "confidence"
            ),
        )

        # =========================================
        # CONDITIONAL GOVERNANCE ROUTING
        # =========================================

        mode = governance[
            "control_mode"
        ]

        if mode.startswith("[E]"):
            case_status = "Escalated"

        elif mode.startswith("[H]"):
            case_status = "Awaiting HITL"

        else:
            case_status = "Triaged"

        completed_at = now()

        conn.execute(
            """
            UPDATE investigations
            SET
                status = ?,
                overall_risk_score = ?,
                classification = ?,
                control_mode = ?,
                escalation_required = ?,
                completed_at = ?
            WHERE investigation_id = ?
            """,
            (
                "Completed",
                governance[
                    "risk_score"
                ],
                summary[
                    "classification"
                ],
                mode,
                int(
                    governance[
                        "escalation_required"
                    ]
                ),
                completed_at,
                investigation_id,
            ),
        )

        conn.execute(
            """
            UPDATE cases
            SET
                status = ?,
                updated_at = ?
            WHERE case_id = ?
            """,
            (
                case_status,
                completed_at,
                case_id,
            ),
        )

        add_audit(
            conn,
            case_id,
            "SOC Orchestrator",
            (
                "Multi-agent investigation "
                "completed"
            ),
            mode,
            "Success",
            {
                "investigation_id":
                    investigation_id,
                "risk_score":
                    governance[
                        "risk_score"
                    ],
                "route":
                    governance[
                        "route"
                    ],
            },
        )

        conn.commit()

        return {
            "case_id": case_id,
            "investigation_id":
                investigation_id,
            "correlation": correlation,
            "threat_intel":
                threat_intel,
            "asset_context":
                asset_context,
            "governance":
                governance,
            "summary":
                summary,
            "model_metadata": {
                "correlation":
                    correlation_result[
                        "metadata"
                    ],
                "summary":
                    summary_result[
                        "metadata"
                    ],
            },
        }

    except Exception as exc:
        conn.rollback()

        conn.execute(
            """
            UPDATE investigations
            SET
                status = ?,
                completed_at = ?
            WHERE investigation_id = ?
            """,
            (
                "Failed",
                now(),
                investigation_id,
            ),
        )

        add_audit(
            conn,
            case_id,
            "SOC Orchestrator",
            "Multi-agent investigation failed",
            "SYSTEM",
            "Failed",
            {
                "error": str(exc),
                "investigation_id":
                    investigation_id,
            },
        )

        conn.commit()

        raise

    finally:
        conn.close()


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: "
            "python "
            "agents/multi_agent_orchestrator.py "
            "ALT-2401"
        )

        raise SystemExit(1)

    alert_id = sys.argv[1]

    print()
    print("=" * 62)
    print("AEGIS MULTI-AGENT SOC INVESTIGATION")
    print("=" * 62)

    print(
        f"Alert: {alert_id}"
    )

    print(
        "Model Runtime: qwen3:8b"
    )

    print(
        "Governance: Deterministic"
    )

    print("=" * 62)

    result = run_pipeline(
        alert_id
    )

    governance = result[
        "governance"
    ]

    summary = result[
        "summary"
    ]

    print()
    print("=" * 62)
    print(
        "MULTI-AGENT INVESTIGATION COMPLETE"
    )
    print("=" * 62)

    print(
        f"Case: "
        f"{result['case_id']}"
    )

    print(
        f"Investigation: "
        f"{result['investigation_id']}"
    )

    print(
        f"Classification: "
        f"{summary['classification']}"
    )

    print(
        f"Severity: "
        f"{summary['severity']}"
    )

    print(
        f"Confidence: "
        f"{summary['confidence']}%"
    )

    print(
        f"Risk Score: "
        f"{governance['risk_score']}"
    )

    print(
        f"Control Mode: "
        f"{governance['control_mode']}"
    )

    print(
        f"Route: "
        f"{governance['route']}"
    )

    print(
        f"Escalation: "
        f"{governance['escalation_required']}"
    )

    print()
    print("Executive Summary:")

    print(
        summary[
            "executive_summary"
        ]
    )

    print("=" * 62)


if __name__ == "__main__":
    main()
