"""AEGIS SOC read/API routes and persisted analyst action endpoints.

These routes have the /dashboard prefix and do not modify the existing
/health or /investigate endpoints. See api/dashboard_api.py for the additive
entrypoint that registers them against the existing FastAPI app.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.schemas import HITLDecisionRequest, EscalationActionRequest
from database.connection import DatabaseConnectionError
from database.repository import AegisRepository, RepositoryError
from services.audit_service import list_combined_audit
from services.escalation_service import (
    list_escalations, list_escalation_actions, record_escalation_action,
)
from services.hitl_service import list_pending_reviews, list_reviews, record_review
from services.store import RecordNotFound, InvalidAction, ActionConflict


router = APIRouter(prefix="/dashboard", tags=["AEGIS dashboard"])
repository = AegisRepository()


def _raise_data_error(exc: Exception) -> None:
    if isinstance(exc, RecordNotFound):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ActionConflict):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, (InvalidAction, ValueError)):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, (RepositoryError, DatabaseConnectionError)):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    raise exc


def _safe(operation):
    try:
        return operation()
    except (RecordNotFound, ActionConflict, InvalidAction, ValueError,
            RepositoryError, DatabaseConnectionError) as exc:
        _raise_data_error(exc)


@router.get("/overview")
def overview() -> dict[str, Any]:
    def result():
        return {
            "database": repository.get_table_counts(),
            "pending_reviews": len(list_pending_reviews(limit=1000)),
            "escalations": len(list_escalations(limit=1000)),
            "environment": "local_prototype",
            "banking_actions_enabled": False,
        }
    return _safe(result)


@router.get("/cases")
def cases(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: str | None = None,
) -> dict[str, Any]:
    return {"items": _safe(lambda: repository.list_cases(
        limit=limit, offset=offset, status=status
    )), "limit": limit, "offset": offset}


@router.get("/cases/{case_id}")
def case(case_id: str) -> dict[str, Any]:
    record = _safe(lambda: repository.get_case(case_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return record


@router.get("/investigations")
def investigations(
    alert_id: str | None = None,
    case_id: str | None = None,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return {"items": _safe(lambda: repository.list_investigations(
        alert_id=alert_id, case_id=case_id, limit=limit, offset=offset
    )), "limit": limit, "offset": offset}


@router.get("/investigations/{investigation_id}")
def investigation(investigation_id: str) -> dict[str, Any]:
    record = _safe(lambda: repository.get_investigation(investigation_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return record


@router.get("/investigations/{investigation_id}/agent-outputs")
def agent_outputs(investigation_id: str) -> dict[str, Any]:
    return {"items": _safe(lambda: repository.list_agent_outputs(investigation_id))}


@router.get("/queues/human-review")
def review_queue(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    return {"items": _safe(lambda: list_pending_reviews(limit=limit))}


@router.get("/queues/escalations")
def escalation_queue(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    return {"items": _safe(lambda: list_escalations(limit=limit))}


@router.get("/reviews")
def reviews(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    return {"items": _safe(lambda: list_reviews(limit=limit))}


@router.post("/reviews", status_code=201)
def submit_review(payload: HITLDecisionRequest) -> dict[str, Any]:
    return _safe(lambda: record_review(**payload.model_dump()))


@router.get("/escalation-actions")
def escalation_actions(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    return {"items": _safe(lambda: list_escalation_actions(limit=limit))}


@router.post("/escalation-actions", status_code=201)
def submit_escalation(payload: EscalationActionRequest) -> dict[str, Any]:
    return _safe(lambda: record_escalation_action(**payload.model_dump()))


@router.get("/audit")
def audit(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    return {"items": _safe(lambda: list_combined_audit(limit=limit))}


@router.get("/alerts")
def alerts() -> dict[str, Any]:
    """Read synthetic case fixtures without editing or persisting them."""
    path = Path(__file__).resolve().parents[1] / "data" / "alerts.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="data/alerts.json not found")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=500, detail="Invalid local alerts dataset") from exc
    if isinstance(data, list):
        return {"items": data}
    if isinstance(data, dict) and isinstance(data.get("alerts"), list):
        return {"items": data["alerts"]}
    raise HTTPException(status_code=500, detail="Unsupported alerts.json structure")
