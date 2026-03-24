"""SQLite database access for HydroKey."""

from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from hydro_key._config import APP_DIR

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = APP_DIR / "hydrokey.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS intake (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    amount_ml INTEGER NOT NULL
)
"""

_lock = threading.Lock()


def ensure_db(path: Path = DB_PATH) -> None:
    """Create the database directory and table if they do not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        try:
            with sqlite3.connect(path) as conn:
                conn.execute(_CREATE_TABLE)
        except sqlite3.DatabaseError:
            logger.warning("Database corrupted, backing up and recreating: %s", path)
            backup = path.with_suffix(".db.bak")
            try:
                if path.exists():
                    path.rename(backup)
                with sqlite3.connect(path) as conn:
                    conn.execute(_CREATE_TABLE)
            except (OSError, sqlite3.DatabaseError):
                logger.exception("Failed to recreate database at %s", path)
                raise


def add_record(amount_ml: int, path: Path = DB_PATH) -> int:
    """Insert an intake record (UTC timestamp) and return its row id."""
    now = datetime.now(tz=UTC).isoformat()
    with _lock, sqlite3.connect(path) as conn:
        cursor = conn.execute(
            "INSERT INTO intake (timestamp, amount_ml) VALUES (?, ?)",
            (now, amount_ml),
        )
        return cursor.lastrowid or 0


def delete_record(record_id: int, path: Path = DB_PATH) -> None:
    """Delete a single intake record by id."""
    with _lock, sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM intake WHERE id = ?", (record_id,))


def today_total(path: Path = DB_PATH) -> int:
    """Return the total intake in ml for today (local time)."""
    with _lock, sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount_ml), 0) FROM intake "
            "WHERE date(timestamp, 'localtime') = date('now', 'localtime')",
        ).fetchone()
        return int(row[0])
