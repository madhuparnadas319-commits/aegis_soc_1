"""Comparable local Ollama evaluation for three open-weight LLMs.

Only the model's triage classification is benchmarked. AEGIS deterministic
risk/governance routing is not inferred from these LLM outputs, and no
results are claimed until the user actually runs the benchmark.

Run only after all configured models are installed. By default, output is
written to evaluation/results/ and existing results remain preserved.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from evaluation.metrics import classification_metrics


ROOT = Path(__file__).resolve().parents[1]
PROMPT = (
    "You are a SOC alert triage classifier in a controlled offline demo. "
    "Assess only the provided synthetic alert context. "
    "Return a JSON object with exactly two keys: classification and rationale. "
    "classification must be either 'True Positive' or 'Likely False Positive'. "
    "Do not assume unprovided evidence. Keep rationale under 90 words."
)


def load_cases() -> list[dict[str, Any]]:
    with (ROOT / "evaluation" / "expected_outcomes.json").open(encoding="utf-8") as file:
        reference = json.load(file)["cases"]
    with (ROOT / "data" / "alerts.json").open(encoding="utf-8") as file:
        alerts = json.load(file)
    if isinstance(alerts, dict):
        alerts = alerts.get("alerts", [])
    if not isinstance(alerts, list):
        raise ValueError("data/alerts.json must contain a list or {'alerts': [...]} object")
    result = []
    for alert in alerts:
        alert_id = alert.get("alert_id") if isinstance(alert, dict) else None
        if alert_id in reference:
            result.append({"alert_id": alert_id, "alert": alert,
                           "expected_classification": reference[alert_id]["expected_classification"]})
    missing = set(reference) - {r["alert_id"] for r in result}
    if missing:
        raise ValueError(f"Missing benchmark case alerts from alerts.json: {sorted(missing)}")
    return result


def installed_models(session: requests.Session, url: str) -> set[str]:
    response = session.get(f"{url}/api/tags", timeout=(5, 20))
    response.raise_for_status()
    return {str(item["name"]) for item in response.json().get("models", [])}


def evaluate_model(
    model: str, cases: list[dict[str, Any]],
    session: requests.Session, url: str, timeout: int,
) -> dict[str, Any]:
    rows = []
    for case in cases:
        start = time.monotonic()
        record = {"alert_id": case["alert_id"],
                  "expected_classification": case["expected_classification"],
                  "predicted_classification": "", "error": None}
        try:
            response = session.post(
                f"{url}/api/chat",
                json={
                    "model": model, "stream": False, "think": False,
                    "format": "json", "options": {"temperature": 0},
                    "messages": [
                        {"role": "system", "content": PROMPT},
                        {"role": "user", "content": json.dumps(case["alert"], sort_keys=True)},
                    ],
                },
                timeout=(5, timeout),
            )
            response.raise_for_status()
            output = json.loads(response.json()["message"]["content"])
            predicted = str(output.get("classification", "")).strip()
            valid_labels = {"True Positive", "Likely False Positive"}
            if predicted not in valid_labels:
                raise ValueError(f"Unexpected classification label: {predicted!r}")
            record["predicted_classification"] = predicted
            record["rationale"] = str(output.get("rationale", ""))
        except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
            record["error"] = str(exc)
        record["latency_seconds"] = round(time.monotonic() - start, 3)
        rows.append(record)
    return {"model": model, "rows": rows, "metrics": classification_metrics(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="AEGIS three-model triage benchmark")
    parser.add_argument("--url", default=os.getenv("AEGIS_OLLAMA_URL", "http://localhost:11434"))
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--models", nargs="+", help="Override model list from registry")
    args = parser.parse_args()
    registry = json.loads((ROOT / "evaluation" / "model_registry.json").read_text(encoding="utf-8"))
    models = args.models or [item["id"] for item in registry["models"]]
    cases = load_cases()
    session = requests.Session()
    present = installed_models(session, args.url.rstrip("/"))
    missing = [model for model in models if model not in present]
    if missing:
        raise SystemExit("Models not installed in Ollama: " + ", ".join(missing))
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "type": "triage_classification_only",
        "prompt": PROMPT,
        "cases": [item["alert_id"] for item in cases],
        "results": [evaluate_model(
            model, cases, session, args.url.rstrip("/"), args.timeout
        ) for model in models],
    }
    directory = ROOT / "evaluation" / "results"
    directory.mkdir(parents=True, exist_ok=True)
    file = directory / f"benchmark_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Saved real benchmark data to: {file}")
    for item in output["results"]:
        print(item["model"], item["metrics"])


if __name__ == "__main__":
    main()
