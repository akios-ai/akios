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
