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
Security module - The unbreakable cage of AKIOS

Provides kernel-level isolation, syscall interception, and real-time PII protection.
Every execution path must pass through this module before any action is allowed.
"""

# Import the main enforcement functions
from .sandbox.manager import create_sandboxed_process, destroy_sandboxed_process
from .sandbox.quotas import enforce_hard_limits
from .syscall.interceptor import apply_syscall_policy, create_syscall_interceptor
from .syscall.policy import AgentType
from .pii.redactor import apply_pii_redaction

# Security validation functions
from .validation import validate_all_security, validate_startup_security

import platform
import os


def _is_running_in_container() -> bool:
    """Check if running inside Docker/container"""
    return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')


def enforce_sandbox(agent_type: AgentType = AgentType.TOOL_EXECUTOR):
    """
    Apply comprehensive sandbox security.
    
    On Docker: Apply cgroups (policy-based security)
    On Native Linux: Apply cgroups + syscall filtering (kernel-hard security)
    
    Args:
        agent_type: Type of agent for syscall policy (default: TOOL_EXECUTOR)
    
    Returns:
        None (raises exception if security fails)
    """
    from akios.config import get_settings
    settings = get_settings()
    
    # Always apply resource limits (cgroups)
    enforce_hard_limits()
    
    # Apply syscall filtering on native Linux only (not Docker/macOS/Windows)
    if settings.sandbox_enabled and platform.system() == 'Linux' and not _is_running_in_container():
        try:
            interceptor = create_syscall_interceptor(agent_type=agent_type)
            interceptor.enable_interception()
        except Exception as e:
            # If syscall filtering fails, log but don't crash (graceful degradation)
            # User still gets cgroups + command restrictions + PII redaction
            import logging
            logging.warning(f"Syscall filtering failed (falling back to policy-based): {e}")


__all__ = [
    "enforce_hard_limits",
    "create_sandboxed_process",
    "destroy_sandboxed_process",
    "apply_syscall_policy",
    "apply_pii_redaction",
    "validate_all_security",
    "validate_startup_security",
    "enforce_sandbox"  # Now includes syscall filtering
]
