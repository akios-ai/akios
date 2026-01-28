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
Audit event definitions and serialization for AKIOS

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
        self._workflow_id = workflow_id
        self._step = step
        self._agent = agent
        self._action = action
        self._result = result
        self._metadata = metadata or {}
        self._timestamp = timestamp or datetime.now(timezone.utc).isoformat() + "Z"
        self._hash = self._calculate_hash()

    @property
    def workflow_id(self) -> str:
        return self._workflow_id

    @property
    def step(self) -> int:
        return self._step

    @property
    def agent(self) -> str:
        return self._agent

    @property
    def action(self) -> str:
        return self._action

    @property
    def result(self) -> str:
        return self._result

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def timestamp(self) -> str:
        return self._timestamp

    @property
    def hash(self) -> str:
        """Get the cryptographic hash of this event"""
        return self._hash

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
        """Calculate SHA-256 hash of event data (excluding timestamp for equality)"""
        # Create a safe version of metadata for hashing
        safe_metadata = {}
        for key, value in self._metadata.items():
            try:
                # Try to serialize the value to ensure it's hashable
                json.dumps(value, sort_keys=True)
                safe_metadata[key] = value
            except (TypeError, ValueError):
                # If not serializable, convert to string representation
                safe_metadata[key] = str(value)
        
        event_data = {
            "workflow_id": self._workflow_id,
            "step": self._step,
            "agent": self._agent,
            "action": self._action,
            "result": self._result,
            "metadata": safe_metadata
        }
        
        serialized = json.dumps(event_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(serialized).hexdigest()

    def __repr__(self) -> str:
        return f"AuditEvent(workflow={self.workflow_id}, step={self.step}, agent={self.agent}, hash={self.hash[:8]}...)"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AuditEvent):
            return False
        return (self.workflow_id == other.workflow_id and
                self.step == other.step and
                self.agent == other.agent and
                self.action == other.action and
                self.result == other.result and
                self.metadata == other.metadata)


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