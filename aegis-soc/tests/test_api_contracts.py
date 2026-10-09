"""Validation tests for previously supplied api/schemas.py."""

import pytest
from pydantic import ValidationError

from api.schemas import InvestigationRequest, InvestigationResponse


def test_alert_request_strips_whitespace():
    assert InvestigationRequest(alert_id=" ALT-2404 ").alert_id == "ALT-2404"


def test_blank_alert_rejected():
    with pytest.raises(ValidationError):
        InvestigationRequest(alert_id=" ")


def test_actual_investigation_response_shape():
    payload = dict(
        status="success", alert_id="ALT-2404", case_id="CASE-2404",
        investigation_id="INV-1234", classification="Likely False Positive",
        severity="Medium", confidence=78, risk_score=62,
        control_mode="[A] Autonomous", route="Autonomous Triage",
        escalation_required=False, recommended_actions=[], model_metadata={},
        workflow_route="autonomous", workflow_status="auto_triaged",
    )
    result = InvestigationResponse.model_validate(payload)
    assert result.control_mode == "[A] Autonomous"
