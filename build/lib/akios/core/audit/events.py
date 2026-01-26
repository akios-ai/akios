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
Audit event definitions and serialization for AKIOS V1.0

Structured audit events with cryptographic integrity.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class AuditEvent:
    """
    Represents a single audit event in the AKIOS system.

    Each event is immutable and includes a cryptographic hash for integrity.
    """

    def __init__(self,
                 workflow_id: str,
                 step: int,
                 agent: str,
                 action: str,
                 result: str,
                 metadata: Optional[Dict[str, Any]] = None,
                 timestamp: Optional[str] = None):
        self.workflow_id = workflow_id
        self.step = step
        self.agent = agent
        self.action = action
        self.result = result
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat() + "Z"
        self._hash = self._calculate_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "workflow_id": self.workflow_id,
            "step": self.step,
            "agent": self.agent,
            "action": self.action,
            "result": self.result,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "hash": self.hash
        }

    def to_json(self) -> str:
        """Convert event to JSON string"""
        try:
            return json.dumps(self.to_dict(), sort_keys=True, default=str)
        except (TypeError, ValueError) as e:
            # Fallback: convert non-serializable objects to strings
            safe_dict = {}
            for key, value in self.to_dict().items():
                try:
                    json.dumps(value, default=str)
                    safe_dict[key] = value
                except (TypeError, ValueError):
                    safe_dict[key] = str(value)
            return json.dumps(safe_dict, sort_keys=True)

    @property
    def hash(self) -> str:
        """Get the cryptographic hash of this event"""
        return self._hash

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of event data"""
        event_data = {
            "workflow_id": self.workflow_id,
            "step": self.step,
            "agent": self.agent,
            "action": self.action,
            "result": self.result,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
        serialized = json.dumps(event_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(serialized).hexdigest()

    def __repr__(self) -> str:
        return f"AuditEvent(workflow={self.workflow_id}, step={self.step}, agent={self.agent}, hash={self.hash[:8]}...)"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AuditEvent):
            return False
        return self.hash == other.hash


def create_audit_event(event_data: Dict[str, Any]) -> AuditEvent:
    """Create an audit event from dictionary data"""
    required_fields = ['workflow_id', 'step', 'agent', 'action', 'result']
    for field in required_fields:
        if field not in event_data:
            raise ValueError(f"Missing required field: {field}")

    return AuditEvent(
        workflow_id=event_data['workflow_id'],
        step=event_data['step'],
        agent=event_data['agent'],
        action=event_data['action'],
        result=event_data['result'],
        metadata=event_data.get('metadata', {}),
        timestamp=event_data.get('timestamp')
    )