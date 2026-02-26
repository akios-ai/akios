# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# GPL-3.0-only
"""
Audit backends — pluggable storage for AKIOS audit trails (v1.2.0-rc).

Default: JSONL (always active, unchanged from v1.1.x).
Optional: SQLite (local/dev), PostgreSQL (production).

Usage:
    AKIOS_AUDIT_BACKEND=sqlite       → SQLite alongside JSONL (local dev)
    AKIOS_AUDIT_BACKEND=postgresql   → PostgreSQL alongside JSONL (production)
    AKIOS_AUDIT_BACKEND=jsonl        → JSONL only (default)
    AKIOS_AUDIT_PG_DSN=postgresql://user:pass@host:5432/db  → for postgresql
"""

from .jsonl import JSONLBackend

__all__ = ["JSONLBackend", "get_extra_backend"]


def get_extra_backend(backend_name: str):
    """
    Get an optional secondary audit backend by name.
    Returns None if backend is not available or not configured.
    The primary JSONL backend is always active regardless.
    """
    if backend_name in ("jsonl", "default", None, ""):
        return None  # No extra backend — JSONL only (the default)

    if backend_name == "sqlite":
        try:
            from .sqlite import SQLiteBackend
            return SQLiteBackend()
        except ImportError:
            import logging
            logging.getLogger(__name__).warning(
                "SQLite audit backend not available"
            )
            return None

    if backend_name == "postgresql":
        try:
            from .postgresql import PostgreSQLBackend
            return PostgreSQLBackend()
        except ImportError:
            import logging
            logging.getLogger(__name__).warning(
                "PostgreSQL audit backend requires psycopg2: pip install psycopg2-binary"
            )
            return None

    import logging
    logging.getLogger(__name__).warning("Unknown audit backend: %s", backend_name)
    return None
