"""Read-only consolidated audit access across agents and app-level actions."""

from __future__ import annotations

import json
from typing import Any

from database.repository import AegisRepository
from services.store import fetch_app_rows


def list_combined_audit(*, limit: int = 100) -> list[dict[str, Any]]:
    """Return recent original AEGIS events and analyst action events.

    Separate origin fields ensure that demo audit events are never represented
    as native agent logs. No historical audit record is altered.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    native = AegisRepository().list_audit_events(limit=limit)
    app_events = fetch_app_rows("aegis_app_audit_events", limit=limit)
    for row in native:
        row["origin"] = "agent_runtime"
    for row in app_events:
        row["origin"] = "analyst_application"
        try:
            row["details"] = json.loads(row.pop("detail_json"))
        except (ValueError, TypeError, KeyError):
            row["details"] = {}
    combined = native + app_events
    combined.sort(
        key=lambda row: str(next(
            (row[key] for key in (
                "created_at", "recorded_at", "event_timestamp", "timestamp", "event_time"
            ) if row.get(key)), ""
        )),
        reverse=True,
    )
    return combined[:limit]
