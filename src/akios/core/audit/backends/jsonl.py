# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# GPL-3.0-only
"""
JSONL audit backend — the default, always-active audit storage.

This is a thin wrapper that delegates to the primary AuditLedger.
Exists as a named backend for symmetry with future backends.
"""


class JSONLBackend:
    """
    JSONL audit backend (default, always active).
    The primary AuditLedger handles all actual JSONL writing.
    This class is a marker for the default backend.
    """

    def __init__(self):
        self.name = "jsonl"

    def write_event(self, event_data: dict) -> None:
        """JSONL writing is handled by AuditLedger directly."""
        pass  # Delegated to AuditLedger

    def is_available(self) -> bool:
        return True
