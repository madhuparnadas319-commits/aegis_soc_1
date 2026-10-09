import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_json(filename):
    path = DATA_DIR / filename

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def find_item(
    items,
    field,
    value,
):
    for item in items:
        if item.get(field) == value:
            return item

    return None


def build_case_context(alert_id):
    alerts = load_json(
        "alerts.json"
    )["alerts"]

    assets = load_json(
        "assets.json"
    )["assets"]

    identities = load_json(
        "identities.json"
    )["identities"]

    indicators = load_json(
        "threat_intel.json"
    )["indicators"]

    alert = find_item(
        alerts,
        "alert_id",
        alert_id,
    )

    if alert is None:
        raise ValueError(
            f"Alert not found: {alert_id}"
        )

    asset = find_item(
        assets,
        "asset_id",
        alert.get("asset_id"),
    )

    identity = find_item(
        identities,
        "user_id",
        alert.get("user_id"),
    )

    threat_intel = find_item(
        indicators,
        "indicator",
        alert.get("ip"),
    )

    return {
        "alert": alert,
        "asset": asset,
        "identity": identity,
        "threat_intel": threat_intel,
    }
