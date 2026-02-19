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

from .merkle import MerkleTree

logger = logging.getLogger(__name__)


class AuditLedger:
    """Append-only audit ledger with Merkle tree integrity and memory optimization"""

    def __init__(self):
        settings = get_settings()
        audit_path = Path(settings.audit_storage_path)
        audit_path.mkdir(parents=True, exist_ok=True)

        self.ledger_file = audit_path / "audit_events.jsonl"
        self.ledger_file.touch(exist_ok=True)
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

        # Log rotation: rotate ledger at configurable threshold instead of dropping events
        self._rotation_threshold = 50000  # Rotate ledger at 50K events
        self._counter_file = audit_path / ".event_count"
        self._archive_dir = audit_path / "archive"
        self._total_event_count = self._read_counter()  # O(1) from counter file

        # Register shutdown handler to ensure buffers are flushed
        atexit.register(self._shutdown_flush)

        self._load_events_lazy()

    def _read_counter(self) -> int:
        """Read event count from counter file — O(1) instead of O(n) file scan"""
        if self._counter_file.exists():
            try:
                return int(self._counter_file.read_text().strip())
            except (ValueError, OSError):
                # Counter corrupted, fall back to line count and rebuild
                count = self._count_lines_on_disk()
                self._write_counter(count)
                return count
        else:
            # No counter file yet (pre-rotation ledger), count from disk
            count = self._count_lines_on_disk()
            self._write_counter(count)
            return count

    def _count_lines_on_disk(self) -> int:
        """Count lines in ledger file — fallback for when counter file is missing"""
        if not self.ledger_file.exists():
            return 0
        try:
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _write_counter(self, count: int) -> None:
        """Write event count to counter file"""
        try:
            self._counter_file.write_text(str(count))
        except Exception as e:
            logger.warning(f"Failed to write event counter: {e}")

    def flush_buffer(self) -> None:
        """Force flush any buffered events to disk (thread-safe)"""
        self._flush_buffer()

    def _load_events_lazy(self) -> None:
        """Lazy load events - only load file metadata initially"""
        if not self.ledger_file.exists():
            return

        # Use persistent counter for O(1) event count (no file scan)
        self._event_count = self._total_event_count

    def _load_all_events(self) -> None:
        """Load all events from disk into memory.

        Flushes any pending buffered events to disk first, then resets
        in-memory state and reloads everything from disk.  This prevents
        both duplication (events appended before this call) and data loss
        (events still sitting in the write buffer).
        """
        with self._state_lock:
            if self._loaded_all_events:
                return

            if not self.ledger_file.exists():
                self._loaded_all_events = True
                return

            # Flush any pending buffered events to disk before reloading,
            # so they survive the in-memory reset below.
            try:
                with self._buffer_lock:
                    if self._event_buffer:
                        with open(self.ledger_file, 'a', encoding='utf-8') as f:
                            for event_json in self._event_buffer:
                                f.write(event_json + '\n')
                        self._event_buffer.clear()
            except Exception as e:
                logger.warning(f"Could not flush buffer before full reload: {e}")

            # Reset in-memory state to prevent duplication with already-appended events
            self.events = []
            self.merkle_tree = MerkleTree()

            try:
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
            except (PermissionError, OSError) as e:
                logger.error(f"Cannot read audit file: {e}")

            self._loaded_all_events = True

    def append_event(self, event_data: Dict[str, Any]) -> AuditEvent:
        """Append an audit event to the ledger with buffered writing for performance.

        Events are NEVER silently dropped. When the rotation threshold is
        reached, the current ledger is archived and a fresh one is started
        with Merkle chain linkage to the previous segment.
        """
        event = create_audit_event(event_data)

        with self._state_lock:
            # Rotation check INSIDE lock (fixes TOCTOU race from v1.0.6)
            if self._total_event_count >= self._rotation_threshold:
                self._rotate_ledger()

            self._total_event_count += 1
            self.events.append(event)
            self.merkle_tree.append(event.to_json())

            # Memory management: remove old events if we exceed memory limit
            if len(self.events) > self._max_memory_events:
                # Keep only the most recent events in memory
                # Note: Old events remain on disk, just not in memory
                excess_count = len(self.events) - self._max_memory_events
                self.events = self.events[excess_count:]
                # Rebuild Merkle tree to maintain integrity after trimming
                self._rebuild_merkle_tree()

        # Buffer events for performance optimization (thread-safe)
        event_json = event.to_json()
        needs_flush = False
        with self._buffer_lock:
            self._event_buffer.append(event_json)

            # Check if buffer threshold reached (flush outside the lock to avoid deadlock)
            if len(self._event_buffer) >= self._buffer_size:
                needs_flush = True

        if needs_flush:
            self._flush_buffer()

        return event

    def _flush_buffer(self) -> None:
        """Flush buffered events to disk and update counter (thread-safe)"""
        with self._buffer_lock:
            if not self._event_buffer:
                return

            count = len(self._event_buffer)
            # Write all buffered events at once
            with open(self.ledger_file, 'a', encoding='utf-8') as f:
                for event_json in self._event_buffer:
                    f.write(event_json + '\n')

            logger.debug(f"Flushed {count} audit events to disk")
            self._event_buffer.clear()

        # Persist event counter and Merkle root hash
        self._write_counter(self._total_event_count)
        self._save_root_hash()

    def _shutdown_flush(self) -> None:
        """Flush any remaining buffers during program shutdown"""
        try:
            if self._event_buffer:
                pending = len(self._event_buffer)
                self._flush_buffer()
                logger.info(f"Shutdown flush completed: {pending} events written")
            # Always persist final root hash on shutdown
            self._save_root_hash()
        except Exception as e:
            # Log error but don't crash during shutdown
            logger.error(f"Error during shutdown flush: {e}")

    def _save_root_hash(self) -> None:
        """Persist current Merkle root hash to sidecar file for verification"""
        try:
            root = self.merkle_tree.get_root_hash()
            if root:
                root_file = self.ledger_file.parent / "merkle_root.hash"
                with open(root_file, 'w', encoding='utf-8') as f:
                    f.write(root)
        except Exception as e:
            logger.warning(f"Failed to save Merkle root hash: {e}")

    def _rotate_ledger(self) -> None:
        """Rotate the current ledger file to archive directory.

        Flushes pending events, saves Merkle chain metadata, and starts
        a fresh ledger.  Must be called while holding _state_lock.
        """
        from datetime import datetime, timezone
        import shutil

        # Flush any pending buffer to current file first
        with self._buffer_lock:
            if self._event_buffer:
                try:
                    with open(self.ledger_file, 'a', encoding='utf-8') as f:
                        for event_json in self._event_buffer:
                            f.write(event_json + '\n')
                    self._event_buffer.clear()
                except Exception as e:
                    logger.error(f"Failed to flush buffer before rotation: {e}")
                    return  # Don't rotate if we can't flush

        # Create archive directory
        self._archive_dir.mkdir(parents=True, exist_ok=True)

        # Capture Merkle root of current segment for chain verification
        merkle_root = self.merkle_tree.get_root_hash()

        # Generate timestamp-based archive name (microseconds to avoid collisions)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        archive_name = f"ledger_{timestamp}.jsonl"
        archive_file = self._archive_dir / archive_name

        try:
            # Move current ledger to archive
            shutil.move(str(self.ledger_file), str(archive_file))

            # Append chain metadata (one JSON line per rotation)
            chain_file = self._archive_dir / "chain.jsonl"
            chain_entry = json.dumps({
                "segment": archive_name,
                "merkle_root": merkle_root,
                "event_count": self._total_event_count,
                "rotated_at": datetime.now(timezone.utc).isoformat()
            }, sort_keys=True)
            with open(chain_file, 'a', encoding='utf-8') as f:
                f.write(chain_entry + '\n')

            # Create fresh ledger file
            self.ledger_file.touch()

            # Reset in-memory state
            self.events.clear()
            self.merkle_tree = MerkleTree()
            self._total_event_count = 0
            self._write_counter(0)
            self._loaded_all_events = False

            logger.info(
                f"Audit log rotated: {archive_name} "
                f"({self._rotation_threshold} events, "
                f"root: {merkle_root[:16] if merkle_root else 'none'}...)"
            )
        except Exception as e:
            logger.error(f"Failed to rotate audit log: {e}")
            # If rotation fails, keep appending to current file
            if not self.ledger_file.exists():
                self.ledger_file.touch()

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

        Loads all events from disk first to ensure complete comparison
        (in-memory events may be truncated for memory management).
        """

        audit_path = self.ledger_file

        if not audit_path.exists():
            return False

        # Ensure all events are loaded from disk (memory may be truncated
        # to _max_memory_events after many appends — v1.0.7 fix)
        self._load_all_events()

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


def reset_ledger() -> None:
    """Reset the global ledger instance and clear audit files (for testing only)"""
    global _ledger
    _ledger = None

    # Clear audit files for testing
    try:
        from ...config import get_settings
        settings = get_settings()
        audit_path = Path(settings.audit_storage_path)
        ledger_file = audit_path / "audit_events.jsonl"
        if ledger_file.exists():
            ledger_file.unlink()  # Delete the file
        counter_file = audit_path / ".event_count"
        if counter_file.exists():
            counter_file.unlink()
    except Exception:
        # Ignore errors during testing cleanup
        pass


def append_audit_event(event_data: Dict[str, Any]) -> AuditEvent:
    """Append an audit event to the global ledger"""
    ledger = get_ledger()
    return ledger.append_event(event_data)


def get_merkle_root() -> Optional[str]:
    """Get the current Merkle root hash"""
    ledger = get_ledger()
    return ledger.get_merkle_root()
