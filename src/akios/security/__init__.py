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
Security module - The unbreakable cage of AKIOS v1.0.0

Provides kernel-level isolation, syscall interception, and real-time PII protection.
Every execution path must pass through this module before any action is allowed.
"""

# Import the main enforcement functions
from .sandbox.manager import create_sandboxed_process, destroy_sandboxed_process
from .sandbox.quotas import enforce_hard_limits
from .syscall.interceptor import apply_syscall_policy
from .pii.redactor import apply_pii_redaction

# Security validation functions
from .validation import validate_all_security, validate_startup_security

# Legacy compatibility - these will be removed in future versions
def enforce_sandbox():
    """Legacy function - use enforce_hard_limits instead"""
    return enforce_hard_limits()

__all__ = [
    "enforce_hard_limits",
    "create_sandboxed_process",
    "destroy_sandboxed_process",
    "apply_syscall_policy",
    "apply_pii_redaction",
    "validate_all_security",
    "validate_startup_security",
    "enforce_sandbox"  # Legacy
]
