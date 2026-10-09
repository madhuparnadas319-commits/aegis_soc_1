"""Sanity tests for model comparison math."""

from evaluation.metrics import classification_metrics, normalize_label


def test_normalization():
    assert normalize_label(" True_Positive ") == "true positive"


def test_perfect_predictions():
    rows = [
        {"expected_classification": "True Positive", "predicted_classification": "True Positive", "latency_seconds": 1.0},
        {"expected_classification": "Likely False Positive", "predicted_classification": "Likely False Positive", "latency_seconds": 3.0},
    ]
    metrics = classification_metrics(rows)
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["mean_latency_seconds"] == 2.0


def test_missing_prediction_counts_as_error():
    metrics = classification_metrics([
        {"expected_classification": "True Positive", "predicted_classification": ""},
    ])
    assert metrics["accuracy"] == 0.0
    assert metrics["invalid_predictions"] == 1
