"""
Syscall module - System call interception & policy enforcement

Provides seccomp-bpf filters + custom syscall bus for access control.
"""

from .policy import (
    SyscallPolicy,
    load_syscall_policy,
    get_default_policy,
    AgentType
)
from .interceptor import (
    SyscallInterceptor,
    create_syscall_interceptor,
    apply_syscall_policy,
    SyscallViolationError
)

__all__ = [
    "SyscallPolicy",
    "SyscallInterceptor",
    "AgentType",
    "load_syscall_policy",
    "get_default_policy",
    "create_syscall_interceptor",
    "apply_syscall_policy",
    "SyscallViolationError"
]
