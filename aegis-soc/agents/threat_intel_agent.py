def run_threat_intel(context):
    alert = context.get("alert") or {}
    intel = context.get("threat_intel")

    if not intel:
        return {
            "indicator": alert.get("ip"),
            "match_found": False,
            "reputation": "Unknown",
            "confidence": 0,
            "threat_category": "Unclassified",
            "source": "No matching intelligence",
            "is_malicious": False,
        }

    reputation = intel.get(
        "reputation",
        "Unknown",
    )

    return {
        "indicator": intel.get("indicator"),
        "match_found": True,
        "reputation": reputation,
        "confidence": intel.get(
            "confidence",
            0,
        ),
        "threat_category": intel.get(
            "threat_category",
            "Unclassified",
        ),
        "source": intel.get(
            "source",
            "AEGIS Synthetic TI Feed",
        ),
        "is_malicious":
            reputation == "Malicious",
    }
