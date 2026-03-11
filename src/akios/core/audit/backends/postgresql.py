# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# GPL-3.0-only
"""
PostgreSQL audit backend — optional secondary audit storage (v1.2.0-rc).

Writes audit events to PostgreSQL alongside the primary JSONL backend.
Requires: pip install akios[enforcecore] AND psycopg2-binary

IMPORTANT: JSONL + Merkle chain remain primary. PostgreSQL is ADDITIONAL storage.

Usage: AKIOS_AUDIT_BACKEND=postgresql
Config: AKIOS_AUDIT_PG_DSN=postgresql://user:pass@host:5432/dbname
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PostgreSQLBackend:
    """
    PostgreSQL secondary audit backend.
    Writes events alongside JSONL. Does NOT replace JSONL or the Merkle chain.
    """

    def __init__(self, dsn: Optional[str] = None):
        self.name = "postgresql"
        self._dsn = dsn or os.environ.get("AKIOS_AUDIT_PG_DSN", "")
        self._conn = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return True
        if not self._dsn:
            logger.warning(
                "PostgreSQL backend requires AKIOS_AUDIT_PG_DSN env var. "
                "Example: postgresql://user:pass@localhost:5432/audit_db"
            )
            return False
        try:
            import psycopg2
            self._conn = psycopg2.connect(self._dsn)
            self._conn.autocommit = True
            cursor = self._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS akios_audit_events (
                    id SERIAL PRIMARY KEY,
                    event_id TEXT,
                    timestamp TEXT,
                    workflow_id TEXT,
                    step INTEGER,
                    agent TEXT,
                    action TEXT,
                    result TEXT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_akios_workflow_id ON akios_audit_events (workflow_id)"
            )
            cursor.close()
            self._initialized = True
            return True
        except ImportError:
            logger.warning("PostgreSQL backend requires psycopg2: pip install psycopg2-binary")
            return False
        except Exception as e:
            logger.warning("PostgreSQL audit backend init failed: %s", e)
            return False

    def write_event(self, event_data: Dict[str, Any]) -> None:
        """Write event to PostgreSQL. Errors never block JSONL."""
        try:
            if not self._ensure_initialized():
                return
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO akios_audit_events
                    (event_id, timestamp, workflow_id, step, agent, action, result, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                event_data.get("event_id", ""),
                event_data.get("timestamp", ""),
                event_data.get("workflow_id", ""),
                event_data.get("step", 0),
                event_data.get("agent", ""),
                event_data.get("action", ""),
                event_data.get("result", ""),
                json.dumps(event_data.get("metadata", {}), default=str),
            ))
            cursor.close()
        except Exception as e:
            logger.debug("PostgreSQL write_event error (non-fatal): %s", e)
            # Reconnect on next write
            self._initialized = False

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
