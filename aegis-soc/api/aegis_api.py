"""AEGIS SOC local investigation runtime API.

Restore to: aegis-soc/api/aegis_api.py

GET  /health       Health probe used by Streamlit and n8n.
POST /investigate  Runs the existing multi-agent orchestrator and returns its
                   actual investigation result, not synthetic placeholders.

This is a compatible reconstruction of the previously working API contract.
It does not change agent logic, governance policy, or database tables.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = PROJECT_ROOT / "agents"
# Existing AEGIS agent files may import their siblings as top-level modules.
# Making this directory importable retains compatibility with that layout.
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from agents.multi_agent_orchestrator import run_pipeline  # noqa: E402


log = logging.getLogger(__name__)
app = FastAPI(
    title="AEGIS SOC Runtime API",
    description="Local governed multi-agent SOC investigation prototype",
    version="1.0.0",
)


class InvestigationRequest(BaseModel):
    alert_id: str = Field(min_length=1, max_length=128)

    @field_validator("alert_id")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("alert_id cannot be blank")
        return value


def _dict(value: Any, field_name: str) -> dict[str, Any]:
    """Normalize a plain mapping or a Pydantic result to a dictionary."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if not isinstance(value, dict):
        raise TypeError(f"Orchestrator result {field_name!r} must be an object")
    return value


def _agent_output(value: Any, field_name: str) -> dict[str, Any]:
    """Some agents return {output, metadata}, others return raw output."""
    data = _dict(value, field_name)
    if "output" in data:
        return _dict(data["output"], f"{field_name}.output")
    return data


def _required(source: dict[str, Any], key: str) -> Any:
    if key not in source:
        raise KeyError(f"Investigation output is missing {key!r}")
    return source[key]


def _first_mapping(result: dict[str, Any], *names: str) -> dict[str, Any]:
    for name in names:
        if name in result:
            return _dict(result[name], name)
    raise KeyError(f"Orchestrator output is missing: {' / '.join(names)}")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "AEGIS SOC Runtime API",
        "runtime": "Python Multi-Agent Engine",
    }


@app.post("/investigate")
def investigate(payload: InvestigationRequest) -> dict[str, Any]:
    """Run the REAL AEGIS five-agent pipeline and report its governance result.

    The orchestrator is responsible for recording agent outputs and the
    investigation in SQLite. The API does not duplicate those writes.
    """
    try:
        result = _dict(run_pipeline(payload.alert_id), "pipeline")
        governance_wrapped = _first_mapping(
            result, "governance", "risk_governance", "governance_result"
        )
        summary_wrapped = _first_mapping(
            result, "summary", "incident_summary", "summary_result"
        )
        governance = _agent_output(governance_wrapped, "governance")
        summary = _agent_output(summary_wrapped, "summary")

        model_metadata = result.get("model_metadata") or {}
        if not isinstance(model_metadata, dict):
            model_metadata = {}

        return {
            "status": "success",
            "alert_id": result.get("alert_id", payload.alert_id),
            "case_id": _required(result, "case_id"),
            "investigation_id": _required(result, "investigation_id"),
            "classification": _required(summary, "classification"),
            "severity": _required(summary, "severity"),
            "confidence": _required(summary, "confidence"),
            "risk_score": _required(governance, "risk_score"),
            "control_mode": _required(governance, "control_mode"),
            "route": _required(governance, "route"),
            "escalation_required": _required(governance, "escalation_required"),
            "policy_rationale": governance.get("policy_rationale", ""),
            "executive_summary": summary.get("executive_summary", ""),
            "recommended_actions": summary.get("recommended_actions", []),
            "model_metadata": {
                "correlation": model_metadata.get("correlation", {}),
                "summary": model_metadata.get("summary", summary_wrapped.get("metadata", {})),
            },
        }
    except ValueError as exc:
        # The original AEGIS orchestrator uses ValueError for unknown alerts.
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("AEGIS investigation failed for alert %s", payload.alert_id)
        raise HTTPException(
            status_code=500,
            detail="AEGIS investigation failed; check the Uvicorn terminal log",
        ) from exc
