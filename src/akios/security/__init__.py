"""
Security module - The unbreakable cage of AKIOS V1.0

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
