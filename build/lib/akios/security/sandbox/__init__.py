"""
Sandbox module - Kernel-level process isolation

Provides cgroups v2 + seccomp-based process isolation and resource limits.
"""

from .manager import (
    SandboxManager,
    create_sandboxed_process,
    destroy_sandboxed_process,
    cleanup_sandbox_processes,
    get_sandbox_manager
)
from .quotas import (
    ResourceQuotas,
    enforce_hard_limits,
    QuotaViolationError
)

# Legacy compatibility
from .quotas import enforce_hard_limits as enforce_sandbox

__all__ = [
    "SandboxManager",
    "ResourceQuotas",
    "create_sandboxed_process",
    "destroy_sandboxed_process",
    "cleanup_sandbox_processes",
    "get_sandbox_manager",
    "enforce_hard_limits",
    "enforce_sandbox",  # Legacy alias
    "QuotaViolationError"
]
