# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# GPL-3.0-only
"""
Audit backends — pluggable storage for AKIOS audit trails (v1.2.0-beta).

Default: JSONL (always active, unchanged from v1.1.x).
Optional: SQLite (requires EnforceCore), PostgreSQL (v1.3.0).

Usage:
    AKIOS_AUDIT_BACKEND=sqlite  → SQLite alongside JSONL
    AKIOS_AUDIT_BACKEND=jsonl   → JSONL only (default)
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
                "SQLite audit backend requires EnforceCore: pip install akios[enforcecore]"
            )
            return None

    return None
