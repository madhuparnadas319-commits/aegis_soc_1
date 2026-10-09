"""SQLite connection helpers for the AEGIS SOC application.

Save this file as ``aegis-soc/database/connection.py``.

This module opens the existing AEGIS database; it does not create or alter
its schema. Every caller should use ``db_session`` for reliable cleanup.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "database" / "aegis.db"


class DatabaseConnectionError(RuntimeError):
    """Raised when the configured AEGIS database cannot be opened."""


def get_database_path() -> Path:
    """Return the SQLite path, optionally overridden by ``AEGIS_DB_PATH``.

    Relative environment paths are interpreted from the project root rather
    than from the current working directory, so running Streamlit and FastAPI
    from different directories does not select different databases.
    """
    configured = os.getenv("AEGIS_DB_PATH", "").strip()
    if not configured:
        return DEFAULT_DATABASE_PATH

    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def get_connection(
    *,
    read_only: bool = False,
    create_if_missing: bool = False,
    timeout: float = 30.0,
) -> sqlite3.Connection:
    """Open a new SQLite connection with dict-like ``sqlite3.Row`` results.

    By default, the database must already exist. This protects AEGIS from
    silently creating an empty database when a path is wrong. Database setup
    tools may explicitly opt into ``create_if_missing=True``.

    Connections returned directly must be closed by their caller; prefer
    ``db_session`` for automatic commit/rollback and closure.
    """
    if read_only and create_if_missing:
        raise ValueError("A read-only connection cannot create a database.")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    path = get_database_path()
    if not path.is_file() and not create_if_missing:
        raise DatabaseConnectionError(
            f"AEGIS database not found: {path}. "
            "Check AEGIS_DB_PATH or initialize the database first."
        )

    if create_if_missing:
        path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if read_only:
            connection = sqlite3.connect(
                f"{path.as_uri()}?mode=ro",
                uri=True,
                timeout=timeout,
            )
        else:
            connection = sqlite3.connect(str(path), timeout=timeout)

        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
        return connection
    except sqlite3.Error as exc:
        raise DatabaseConnectionError(
            f"Could not open AEGIS database at {path}: {exc}"
        ) from exc


@contextmanager
def db_session(
    *,
    read_only: bool = False,
    create_if_missing: bool = False,
    timeout: float = 30.0,
) -> Iterator[sqlite3.Connection]:
    """Manage a database connection, transaction, and cleanup.

    Usage in a repository module::

        with db_session(read_only=True) as conn:
            rows = conn.execute("SELECT * FROM cases").fetchall()

        with db_session() as conn:
            conn.execute("UPDATE cases SET status = ? WHERE case_id = ?", ...)

    A successful writable session commits; an exception rolls back.
    """
    conn = get_connection(
        read_only=read_only,
        create_if_missing=create_if_missing,
        timeout=timeout,
    )
    try:
        yield conn
        if not read_only:
            conn.commit()
    except BaseException:
        if not read_only:
            conn.rollback()
        raise
    finally:
        conn.close()
