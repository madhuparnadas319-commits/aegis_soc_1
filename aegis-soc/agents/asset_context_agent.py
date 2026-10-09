def run_asset_context(context):
    asset = context.get("asset") or {}
    identity = context.get("identity") or {}

    reasons = []

    modifier = 0

    criticality = asset.get(
        "criticality",
        "Unknown",
    )

    if criticality == "Critical":
        modifier += 15
        reasons.append(
            "Asset is business critical."
        )

    elif criticality == "High":
        modifier += 10
        reasons.append(
            "Asset has high business criticality."
        )

    elif criticality == "Medium":
        modifier += 5

    if asset.get("internet_exposed"):
        modifier += 5

        reasons.append(
            "Asset is internet exposed."
        )

    if asset.get("privileged_access"):
        modifier += 5

        reasons.append(
            "Asset supports privileged access."
        )

    privilege = identity.get(
        "privilege_level",
        "Unknown",
    )

    if privilege == "Privileged":
        modifier += 5

        reasons.append(
            "Associated identity is privileged."
        )

    identity_risk = identity.get(
        "risk_level",
        "Unknown",
    )

    if identity_risk == "High":
        modifier += 5

        reasons.append(
            "Identity carries elevated risk context."
        )

    return {
        "asset_id": asset.get(
            "asset_id"
        ),
        "business_unit": asset.get(
            "business_unit",
            "Unknown",
        ),
        "criticality": criticality,
        "data_classification": asset.get(
            "data_classification",
            "Unknown",
        ),
        "internet_exposed": bool(
            asset.get(
                "internet_exposed",
                False,
            )
        ),
        "privileged_access": bool(
            asset.get(
                "privileged_access",
                False,
            )
        ),
        "identity": identity.get(
            "username",
            "Unknown",
        ),
        "identity_privilege": privilege,
        "identity_risk": identity_risk,
        "risk_modifier": modifier,
        "context_reasons": reasons,
    }
