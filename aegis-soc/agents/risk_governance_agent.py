def run_risk_governance(
    context,
    correlation,
    threat_intel,
    asset_context,
):
    alert = context.get("alert") or {}

    severity_weights = {
        "Critical": 55,
        "High": 42,
        "Medium": 25,
        "Low": 10,
    }

    severity = alert.get(
        "severity",
        "Low",
    )

    score = severity_weights.get(
        severity,
        10,
    )

    detection_confidence = int(
        alert.get(
            "detection_confidence",
            0,
        )
    )

    score += round(
        detection_confidence * 0.15
    )

    score += int(
        asset_context.get(
            "risk_modifier",
            0,
        )
    )

    reputation = threat_intel.get(
        "reputation"
    )

    if reputation == "Malicious":
        score += 15

    elif reputation == "Suspicious":
        score += 7

    correlation_confidence = int(
        correlation.get(
            "confidence",
            0,
        )
    )

    if correlation_confidence >= 85:
        score += 5

    score = max(
        0,
        min(
            score,
            100,
        ),
    )

    critical_asset = (
        asset_context.get(
            "criticality"
        )
        == "Critical"
    )

    malicious_ioc = bool(
        threat_intel.get(
            "is_malicious"
        )
    )

    evidence_gaps = correlation.get(
        "evidence_gaps",
        [],
    )

    # =============================================
    # DETERMINISTIC GOVERNANCE POLICY
    # =============================================

    if (
        critical_asset
        and malicious_ioc
        and score >= 85
    ):
        control_mode = "[E] Escalation"

        route = "Escalation Center"

        escalation_required = True

        rationale = (
            "Critical asset combined with "
            "confirmed malicious IOC and "
            "high governed risk."
        )

    elif (
        score >= 75
        or correlation_confidence < 65
        or (
            len(evidence_gaps) >= 2
            and score >= 65
        )
    ):
        control_mode = "[H] HITL"

        route = "Human Review"

        escalation_required = False

        rationale = (
            "Risk or evidence-quality policy "
            "requires analyst review."
        )

    else:
        control_mode = "[A] Autonomous"

        route = "Autonomous Triage"

        escalation_required = False

        rationale = (
            "Risk is below HITL threshold, "
            "correlation confidence is adequate, "
            "and no mandatory escalation condition "
            "was triggered."
        )

    return {
        "risk_score": score,
        "control_mode": control_mode,
        "route": route,
        "escalation_required":
            escalation_required,
        "policy_rationale": rationale,
        "policy_inputs": {
            "alert_severity": severity,
            "detection_confidence":
                detection_confidence,
            "correlation_confidence":
                correlation_confidence,
            "asset_criticality":
                asset_context.get(
                    "criticality"
                ),
            "threat_reputation":
                reputation,
            "evidence_gap_count":
                len(evidence_gaps),
        },
    }
