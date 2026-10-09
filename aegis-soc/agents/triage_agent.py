import json
import os
import sqlite3
import sys
import uuid

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from context_loader import build_case_context
from ollama_client import chat_json


ROOT = Path(__file__).resolve().parent.parent
_db_setting = os.getenv("AEGIS_DB_PATH", "").strip()
DB_PATH = Path(_db_setting).expanduser() if _db_setting else ROOT / "database" / "aegis.db"
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
DB_PATH = DB_PATH.resolve()


# =========================================================
# STRUCTURED LLM OUTPUT
# =========================================================

class TriageAssessment(BaseModel):
    classification: str

    severity: str

    confidence: int = Field(
        ge=0,
        le=100,
    )

    evidence: list[str]

    mitre_techniques: list[str]

    summary: str

    recommended_actions: list[str]

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value):
        """
        Accept confidence in either:
        - 0.96 form
        - 96 form
        - 96.0 form
        - "96%" form

        Normalize everything to integer percentage 0-100.
        """

        if isinstance(value, str):
            value = value.strip().replace("%", "")

            try:
                value = float(value)
            except ValueError as exc:
                raise ValueError(
                    "Confidence must be numeric."
                ) from exc

        if isinstance(value, (int, float)):
            if 0 <= value <= 1:
                value = value * 100

            return int(round(value))

        raise ValueError(
            "Confidence must be a number between 0 and 100."
        )


# =========================================================
# DETERMINISTIC GOVERNANCE ENGINE
# =========================================================

def calculate_governance(context):
    alert = context["alert"]
    asset = context.get("asset") or {}
    identity = (
        context.get("identity")
        or {}
    )
    ti = (
        context.get("threat_intel")
        or {}
    )

    severity_base = {
        "Critical": 70,
        "High": 55,
        "Medium": 35,
        "Low": 15,
    }

    score = severity_base.get(
        alert.get("severity"),
        25,
    )

    # Detection confidence contribution
    detection_confidence = int(
        alert.get(
            "detection_confidence",
            0,
        )
    )

    score += round(
        detection_confidence * 0.10
    )

    # Asset criticality
    asset_weight = float(
        asset.get(
            "risk_weight",
            0,
        )
    )

    score += round(
        asset_weight * 10
    )

    # Threat intelligence
    reputation = ti.get(
        "reputation",
        "Unknown",
    )

    if reputation == "Malicious":
        score += 10

    elif reputation == "Suspicious":
        score += 5

    # Identity risk
    identity_risk = identity.get(
        "risk_level"
    )

    if identity_risk == "High":
        score += 5

    elif identity_risk == "Medium":
        score += 2

    # Privileged identity
    if (
        identity.get(
            "privilege_level"
        )
        == "Privileged"
    ):
        score += 5

    score = max(
        0,
        min(
            score,
            100,
        ),
    )

    critical_asset = (
        asset.get("criticality")
        == "Critical"
    )

    malicious_ioc = (
        reputation
        == "Malicious"
    )

    # ---------------------------------------------
    # Governance policy
    # ---------------------------------------------

    if (
        critical_asset
        and malicious_ioc
    ):
        control_mode = (
            "[E] Escalation"
        )

        escalation_required = True

        rationale = (
            "Critical asset combined with "
            "confirmed malicious threat "
            "intelligence."
        )

    elif score >= 75:
        control_mode = (
            "[H] HITL"
        )

        escalation_required = False

        rationale = (
            "Risk score meets mandatory "
            "Human-in-the-Loop threshold."
        )

    else:
        control_mode = (
            "[A] Autonomous"
        )

        escalation_required = False

        rationale = (
            "Risk remains within governed "
            "autonomous triage threshold."
        )

    return {
        "risk_score": score,
        "control_mode": control_mode,
        "escalation_required":
            escalation_required,
        "policy_rationale":
            rationale,
    }


# =========================================================
# LLM ANALYSIS
# =========================================================

SYSTEM_PROMPT = """
You are the AEGIS SOC Triage Agent.

Analyse only the evidence supplied to you.

Do not invent:
- phishing emails
- macros
- exploits
- malware families
- attacker identity
- persistence
- lateral movement
unless explicitly supported by evidence.

Your task is evidence analysis, not governance.

Return ONLY valid JSON using this exact structure:

{
  "classification": "True Positive | Likely False Positive | Requires Additional Context",
  "severity": "Critical | High | Medium | Low",
  "confidence": 96,
  "evidence": [
    "Evidence statement"
  ],
  "mitre_techniques": [
    "TXXXX"
  ],
  "summary": "Concise incident summary",
  "recommended_actions": [
    "Non-destructive analyst recommendation"
  ]
}

Confidence MUST be returned as an integer percentage from 0 to 100.
Example: use 96, never 0.96.

Never include chain-of-thought or hidden reasoning.
"""


def run_triage(alert_id):
    context = build_case_context(
        alert_id
    )

    user_prompt = (
        "Analyse the following synthetic "
        "SOC evidence.\n\n"
        + json.dumps(
            context,
            indent=2,
        )
    )

    raw_output, metadata = chat_json(
        SYSTEM_PROMPT,
        user_prompt,
    )

    assessment = (
        TriageAssessment
        .model_validate(
            raw_output
        )
    )

    governance = (
        calculate_governance(
            context
        )
    )

    return {
        "alert_id": alert_id,
        "model_assessment":
            assessment.model_dump(),
        "governance":
            governance,
        "model_metadata":
            metadata,
        "context":
            context,
    }


# =========================================================
# SQLITE PERSISTENCE
# =========================================================

def persist_result(result):
    alert_id = result["alert_id"]

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:
        row = conn.execute(
            """
            SELECT case_id
            FROM cases
            WHERE alert_id = ?
            """,
            (alert_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                f"No database case exists "
                f"for {alert_id}"
            )

        case_id = row[0]

        investigation_id = (
            "INV-"
            + uuid.uuid4()
            .hex[:8]
            .upper()
        )

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        assessment = result[
            "model_assessment"
        ]

        governance = result[
            "governance"
        ]

        conn.execute(
            """
            INSERT INTO investigations (
                investigation_id,
                case_id,
                status,
                overall_risk_score,
                classification,
                control_mode,
                escalation_required,
                started_at,
                completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                investigation_id,
                case_id,
                "Completed",
                governance[
                    "risk_score"
                ],
                assessment[
                    "classification"
                ],
                governance[
                    "control_mode"
                ],
                int(
                    governance[
                        "escalation_required"
                    ]
                ),
                now,
                now,
            ),
        )

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
                "AEGIS Triage Agent",
                json.dumps(
                    result,
                    ensure_ascii=False,
                ),
                assessment[
                    "confidence"
                ],
                now,
            ),
        )

        control_mode = governance[
            "control_mode"
        ]

        if control_mode.startswith(
            "[E]"
        ):
            new_status = "Escalated"

        elif control_mode.startswith(
            "[H]"
        ):
            new_status = (
                "Awaiting HITL"
            )

        else:
            new_status = "Triaged"

        conn.execute(
            """
            UPDATE cases
            SET
                status = ?,
                updated_at = ?
            WHERE case_id = ?
            """,
            (
                new_status,
                now,
                case_id,
            ),
        )

        conn.execute(
            """
            INSERT INTO audit_events (
                case_id,
                actor,
                action,
                control_mode,
                status,
                details_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                "AEGIS Triage Agent",
                (
                    "AI-assisted SOC "
                    "triage completed"
                ),
                control_mode,
                "Success",
                json.dumps(
                    {
                        "investigation_id":
                            investigation_id,
                        "model":
                            result[
                                "model_metadata"
                            ]["model"],
                        "risk_score":
                            governance[
                                "risk_score"
                            ],
                    }
                ),
                now,
            ),
        )

        conn.commit()

        return (
            investigation_id,
            case_id,
        )

    finally:
        conn.close()


# =========================================================
# CLI
# =========================================================

def main():
    if len(sys.argv) != 2:
        print(
            "Usage: "
            "python agents/triage_agent.py "
            "ALT-2401"
        )

        raise SystemExit(1)

    alert_id = sys.argv[1]

    print(
        f"\nRunning AEGIS triage "
        f"for {alert_id}..."
    )

    print(
        "Model: qwen3:8b"
    )

    print(
        "Thinking: DISABLED"
    )

    result = run_triage(
        alert_id
    )

    investigation_id, case_id = (
        persist_result(
            result
        )
    )

    print(
        "\n"
        + "=" * 58
    )

    print(
        "AEGIS AI INVESTIGATION COMPLETE"
    )

    print(
        "=" * 58
    )

    print(
        f"Case: {case_id}"
    )

    print(
        f"Investigation: "
        f"{investigation_id}"
    )

    print(
        f"Classification: "
        f"{result['model_assessment']['classification']}"
    )

    print(
        f"AI Severity: "
        f"{result['model_assessment']['severity']}"
    )

    print(
        f"AI Confidence: "
        f"{result['model_assessment']['confidence']}%"
    )

    print(
        f"Governed Risk Score: "
        f"{result['governance']['risk_score']}"
    )

    print(
        f"Control Mode: "
        f"{result['governance']['control_mode']}"
    )

    print(
        f"Escalation Required: "
        f"{result['governance']['escalation_required']}"
    )

    print(
        f"Model Latency: "
        f"{result['model_metadata']['latency_seconds']}s"
    )

    print(
        "\nSummary:"
    )

    print(
        result[
            "model_assessment"
        ]["summary"]
    )

    print(
        "=" * 58
    )


if __name__ == "__main__":
    main()
