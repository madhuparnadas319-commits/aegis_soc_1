"""Pydantic API contracts for AEGIS SOC.

Save as: aegis-soc/api/schemas.py

These schemas describe requests and responses exchanged by Streamlit,
FastAPI, and the n8n governance workflow. This file does not replace the
existing FastAPI application or change the SQLite database.

Compatible with Pydantic 2.x and the current AEGIS /investigate response.
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


ControlMode = Literal["[A] Autonomous", "[H] HITL", "[E] Escalation"]
ReviewDecision = Literal["approve", "reject", "request_more_evidence"]
EscalationAction = Literal["acknowledge", "assign", "resolve"]


class APIModel(BaseModel):
    """Accept non-breaking metadata additions from future AEGIS versions."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)


class HealthResponse(APIModel):
    """Existing GET /health response."""

    status: str = Field(description="Typically 'ok' when the service is healthy")
    service: str
    runtime: str


class InvestigationRequest(BaseModel):
    """Existing POST /investigate and n8n webhook request."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    alert_id: str = Field(min_length=1, max_length=128)

    @field_validator("alert_id")
    @classmethod
    def validate_alert_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("alert_id cannot be blank")
        return value


class ModelRunMetadata(APIModel):
    """Optional timing/token information from an Ollama agent call."""

    model: str | None = None
    latency_seconds: float | None = Field(default=None, ge=0)
    total_duration_ns: int | None = Field(default=None, ge=0)
    prompt_eval_count: int | None = Field(default=None, ge=0)
    eval_count: int | None = Field(default=None, ge=0)
    done_reason: str | None = None


class InvestigationResponse(APIModel):
    """Successful AEGIS investigation result, before or after n8n routing.

    ``workflow_route`` and ``workflow_status`` are optional because FastAPI
    may return the investigation before n8n adds those two fields.
    """

    status: str
    alert_id: str
    case_id: str
    investigation_id: str
    classification: str
    severity: str
    confidence: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    control_mode: ControlMode
    route: str
    escalation_required: bool
    policy_rationale: str = ""
    executive_summary: str = ""
    recommended_actions: list[str] = Field(default_factory=list)
    model_metadata: dict[str, ModelRunMetadata] = Field(default_factory=dict)
    workflow_route: str | None = None
    workflow_status: str | None = None


class CaseRecord(APIModel):
    """Core case attributes. Extra fields from SQLite are preserved."""

    case_id: str
    alert_id: str | None = None
    status: str | None = None


class InvestigationRecord(APIModel):
    """Core investigation attributes. Extra SQLite columns are preserved."""

    investigation_id: str
    case_id: str | None = None
    alert_id: str | None = None
    classification: str | None = None
    control_mode: str | None = None
    risk_score: float | None = None


ItemT = TypeVar("ItemT")


class PaginatedResponse(APIModel, Generic[ItemT]):
    """Generic response envelope for future GET /cases and history APIs."""

    items: list[ItemT]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=1000)
    offset: int = Field(ge=0)


class HITLDecisionRequest(BaseModel):
    """Human analyst action contract; backend persistence comes later."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: str = Field(min_length=1)
    investigation_id: str = Field(min_length=1)
    analyst_id: str = Field(min_length=1)
    decision: ReviewDecision
    rationale: str = Field(min_length=1, max_length=5000)

    @field_validator("case_id", "investigation_id", "analyst_id", "rationale")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field cannot be blank")
        return value


class EscalationActionRequest(BaseModel):
    """Analyst actions on escalated incidents; implementation comes later."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: str = Field(min_length=1)
    investigation_id: str = Field(min_length=1)
    analyst_id: str = Field(min_length=1)
    action: EscalationAction
    rationale: str = Field(min_length=1, max_length=5000)
    assignee: str | None = None

    @field_validator("case_id", "investigation_id", "analyst_id", "rationale")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field cannot be blank")
        return value


class ErrorResponse(BaseModel):
    """Consistent structure for future API error responses."""

    detail: str
    code: str | None = None


__all__ = [
    "ControlMode",
    "ReviewDecision",
    "EscalationAction",
    "HealthResponse",
    "InvestigationRequest",
    "ModelRunMetadata",
    "InvestigationResponse",
    "CaseRecord",
    "InvestigationRecord",
    "PaginatedResponse",
    "HITLDecisionRequest",
    "EscalationActionRequest",
    "ErrorResponse",
]
