import json

from pydantic import BaseModel, Field, field_validator

from ollama_client import chat_json


class CorrelationResult(BaseModel):
    correlated_events: list[str]
    attack_pattern: str
    confidence: int = Field(ge=0, le=100)
    mitre_techniques: list[str]
    evidence_gaps: list[str]

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
You are the AEGIS Correlation Agent.

Your role is to correlate security telemetry and identify
relationships between observed events.

Use ONLY supplied evidence.

Do not invent:
- phishing emails
- malware families
- persistence
- lateral movement
- exploits
unless explicitly supported.

Return ONLY JSON:

{
  "correlated_events": [
    "Evidence-backed relationship"
  ],
  "attack_pattern": "Concise pattern description",
  "confidence": 0,
  "mitre_techniques": [
    "TXXXX"
  ],
  "evidence_gaps": [
    "Missing evidence"
  ]
}

Confidence must be an integer percentage from 0 to 100.
Do not expose chain-of-thought.
"""


def run_correlation(context):
    evidence = {
        "alert": context.get("alert"),
        "identity": context.get("identity"),
        "asset": context.get("asset"),
    }

    output, metadata = chat_json(
        SYSTEM_PROMPT,
        json.dumps(
            evidence,
            indent=2,
        ),
    )

    validated = CorrelationResult.model_validate(
        output
    )

    return {
        "output": validated.model_dump(),
        "metadata": metadata,
    }
