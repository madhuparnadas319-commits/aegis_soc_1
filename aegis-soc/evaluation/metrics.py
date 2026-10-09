"""Pure functions for transparent triage-classification benchmark metrics."""

from __future__ import annotations

from collections import Counter
from statistics import mean, median
from typing import Any


def normalize_label(value: str) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def classification_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return accuracy and per-class/macro F1 from labeled benchmark rows.

    Excludes invalid/missing responses from accuracy denominator only by
    counting them as incorrect predictions; reports their number explicitly.
    """
    if not rows:
        return {"count": 0, "accuracy": None, "macro_f1": None,
                "per_class": {}, "invalid_predictions": 0}
    truth = [normalize_label(row["expected_classification"]) for row in rows]
    predicted = [normalize_label(row.get("predicted_classification", "")) for row in rows]
    classes = sorted(set(truth))
    correct = sum(a == b for a, b in zip(truth, predicted))
    scores: dict[str, Any] = {}
    for label in classes:
        tp = sum(a == label and b == label for a, b in zip(truth, predicted))
        fp = sum(a != label and b == label for a, b in zip(truth, predicted))
        fn = sum(a == label and b != label for a, b in zip(truth, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores[label] = {
            "support": Counter(truth)[label], "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4),
        }
    latencies = [float(r["latency_seconds"]) for r in rows
                 if r.get("latency_seconds") is not None]
    return {
        "count": len(rows), "accuracy": round(correct / len(rows), 4),
        "macro_f1": round(mean(item["f1"] for item in scores.values()), 4),
        "per_class": scores,
        "invalid_predictions": sum(not x for x in predicted),
        "mean_latency_seconds": round(mean(latencies), 3) if latencies else None,
        "median_latency_seconds": round(median(latencies), 3) if latencies else None,
    }
