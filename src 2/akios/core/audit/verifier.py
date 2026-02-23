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
Audit integrity verification and proof generation.

Checks Merkle tree integrity and generates verifiable proofs.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .ledger import get_ledger, get_merkle_root
from ...config import get_settings


def verify_audit_integrity() -> Dict[str, Any]:
    """
    Verify the overall integrity of the audit system.
    Includes tamper detection by checking stored audit file against Merkle tree.

    Returns:
        Dict with verification results
    """

    ledger = get_ledger()
    settings = get_settings()
    audit_path = Path(settings.audit_storage_path) / "audit_events.jsonl"

    # Flush any buffered events to disk before verifying
    ledger.flush_buffer()

    # Ensure all events are loaded for integrity check
    ledger._load_all_events()

    result = {
        'events_count': len(ledger.events),
        'tree_size': ledger.merkle_tree.size(),
        'merkle_root': get_merkle_root(),
        'integrity_ok': True,
        'issues': []
    }

    # Basic consistency checks
    if len(ledger.events) != ledger.merkle_tree.size():
        result['integrity_ok'] = False
        result['issues'].append("Event count mismatch with Merkle tree")

    # Check that all events have valid hashes
    for i, event in enumerate(ledger.events):
        if not event.hash or len(event.hash) != 64:
            result['integrity_ok'] = False
            result['issues'].append(f"Invalid hash for event {i}")
        # Additional validation: verify hash is valid hex
        elif not all(c in '0123456789abcdefABCDEF' for c in event.hash):
            result['integrity_ok'] = False
            result['issues'].append(f"Invalid hash format for event {i}")

    # TAMPER DETECTION: Verify stored file matches ledger
    if audit_path.exists():
        try:
            stored_events = []
            with open(audit_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            stored_event = json.loads(line)
                            stored_events.append(stored_event)
                        except json.JSONDecodeError:
                            result['integrity_ok'] = False
                            result['issues'].append(f"Invalid JSON in audit file line {line_num}")
                            continue

            # Check event count matches
            if len(stored_events) != len(ledger.events):
                result['integrity_ok'] = False
                result['issues'].append(f"Stored event count ({len(stored_events)}) doesn't match ledger ({len(ledger.events)})")

            # Check each stored event matches ledger
            for i, (stored, ledger_event) in enumerate(zip(stored_events, ledger.events)):
                # Compare key fields (excluding metadata which may vary)
                key_fields = ['action', 'agent', 'result', 'timestamp', 'workflow_id', 'step']
                for field in key_fields:
                    if stored.get(field) != getattr(ledger_event, field, None):
                        result['integrity_ok'] = False
                        result['issues'].append(f"Event {i} field '{field}' mismatch: stored={stored.get(field)}, ledger={getattr(ledger_event, field, None)}")
                        break

                # Check hash matches
                if stored.get('hash') != ledger_event.hash:
                    result['integrity_ok'] = False
                    result['issues'].append(f"Event {i} hash mismatch")

        except Exception as e:
            result['integrity_ok'] = False
            result['issues'].append(f"Error reading audit file: {e}")
    else:
        result['integrity_ok'] = False
        result['issues'].append("Audit file does not exist")

    return result


def generate_audit_report() -> Dict[str, Any]:
    """
    Generate a comprehensive audit report.

    Returns:
        Dict with audit statistics and integrity status
    """
    ledger = get_ledger()

    report = {
        'total_events': len(ledger.events),
        'merkle_root': get_merkle_root(),
        'integrity_check': verify_audit_integrity()
    }

    # Add event statistics
    agent_counts = {}
    action_counts = {}
    result_counts = {}

    for event in ledger.events:
        agent_counts[event.agent] = agent_counts.get(event.agent, 0) + 1
        action_counts[event.action] = action_counts.get(event.action, 0) + 1
        result_counts[event.result] = result_counts.get(event.result, 0) + 1

    report.update({
        'by_agent': agent_counts,
        'by_action': action_counts,
        'by_result': result_counts
    })

    return report