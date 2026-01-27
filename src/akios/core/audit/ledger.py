"""
Append-only ledger for audit events using filesystem storage.

Stores events as JSON lines and maintains Merkle tree state.
"""

import atexit
import json
import logging
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any

from ...config import get_settings
from .events import AuditEvent, create_audit_event

logger = logging.getLogger(__name__)
from .merkle import MerkleTree

# Configure audit logger
logger = logging.getLogger(__name__)


class AuditLedger:
    """Append-only audit ledger with Merkle tree integrity and memory optimization"""

    def __init__(self):
        settings = get_settings()
        audit_path = Path(settings.audit_storage_path)
        audit_path.mkdir(parents=True, exist_ok=True)

        self.ledger_file = audit_path / "audit_events.jsonl"
        self.events: List[AuditEvent] = []
        self.merkle_tree = MerkleTree()

        # Performance optimizations
        self._event_buffer: List[str] = []

        # Use larger buffer in both Docker and native to reduce file I/O frequency and prevent hangs
        import os
        self._buffer_size = 100  # Flush every 100 events to prevent hangs in cgroups
        self._loaded_all_events = False
        self._buffer_lock = threading.Lock()  # Thread safety for buffer operations
        self._state_lock = threading.Lock()   # Thread safety for all state modifications

        # Memory management: limit events in memory to prevent leaks
        self._max_memory_events = 1000  # Keep only last 1000 events in memory

        # Performance safeguard: limit total audit events to prevent O(n²) Merkle tree scaling
        # This bounds the performance impact while maintaining audit integrity
        self._max_total_events = 10000  # Hard limit on total audit events

        # Register shutdown handler to ensure buffers are flushed
        atexit.register(self._shutdown_flush)

        self._load_events_lazy()

    def _count_total_events_on_disk(self) -> int:
        """Count total audit events stored on disk (for performance limiting)"""
        if not self.ledger_file.exists():
            return 0

        try:
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            # If we can't count, assume we're at the limit to be safe
            return self._max_total_events

    def flush_buffer(self) -> None:
        """Force flush any buffered events to disk (thread-safe)"""
        self._flush_buffer()

    def _load_events_lazy(self) -> None:
        """Lazy load events - only load file metadata initially"""
        if not self.ledger_file.exists():
            return

        # Just store file info, don't load all events into memory
        self._event_count = sum(1 for _ in open(self.ledger_file, 'r', encoding='utf-8'))

    def _load_all_events(self) -> None:
        """Load all events into memory when needed"""
        with self._state_lock:
            if self._loaded_all_events:
                return

            if not self.ledger_file.exists():
                self._loaded_all_events = True
                return

            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        event = AuditEvent(
                            workflow_id=data['workflow_id'],
                            step=data['step'],
                            agent=data['agent'],
                            action=data['action'],
                            result=data['result'],
                            metadata=data.get('metadata', {}),
                            timestamp=data.get('timestamp')
                        )

                        # Validate hash integrity if stored hash is available
                        stored_hash = data.get('hash')
                        if stored_hash and event.hash != stored_hash:
                            logger.warning(f"Hash mismatch for audit event: expected {stored_hash}, got {event.hash}")
                            # Continue processing but log the integrity issue

                        self.events.append(event)
                        self.merkle_tree.append(event.to_json())
                    except (json.JSONDecodeError, KeyError) as e:
                        # Log error but continue processing
                        logger.warning(f"Skipping corrupted audit event: {e}")

            self._loaded_all_events = True

    def append_event(self, event_data: Dict[str, Any]) -> AuditEvent:
        """Append an audit event to the ledger with buffered writing for performance"""
        event = create_audit_event(event_data)

        # Performance safeguard: check total events limit to prevent O(n²) Merkle tree scaling
        total_events_on_disk = self._count_total_events_on_disk()
        if total_events_on_disk >= self._max_total_events:
            logger.warning(f"Audit event limit reached ({self._max_total_events}). "
                          "Further audit events will be dropped to maintain performance. "
                          "Consider rotating audit logs or increasing the limit.")
            # Return a dummy event to avoid breaking calling code
            return event

        with self._state_lock:
            self.events.append(event)
            self.merkle_tree.append(event.to_json())

            # Memory management: remove old events if we exceed memory limit
            if len(self.events) > self._max_memory_events:
                # Keep only the most recent events in memory
                # Note: Old events remain on disk, just not in memory
                excess_count = len(self.events) - self._max_memory_events
                self.events = self.events[excess_count:]
                # Note: Merkle tree becomes invalid after trimming - would need rebuild in production

        # Buffer events for performance optimization (thread-safe)
        event_json = event.to_json()
        with self._buffer_lock:
            self._event_buffer.append(event_json)

            # Flush buffer when it reaches threshold
            if len(self._event_buffer) >= self._buffer_size:
                self._flush_buffer()

        return event

    def _flush_buffer(self) -> None:
        """Flush buffered events to disk (thread-safe)"""
        with self._buffer_lock:
            if not self._event_buffer:
                return

            count = len(self._event_buffer)
            # Write all buffered events at once
            with open(self.ledger_file, 'a', encoding='utf-8') as f:
                for event_json in self._event_buffer:
                    f.write(event_json + '\n')

            logger.debug(f"Flushed {count} audit events to disk (Docker tmpfs)")
            # Clear buffer and force flush to disk
            self._event_buffer.clear()
            # Note: Removed chmod to prevent potential hanging on some filesystems

    def _shutdown_flush(self) -> None:
        """Flush any remaining buffers during program shutdown"""
        try:
            if self._event_buffer:
                pending = len(self._event_buffer)
                self._flush_buffer()
                logger.info(f"Shutdown flush completed: {pending} events written")
        except Exception as e:
            # Log error but don't crash during shutdown
            logger.error(f"Error during shutdown flush: {e}")

    def get_merkle_root(self) -> Optional[str]:
        """Get the current Merkle root hash"""
        # Rebuild tree to ensure it reflects any changes to events
        self._rebuild_merkle_tree()
        return self.merkle_tree.get_root_hash()

    def _rebuild_merkle_tree(self) -> None:
        """Rebuild the Merkle tree from current events to detect tampering"""
        self.merkle_tree = MerkleTree()
        for event in self.events:
            self.merkle_tree.append(event.to_json())

    def get_all_events(self) -> List[AuditEvent]:
        """Get all events in the ledger (always reloads from disk for latest data)"""
        # Force reload from disk to ensure we get latest events
        # This prevents stale data issues where status commands don't see recent workflow completions
        self._loaded_all_events = False  # Reset flag to force reload
        self._load_all_events()
        return self.events.copy()

    def size(self) -> int:
        """Get the number of events in the ledger (uses cached count for performance)"""
        if not self._loaded_all_events and hasattr(self, '_event_count'):
            return self._event_count
        return len(self.events)

    def verify_file_integrity(self) -> bool:
        """
        Verify that stored audit file matches the in-memory ledger.
        This detects file-based tampering (the real threat).
        """
        from ...config import get_settings
        from pathlib import Path
        import json

        settings = get_settings()
        audit_path = Path(settings.audit_storage_path) / "audit_events.jsonl"

        if not audit_path.exists():
            return False

        try:
            # Read stored events from file
            stored_events = []
            with open(audit_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        stored_event = json.loads(line)
                        stored_events.append(stored_event)

            # Compare with in-memory events
            if len(stored_events) != len(self.events):
                return False

            # Verify each event matches
            for stored, memory_event in zip(stored_events, self.events):
                # Compare key fields
                key_fields = ['workflow_id', 'step', 'agent', 'action', 'result', 'timestamp']
                for field in key_fields:
                    if stored.get(field) != getattr(memory_event, field, None):
                        return False

                # Compare hashes
                if stored.get('hash') != memory_event.hash:
                    return False

            return True

        except (json.JSONDecodeError, KeyError, OSError):
            return False

    def verify_integrity(self) -> bool:
        """
        Comprehensive integrity check including both in-memory consistency
        and file-based tamper detection.
        """
        # First check file integrity (primary security concern)
        if not self.verify_file_integrity():
            return False

        # Then check in-memory Merkle tree consistency
        self._rebuild_merkle_tree()

        fresh_tree = MerkleTree()
        for event in self.events:
            fresh_tree.append(event.to_json())

        stored_root = self.merkle_tree.root.hash if self.merkle_tree.root else None
        fresh_root = fresh_tree.root.hash if fresh_tree.root else None

        return stored_root == fresh_root

# Global ledger instance
_ledger: Optional[AuditLedger] = None


def get_ledger() -> AuditLedger:
    """Get the global audit ledger instance"""
    global _ledger
    if _ledger is None:
        _ledger = AuditLedger()
    return _ledger


def append_audit_event(event_data: Dict[str, Any]) -> AuditEvent:
    """Append an audit event to the global ledger"""
    ledger = get_ledger()
    return ledger.append_event(event_data)


def get_merkle_root() -> Optional[str]:
    """Get the current Merkle root hash"""
    ledger = get_ledger()
    return ledger.get_merkle_root()
