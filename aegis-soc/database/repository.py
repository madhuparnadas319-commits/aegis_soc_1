"""Read-only SQLite repository for AEGIS SOC.

Save as: aegis-soc/database/repository.py

Exposes the existing case, investigation, agent-output, HITL-decision and
audit-event tables to the dashboard/API. This module does not create tables,
change the schema, or alter existing records.

The exact column layout may vary across AEGIS prototype versions. Repository
methods inspect the existing table columns instead of assuming timestamps or
status fields that may not exist. Human decisions and escalation writes will
be handled by dedicated, schema-aware services.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from database.connection import db_session


_TABLES = frozenset(
    {"cases", "investigations", "agent_outputs", "hitl_decisions", "audit_events"}
)
_ORDER_PREFERENCE = (
    "created_at",
    "started_at",
    "completed_at",
    "recorded_at",
    "event_timestamp",
    "timestamp",
    "investigated_at",
    "updated_at",
    "event_time",
    "id",
)
_MAX_PAGE_SIZE = 1000


class RepositoryError(RuntimeError):
    """Raised when a repository query is incompatible with the existing DB."""


def _quoted(identifier: str) -> str:
    """Quote internal or schema-discovered SQLite identifiers safely."""
    return '"' + identifier.replace('"', '""') + '"'


def _validate_table(table: str) -> None:
    if table not in _TABLES:
        raise RepositoryError(f"Unsupported AEGIS table: {table!r}")


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    _validate_table(table)
    rows = conn.execute(f"PRAGMA table_info({_quoted(table)})").fetchall()
    if not rows:
        raise RepositoryError(
            f"AEGIS database table {table!r} was not found. "
            "Check that this is the database used by the agent orchestrator."
        )
    return {str(row[1]) for row in rows}


def _page(limit: int, offset: int) -> tuple[int, int]:
    if type(limit) is not int or not (1 <= limit <= _MAX_PAGE_SIZE):
        raise ValueError(f"limit must be an integer from 1 to {_MAX_PAGE_SIZE}")
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    return limit, offset


def _order_sql(columns: set[str]) -> str:
    # Ordering only references schema-discovered columns, never user input.
    for preferred in _ORDER_PREFERENCE:
        if preferred in columns:
            return f" ORDER BY {_quoted(preferred)} DESC, rowid DESC"
    return ""  # No sorting assumption if this table lacks a known date/id.


def _select(
    table: str,
    *,
    filters: dict[str, Any] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Read rows from one of the known AEGIS tables with safe bindings."""
    _validate_table(table)
    limit, offset = _page(limit, offset)
    filters = {key: val for key, val in (filters or {}).items() if val is not None}

    with db_session(read_only=True) as conn:
        columns = _columns(conn, table)
        missing = set(filters) - columns
        if missing:
            raise RepositoryError(
                f"Table {table!r} has no column(s): {', '.join(sorted(missing))}. "
                f"Available columns: {', '.join(sorted(columns))}"
            )

        statement = f"SELECT * FROM {_quoted(table)}"
        params: list[Any] = []
        if filters:
            clauses = []
            for key, value in filters.items():
                clauses.append(f"{_quoted(key)} = ?")
                params.append(value)
            statement += " WHERE " + " AND ".join(clauses)
        statement += _order_sql(columns)
        statement += " LIMIT ? OFFSET ?"
        params.extend((limit, offset))
        return [dict(row) for row in conn.execute(statement, params).fetchall()]


def _one(table: str, key: str, value: str) -> dict[str, Any] | None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    result = _select(table, filters={key: value.strip()}, limit=1)
    return result[0] if result else None


class AegisRepository:
    """Database read operations used by the FastAPI/Streamlit application.

    Each method opens its own short-lived read-only SQLite connection, so the
    repository can be safely shared between requests without retaining an
    unsafe cross-thread connection.
    """

    def list_cases(
        self, *, limit: int = 50, offset: int = 0, status: str | None = None
    ) -> list[dict[str, Any]]:
        filters = {"status": status} if status is not None else None
        return _select("cases", filters=filters, limit=limit, offset=offset)

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        return _one("cases", "case_id", case_id)

    def list_investigations(
        self,
        *,
        alert_id: str | None = None,
        case_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        # Alert IDs live in cases; the investigations table has case_id only.
        if alert_id is None:
            return _select(
                "investigations", filters={"case_id": case_id},
                limit=limit, offset=offset,
            )
        limit, offset = _page(limit, offset)
        with db_session(read_only=True) as conn:
            _columns(conn, "investigations")
            _columns(conn, "cases")
            statement = (
                "SELECT i.* FROM investigations i "
                "JOIN cases c ON c.case_id = i.case_id WHERE c.alert_id = ?"
            )
            params: list[Any] = [alert_id]
            if case_id is not None:
                statement += " AND i.case_id = ?"
                params.append(case_id)
            statement += " ORDER BY i.started_at DESC, i.rowid DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            return [dict(row) for row in conn.execute(statement, params)]

    def get_investigation(self, investigation_id: str) -> dict[str, Any] | None:
        return _one("investigations", "investigation_id", investigation_id)

    def list_agent_outputs(
        self, investigation_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        return _select(
            "agent_outputs",
            filters={"investigation_id": investigation_id},
            limit=limit,
            offset=offset,
        )

    def list_hitl_decisions(
        self,
        *,
        investigation_id: str | None = None,
        case_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return _select(
            "hitl_decisions",
            filters={"investigation_id": investigation_id, "case_id": case_id},
            limit=limit,
            offset=offset,
        )

    def list_audit_events(
        self,
        *,
        investigation_id: str | None = None,
        case_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return _select(
            "audit_events",
            filters={"investigation_id": investigation_id, "case_id": case_id},
            limit=limit,
            offset=offset,
        )

    def count_rows(self, table: str) -> int:
        _validate_table(table)
        with db_session(read_only=True) as conn:
            _columns(conn, table)
            return int(conn.execute(f"SELECT COUNT(*) FROM {_quoted(table)}").fetchone()[0])

    def get_table_counts(self) -> dict[str, int]:
        """Return live counts for the five current persistence tables."""
        with db_session(read_only=True) as conn:
            counts: dict[str, int] = {}
            for table in sorted(_TABLES):
                _columns(conn, table)
                counts[table] = int(
                    conn.execute(f"SELECT COUNT(*) FROM {_quoted(table)}").fetchone()[0]
                )
            return counts

    def get_recent_activity(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Convenience alias for audit activity displayed in Command Center."""
        return self.list_audit_events(limit=limit)


def get_repository() -> AegisRepository:
    """Return a lightweight repository instance for dependency injection."""
    return AegisRepository()


__all__ = ["AegisRepository", "RepositoryError", "get_repository"]
