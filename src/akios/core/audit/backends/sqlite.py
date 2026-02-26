# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# GPL-3.0-only
"""
SQLite audit backend — optional secondary audit storage (v1.2.0-beta).

Writes audit events to SQLite alongside the primary JSONL backend.
Requires: pip install akios[enforcecore]

IMPORTANT: JSONL remains the primary backend. SQLite is ADDITIONAL storage.
The Merkle chain lives in JSONL. SQLite enables queryable audit data.

Usage: AKIOS_AUDIT_BACKEND=sqlite
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SQLiteBackend:
    """
    SQLite secondary audit backend.
    Writes events alongside JSONL. Does NOT replace JSONL or the Merkle chain.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.name = "sqlite"
        self._db_path = db_path  # Resolved lazily from settings
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = False

    def _get_db_path(self) -> str:
        if self._db_path:
            return self._db_path
        try:
            from akios.config import get_settings
            s = get_settings()
            audit_dir = Path(s.audit_storage_path)
            audit_dir.mkdir(parents=True, exist_ok=True)
            return str(audit_dir / "audit_events.db")
        except Exception:
            return "./audit/audit_events.db"

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return True
        try:
            db_path = self._get_db_path()
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    timestamp TEXT,
                    workflow_id TEXT,
                    step INTEGER,
                    agent TEXT,
                    action TEXT,
                    result TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_id ON audit_events (workflow_id)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events (timestamp)"
            )
            self._conn.commit()
            self._initialized = True
            return True
        except Exception as e:
            logger.warning("SQLite audit backend init failed: %s", e)
            return False

    def write_event(self, event_data: Dict[str, Any]) -> None:
        """Write event to SQLite. Errors are logged but never block JSONL."""
        try:
            if not self._ensure_initialized():
                return
            metadata = event_data.get("metadata", {})
            self._conn.execute("""
                INSERT INTO audit_events (event_id, timestamp, workflow_id, step, agent, action, result, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get("event_id", ""),
                event_data.get("timestamp", ""),
                event_data.get("workflow_id", ""),
                event_data.get("step", 0),
                event_data.get("agent", ""),
                event_data.get("action", ""),
                event_data.get("result", ""),
                json.dumps(metadata, default=str),
            ))
            self._conn.commit()
        except Exception as e:
            logger.debug("SQLite write_event error (non-fatal): %s", e)

    def query_events(self, workflow_id: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        """Query audit events from SQLite."""
        if not self._ensure_initialized():
            return []
        try:
            if workflow_id:
                cursor = self._conn.execute(
                    "SELECT * FROM audit_events WHERE workflow_id = ? ORDER BY id DESC LIMIT ?",
                    (workflow_id, limit),
                )
            else:
                cursor = self._conn.execute(
                    "SELECT * FROM audit_events ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.debug("SQLite query error: %s", e)
            return []

    def is_available(self) -> bool:
        return self._ensure_initialized()

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._initialized = False
