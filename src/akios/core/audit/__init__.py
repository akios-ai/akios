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
AKIOS Core Audit Module

Tamper-evident memory using cryptographic Merkle tree.
Records every action with provable integrity and clean exports.
"""

from .ledger import append_audit_event, get_merkle_root, get_ledger
from .exporter.json import export_audit_json
from .verifier import verify_audit_integrity
from ...config import get_settings
from pathlib import Path


def get_audit_log_path() -> str:
    """
    Get the path to the audit log file.

    Returns:
        Path to the audit_events.jsonl file
    """
    settings = get_settings()
    audit_path = Path(settings.audit_storage_path)
    return str(audit_path / "audit_events.jsonl")


def export_audit(task_id: str = "latest", format: str = "json", output: str = None) -> str:
    """
    Unified audit export function matching scope API.

    Args:
        task_id: Task identifier (currently ignored, always exports latest)
        format: Export format ("json" only)
        output: Output file path

    Returns:
        Path to the exported file

    Raises:
        ValueError: If format is not supported or output is missing
    """
    if not output:
        raise ValueError("output parameter is required for export_audit")

    if format.lower() == "json":
        result = export_audit_json(output)
        return result.get('output_file', output)
    else:
        raise ValueError(f"Unsupported export format: {format}. Only 'json' format is supported.")

__all__ = [
    "append_audit_event",
    "get_ledger",
    "get_merkle_root",
    "get_audit_log_path",
    "export_audit",
    "verify_audit_integrity"
]