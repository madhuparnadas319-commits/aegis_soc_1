import json

from pydantic import BaseModel, Field, field_validator

from ollama_client import chat_json


class IncidentSummary(BaseModel):
    classification: str
    severity: str
    confidence: int = Field(ge=0, le=100)
    executive_summary: str
    evidence_summary: list[str]
    recommended_actions: list[str]
    analyst_note: str

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value):
        if isinstance(value, str):
            value = value.strip().replace("%", "")
            value = float(value)

        if isinstance(value, (int, float)):
            if 0 <= value <= 1:
                value *= 100

            return int(round(value))

        raise ValueError("Invalid confidence value")


SYSTEM_PROMPT = """
You are the AEGIS Incident Summary Agent.

Produce a concise analyst-ready SOC incident summary
using ONLY the supplied outputs.

Do not invent evidence.

Governance decisions are deterministic and must not
be changed by you.

Return ONLY JSON:

{
  "classification": "True Positive | Likely False Positive | Requires Additional Context",
  "severity": "Critical | High | Medium | Low",
  "confidence": 0,
  "executive_summary": "Concise incident summary",
  "evidence_summary": [
    "Evidence statement"
  ],
  "recommended_actions": [
    "Non-destructive recommendation"
  ],
  "analyst_note": "Short note for SOC analyst"
}

Confidence must be an integer percentage from 0 to 100.
Do not expose chain-of-thought.
"""


def run_incident_summary(
    context,
    correlation,
    threat_intel,
    asset_context,
    governance,
):
    payload = {
        "alert": context.get("alert"),
        "correlation": correlation,
        "threat_intelligence":
            threat_intel,
        "asset_context":
            asset_context,
        "governance":
            governance,
    }

    output, metadata = chat_json(
        SYSTEM_PROMPT,
        json.dumps(
            payload,
            indent=2,
        ),
    )

    validated = IncidentSummary.model_validate(
        output
    )

    return {
        "output": validated.model_dump(),
        "metadata": metadata,
    }
