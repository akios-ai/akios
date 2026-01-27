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
Retry Handler - Basic retry/fallback logic (max 3 attempts for non-fatal errors)

Provides resilient execution with configurable retry policies.
"""

import time
from typing import Callable, Any, Dict, Optional

from akios.config import get_settings


class RetryHandler:
    """
    Handles retry logic for workflow steps.

    Implements exponential backoff with maximum attempt limits.
    """

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.settings = get_settings()
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def execute_with_retry(self, func: Callable[[], Any]) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute (should be callable with no arguments)

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return func()

            except Exception as e:
                last_exception = e

                # Check if error is retryable
                if not self._is_retryable_error(e):
                    # Non-retryable error, fail immediately
                    raise e

                # Don't retry on last attempt
                if attempt == self.max_attempts - 1:
                    break

                # Calculate delay and wait
                delay = self._calculate_delay(attempt)
                time.sleep(delay)

        # All attempts failed
        raise last_exception

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.

        Args:
            error: The exception that occurred

        Returns:
            True if the error should be retried
        """
        error_str = str(error).lower()

        # Network-related errors are typically retryable
        retryable_patterns = [
            'timeout',
            'connection',
            'network',
            'temporary',
            'rate limit',
            'server error',
            '502', '503', '504'  # HTTP server errors
        ]

        for pattern in retryable_patterns:
            if pattern in error_str:
                return True

        # Security and validation errors are not retryable
        non_retryable_patterns = [
            'permission',
            'forbidden',
            'unauthorized',
            'invalid',
            'security',
            'sandbox',
            'kill'
        ]

        for pattern in non_retryable_patterns:
            if pattern in error_str:
                return False

        # Default: assume retryable for unknown errors
        return True

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt using exponential backoff.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * 2^attempt
        delay = self.base_delay * (2 ** attempt)

        # Add jitter (±25%) to prevent thundering herd
        import random
        jitter = random.uniform(0.75, 1.25)
        delay *= jitter

        # Cap at maximum delay
        return min(delay, self.max_delay)

    def get_retry_status(self) -> Dict[str, Any]:
        """Get current retry configuration status"""
        return {
            'max_attempts': self.max_attempts,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay,
            'enabled': True  # Always enabled in v1.0.0
        }


class FallbackHandler:
    """
    Handles fallback logic for failed operations.
    """

    def __init__(self):
        self.settings = get_settings()

    def execute_with_fallback(self, primary_func: Callable[[], Any],
                             fallback_func: Optional[Callable[[], Any]] = None) -> Any:
        """
        Execute with fallback if primary fails.

        Args:
            primary_func: Primary function to try
            fallback_func: Fallback function if primary fails

        Returns:
            Result from primary or fallback

        Raises:
            Exception: If both primary and fallback fail, or no fallback provided
        """
        try:
            return primary_func()
        except Exception as primary_error:
            if fallback_func is None:
                raise primary_error

            try:
                return fallback_func()
            except Exception as fallback_error:
                # Both failed, raise the primary error
                raise primary_error from fallback_error
