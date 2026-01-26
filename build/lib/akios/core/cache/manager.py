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
Performance Cache Manager - Intelligent caching for expensive operations

Optimizes startup time and memory usage through intelligent caching strategies.
Provides lazy loading and result caching for improved performance.
"""

import os
import json
import time
import hashlib
import threading
from typing import Dict, Any, Optional, Callable
from pathlib import Path


class CacheManager:
    """
    Intelligent cache manager for performance optimization.

    Handles caching of expensive operations like template parsing,
    configuration validation, and security checks.
    """

    def __init__(self, cache_dir: str = ".akios/cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._memory_cache = {}
        self._lock = threading.Lock()  # Thread safety for concurrent access

    def get_or_compute(self, key: str, compute_func: Callable[[], Any],
                       ttl_seconds: int = 3600) -> Any:
        """
        Get cached result or compute and cache it.

        Args:
            key: Cache key
            compute_func: Function to compute result if not cached
            ttl_seconds: Time-to-live in seconds

        Returns:
            Cached or computed result
        """
        # Check memory cache first
        if key in self._memory_cache:
            cached_item = self._memory_cache[key]
            if time.time() - cached_item['timestamp'] < ttl_seconds:
                return cached_item['data']

        # Check file cache
        cache_file = self.cache_dir / f"{self._hash_key(key)}.json"
        if cache_file.exists():
            try:
                # Try reading as compressed first, then as JSON
                with open(cache_file, 'rb') as f:
                    raw_data = f.read()

                try:
                    # Try to decompress
                    import gzip
                    decompressed = gzip.decompress(raw_data).decode()
                    cached_data = json.loads(decompressed)
                    is_compressed = True
                except (gzip.BadGzipFile, UnicodeDecodeError):
                    # Not compressed, try as regular JSON
                    cached_data = json.loads(raw_data.decode())
                    is_compressed = False

                if time.time() - cached_data.get('timestamp', 0) < ttl_seconds:
                    # Store in memory cache for faster future access
                    self._memory_cache[key] = cached_data
                    return cached_data['data']
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                # Cache file corrupted, remove it
                cache_file.unlink(missing_ok=True)

        # Compute result
        result = compute_func()

        # Cache result
        cache_data = {
            'data': result,
            'timestamp': time.time(),
            'key': key
        }

        # Save to file cache with optional compression
        try:
            cache_data_compressed, is_compressed = self._compress_data(cache_data)
            with open(cache_file, 'wb' if is_compressed else 'w') as f:
                if is_compressed:
                    f.write(cache_data_compressed)
                else:
                    json.dump(cache_data_compressed, f)
        except OSError:
            # Silently fail if we can't write cache
            pass

        # Store in memory cache
        self._memory_cache[key] = cache_data

        return result

    def invalidate(self, key: str) -> None:
        """
        Invalidate a specific cache entry (thread-safe).

        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            # Remove from memory cache
            self._memory_cache.pop(key, None)

            # Remove from file cache
            cache_file = self.cache_dir / f"{self._hash_key(key)}.json"
            cache_file.unlink(missing_ok=True)

    def clear_all(self) -> None:
        """Clear all cache entries."""
        # Clear memory cache
        self._memory_cache.clear()

        # Clear file cache
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)

    def _hash_key(self, key: str) -> str:
        """Generate a safe filename from cache key using SHA256."""
        return hashlib.sha256(key.encode()).hexdigest()

    def _should_compress(self, data: Any) -> bool:
        """Check if data should be compressed based on size."""
        try:
            data_str = json.dumps(data, default=str, separators=(',', ':'))
            return len(data_str) > 1024  # Compress if > 1KB
        except (TypeError, ValueError):
            return False

    def _compress_data(self, data: Any) -> tuple[Any, bool]:
        """Compress data if beneficial."""
        if not self._should_compress(data):
            return data, False

        try:
            import gzip
            data_str = json.dumps(data, default=str, separators=(',', ':'))
            compressed = gzip.compress(data_str.encode('utf-8'), compresslevel=6)
            if len(compressed) < len(data_str):  # Only use if smaller
                return compressed, True
        except (ImportError, TypeError, ValueError):
            pass

        return data, False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        file_cache_size = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.json")
            if f.exists()
        )

        return {
            'memory_cache_entries': len(self._memory_cache),
            'file_cache_files': len(list(self.cache_dir.glob("*.json"))),
            'file_cache_size_bytes': file_cache_size,
            'cache_dir': str(self.cache_dir)
        }


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached_operation(key: str, ttl_seconds: int = 3600):
    """
    Decorator for caching expensive operations.

    Args:
        key: Cache key
        ttl_seconds: Time-to-live in seconds

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache_mgr = get_cache_manager()
            # Create a unique key including function arguments
            full_key = f"{key}_{hash(str(args) + str(kwargs))}"
            return cache_mgr.get_or_compute(full_key, lambda: func(*args, **kwargs), ttl_seconds)
        return wrapper
    return decorator


# Template caching functions
def get_template_cache_key(template_path: str, template_content: str) -> str:
    """Generate cache key for template parsing using SHA256."""
    return f"template_{hashlib.sha256((template_path + template_content).encode()).hexdigest()}"


def get_workflow_cache_key(workflow_data: Dict[str, Any]) -> str:
    """Generate cache key for workflow validation using SHA256."""
    return f"workflow_validation_{hashlib.sha256(json.dumps(workflow_data, sort_keys=True).encode()).hexdigest()}"
