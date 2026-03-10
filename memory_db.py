"""
memory_db.py  (Bonus Feature)
------------------------------
SQLite-backed error memory so the agent can recall past successful fixes
without making a redundant LLM call every time.

Schema
------
Table: fixes
  id           INTEGER PRIMARY KEY AUTOINCREMENT
  error_type   TEXT    – classified error label
  command      TEXT    – original developer command
  fix_command  TEXT    – the fix that was applied
  explanation  TEXT    – LLM's explanation
  applied_at   TEXT    – ISO-8601 timestamp
  success      INTEGER – 1 if the re-run succeeded after the fix
"""

import sqlite3
import datetime
from pathlib import Path
from typing import Optional


_DB_PATH = Path(__file__).parent / "fixes_memory.db"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS fixes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type    TEXT    NOT NULL,
    error_message TEXT    DEFAULT '',
    command       TEXT    NOT NULL,
    fix_command   TEXT    NOT NULL,
    explanation   TEXT,
    applied_at    TEXT    NOT NULL,
    success       INTEGER NOT NULL DEFAULT 0
);
"""


class ErrorMemory:
    """
    Lightweight wrapper around a SQLite database that stores fix records.

    Usage
    -----
    mem = ErrorMemory()
    mem.store("ModuleNotFoundError", "python app.py", "pip install pandas")
    hint = mem.lookup("ModuleNotFoundError")   # returns best past fix or None
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _DB_PATH
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create the table if it does not yet exist and run migrations."""
        with self._connect() as conn:
            conn.execute(_CREATE_SQL)
            # Migration: add error_message column if it doesn't exist
            try:
                conn.execute("ALTER TABLE fixes ADD COLUMN error_message TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # column already exists
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(
        self,
        error_type: str,
        error_message: str,
        command: str,
        fix_command: str,
        explanation: str = "",
        success: bool = True,
    ) -> int:
        """
        Persist a fix record.  Returns the new row id.
        """
        now = datetime.datetime.utcnow().isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO fixes (error_type, error_message, command, fix_command, explanation,
                                   applied_at, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (error_type, error_message, command, fix_command, explanation, now, int(success)),
            )
            conn.commit()
            return cur.lastrowid

    def lookup(self, error_type: str, error_message: str) -> Optional[dict]:
        """
        Return the most recent *successful* fix for a given error_type + error_message,
        or None if no matching fix exists.
        """
        with self._connect() as conn:
            # We match on exact error_message, or if error_message isn't available we fall back safely
            row = conn.execute(
                """
                SELECT * FROM fixes
                WHERE error_type = ? AND error_message = ? AND success = 1
                ORDER BY applied_at DESC
                LIMIT 1
                """,
                (error_type, error_message),
            ).fetchone()
        return dict(row) if row else None

    def get_all(self) -> list:
        """Return all fix records as a list of dicts, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM fixes ORDER BY applied_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        """Return total number of stored fix records."""
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM fixes").fetchone()[0]

    def clear(self) -> None:
        """Delete all records (useful for testing)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM fixes")
            conn.commit()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        mem = ErrorMemory(db_path=pathlib.Path(td) / "test.db")
        mem.store("ModuleNotFoundError", "No module named 'pandas'", "python app.py", "pip install pandas",
                  "pandas was missing", success=True)
        hit = mem.lookup("ModuleNotFoundError", "No module named 'pandas'")
        print("Lookup result:", hit)
        print("Total records:", mem.count())
