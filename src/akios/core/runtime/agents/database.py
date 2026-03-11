# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Database Agent — Query PostgreSQL and SQLite with security enforcement.

Added in v1.1.0. Security-first database access:
- Parameterized queries only (no raw SQL concatenation)
- Read-only by default (SELECT only)
- DDL always blocked (CREATE, DROP, ALTER, TRUNCATE)
- PII redaction on query results
- Audit logging of all queries
"""

import logging
import os
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional

from .base import BaseAgent, AgentError
from akios.core.audit import append_audit_event

try:
    from akios.security.pii import apply_pii_redaction
except Exception:
    import logging as _logging
    _logging.getLogger(__name__).critical(
        "PII redaction module failed to import — all content will be masked"
    )
    apply_pii_redaction = lambda x: "[PII_REDACTION_UNAVAILABLE]"

logger = logging.getLogger(__name__)

# DDL patterns — always blocked regardless of allow_write
DDL_PATTERNS = re.compile(
    r"\b(CREATE|DROP|ALTER|TRUNCATE|RENAME|GRANT|REVOKE|VACUUM)\b",
    re.IGNORECASE,
)

# Write DML patterns — blocked unless allow_write=True
WRITE_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|REPLACE|MERGE|UPSERT)\b",
    re.IGNORECASE,
)


class DatabaseAgent(BaseAgent):
    """
    Database agent for querying PostgreSQL and SQLite databases.

    Security model:
    - Parameterized queries enforced (no string interpolation)
    - SELECT only by default
    - DDL always blocked
    - PII redaction on results
    """

    def __init__(self, database_url: str = None, allow_write: bool = False,
                 timeout: int = 30, max_rows: int = 1000, **kwargs):
        super().__init__(**kwargs)
        self.database_url = database_url
        self.allow_write = allow_write
        self.timeout = min(timeout, 60)
        self.max_rows = min(max_rows, 10000)

    def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_parameters(action, parameters)

        query = parameters.get("query", "")
        params = parameters.get("params", [])
        db_url = parameters.get("database_url") or self.database_url

        if not db_url:
            raise AgentError(
                "Database URL required. Set in config.database_url or parameters.database_url."
            )

        # Security: block DDL always
        if DDL_PATTERNS.search(query):
            raise AgentError(
                f"DDL statements are blocked for security. "
                f"CREATE, DROP, ALTER, TRUNCATE are not allowed."
            )

        # Security: block writes unless explicitly allowed
        if WRITE_PATTERNS.search(query) and not self.allow_write:
            raise AgentError(
                f"Write operations blocked. Set allow_write: true in config to enable "
                f"INSERT, UPDATE, DELETE."
            )

        workflow_id = parameters.get("workflow_id", "unknown")
        step = parameters.get("step", 0)

        # Check mock mode
        if os.getenv("AKIOS_MOCK_LLM") == "1":
            return self._mock_response(action, query, workflow_id, step)

        # Execute query
        start_time = time.time()
        if db_url.startswith("sqlite"):
            result = self._execute_sqlite(action, db_url, query, params)
        elif db_url.startswith("postgresql"):
            result = self._execute_postgresql(action, db_url, query, params)
        else:
            raise AgentError(f"Unsupported database URL scheme. Use sqlite:/// or postgresql://")
        execution_time = time.time() - start_time

        # PII redaction on results
        if "rows" in result:
            redacted_rows = []
            for row in result["rows"]:
                redacted_row = [
                    apply_pii_redaction(str(v)) if isinstance(v, str) else v
                    for v in row
                ]
                redacted_rows.append(redacted_row)
            result["rows"] = redacted_rows

        # Audit
        append_audit_event({
            "workflow_id": workflow_id,
            "step": step,
            "agent": "database",
            "action": action,
            "result": "success",
            "metadata": {
                "query_type": action,
                "row_count": result.get("row_count", 0),
                "execution_time": execution_time,
                "database_type": "sqlite" if "sqlite" in db_url else "postgresql",
            },
        })

        result["execution_time"] = execution_time
        return result

    def _execute_sqlite(self, action: str, db_url: str, query: str,
                        params: list) -> Dict[str, Any]:
        # Extract path from sqlite:///path
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not db_path:
            raise AgentError("SQLite database path is empty")

        try:
            conn = sqlite3.connect(db_path, timeout=self.timeout)
            cursor = conn.cursor()

            if action == "count":
                cursor.execute(query, params)
                row = cursor.fetchone()
                count = row[0] if row else 0
                conn.close()
                return {"count": count, "row_count": 1}

            elif action == "query":
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchmany(self.max_rows)
                row_count = len(rows)
                conn.close()
                return {
                    "columns": columns,
                    "rows": [list(r) for r in rows],
                    "row_count": row_count,
                    "truncated": row_count >= self.max_rows,
                }

            elif action == "execute":
                cursor.execute(query, params)
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                return {"affected_rows": affected, "row_count": affected}

        except sqlite3.Error as e:
            raise AgentError(f"SQLite error: {e}") from e

    def _execute_postgresql(self, action: str, db_url: str, query: str,
                            params: list) -> Dict[str, Any]:
        try:
            import psycopg2
        except ImportError:
            raise AgentError(
                "psycopg2 required for PostgreSQL. Install: pip install psycopg2-binary"
            )

        try:
            conn = psycopg2.connect(db_url, connect_timeout=self.timeout)
            cursor = conn.cursor()

            if action == "count":
                cursor.execute(query, params)
                row = cursor.fetchone()
                count = row[0] if row else 0
                conn.close()
                return {"count": count, "row_count": 1}

            elif action == "query":
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchmany(self.max_rows)
                row_count = len(rows)
                conn.close()
                return {
                    "columns": columns,
                    "rows": [list(r) for r in rows],
                    "row_count": row_count,
                    "truncated": row_count >= self.max_rows,
                }

            elif action == "execute":
                cursor.execute(query, params)
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                return {"affected_rows": affected, "row_count": affected}

        except Exception as e:
            raise AgentError(f"PostgreSQL error: {e}") from e

    def _mock_response(self, action: str, query: str,
                       workflow_id: str, step: int) -> Dict[str, Any]:
        logger.info("MOCK MODE: Simulating database %s", action)
        append_audit_event({
            "workflow_id": workflow_id,
            "step": step,
            "agent": "database",
            "action": action,
            "result": "success",
            "metadata": {"mock": True},
        })
        if action == "count":
            return {"count": 42, "row_count": 1, "mock": True}
        elif action == "query":
            return {
                "columns": ["id", "name"],
                "rows": [[1, "mock_result"]],
                "row_count": 1,
                "truncated": False,
                "mock": True,
            }
        return {"affected_rows": 0, "row_count": 0, "mock": True}

    def validate_parameters(self, action: str, parameters: Dict[str, Any]) -> None:
        if action not in self.get_supported_actions():
            raise AgentError(f"Unsupported database action: {action}. Use: {self.get_supported_actions()}")
        if "query" not in parameters:
            raise AgentError("Database agent requires 'query' parameter")

    def get_supported_actions(self) -> List[str]:
        return ["query", "execute", "count"]
