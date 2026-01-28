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
Syscall policy definitions for AKIOS

Define and load syscall policies for different agent types.
Simplified implementation of seccomp-bpf policy functionality.
"""

from typing import Set, Dict, List, Optional, Any
from enum import Enum

from ...config import get_settings


class AgentType(Enum):
    """Types of agents with different syscall requirements"""
    LLM = "llm"
    HTTP = "http"
    FILESYSTEM = "filesystem"
    TOOL_EXECUTOR = "tool_executor"


class SyscallPolicy:
    """
    Syscall policy for controlling system call access

    Defines which syscalls are allowed or denied for different contexts.
    Simplified implementation of seccomp policy functionality.
    """

    def __init__(self, agent_type: Optional[AgentType] = None, settings=None):
        self.settings = settings if settings is not None else get_settings()
        self.agent_type = agent_type
        self.allowed_syscalls = self._load_base_policy()
        self.blocked_syscalls = self._load_blocked_policy()

    def _load_base_policy(self) -> Set[str]:
        """
        Load base allowed syscalls for all agents

        These are essential syscalls needed for basic process operation.
        """
        base_allowed = {
            # Process management
            'getpid', 'getppid', 'getuid', 'geteuid', 'getgid', 'getegid',
            'setuid', 'setgid', 'seteuid', 'setegid',
            'fork', 'vfork', 'clone', 'execve', 'wait4', 'waitpid',

            # Memory management
            'brk', 'mmap', 'mprotect', 'munmap', 'mremap', 'msync',

            # File operations (basic)
            'open', 'close', 'read', 'write', 'lseek', 'fstat', 'stat',
            'fstatfs', 'statfs', 'access', 'readlink',

            # Signal handling
            'kill', 'tkill', 'tgkill', 'sigaction', 'sigprocmask', 'sigsuspend',

            # Time and timers
            'gettimeofday', 'clock_gettime', 'alarm', 'setitimer', 'getitimer',

            # System info
            'uname', 'sysinfo', 'getrlimit', 'setrlimit',

            # Directory operations
            'getdents', 'getdents64', 'chdir', 'fchdir', 'getcwd',

            # Process scheduling
            'sched_getparam', 'sched_setparam', 'sched_getscheduler',
            'sched_setscheduler', 'sched_get_priority_min', 'sched_get_priority_max',

            # Exit
            'exit', 'exit_group',
        }

        return base_allowed

    def _load_blocked_policy(self) -> Set[str]:
        """
        Load syscalls that are always blocked for security

        These syscalls are dangerous and should never be allowed.
        """
        always_blocked = {
            # Process tracing/debugging
            'ptrace', 'process_vm_readv', 'process_vm_writev',

            # Key management (kernel keyring)
            'keyctl', 'add_key', 'request_key', 'update_key', 'revoke_key',

            # Dangerous system operations
            'reboot', 'halt', 'poweroff', 'kexec_load', 'kexec_file_load',

            # Raw I/O and hardware access
            'iopl', 'ioperm', 'pciconfig_read', 'pciconfig_write',

            # Kernel module operations
            'init_module', 'finit_module', 'delete_module',
        }

        # Add network-related syscalls if network is disabled
        if not self.settings.network_access_allowed:
            network_blocked = {
                'socket', 'socketpair', 'bind', 'listen', 'accept', 'accept4',
                'connect', 'getsockname', 'getpeername', 'sendto', 'recvfrom',
                'sendmsg', 'recvmsg', 'shutdown', 'setsockopt', 'getsockopt',
            }
            always_blocked.update(network_blocked)

        return always_blocked

    def _load_agent_specific_policy(self) -> Set[str]:
        """
        Load agent-specific allowed syscalls

        Different agent types need different syscall permissions.
        """
        agent_allowed = set()

        if self.agent_type == AgentType.FILESYSTEM:
            # Filesystem agent needs additional file operations
            agent_allowed.update({
                'mkdir', 'rmdir', 'unlink', 'rename', 'link', 'symlink',
                'chmod', 'fchmod', 'chown', 'fchown', 'lchown',
                'truncate', 'ftruncate', 'utime', 'utimes', 'futimesat',
                'flock', 'fcntl', 'ioctl',
            })

        elif self.agent_type == AgentType.HTTP:
            # HTTP agent needs network operations
            if self.settings.network_access_allowed:
                agent_allowed.update({
                    'socket', 'connect', 'sendto', 'recvfrom',
                    'sendmsg', 'recvmsg', 'shutdown', 'setsockopt', 'getsockopt',
                })

        elif self.agent_type == AgentType.LLM:
            # LLM agent is relatively restricted - mostly just needs basic I/O
            pass  # Uses base policy only

        elif self.agent_type == AgentType.TOOL_EXECUTOR:
            # Tool executor needs to be very restricted to prevent code execution
            # Only basic operations, no exec, no file creation
            pass  # Uses base policy only, blocks execve

        return agent_allowed

    def is_syscall_allowed(self, syscall_name: str) -> bool:
        """
        Check if a syscall is allowed

        Args:
            syscall_name: Name of the syscall to check

        Returns:
            True if allowed, False if blocked
        """
        if not self.settings.sandbox_enabled:
            return True

        # Always block dangerous syscalls
        if syscall_name in self.blocked_syscalls:
            return False

        # Allow base syscalls
        if syscall_name in self.allowed_syscalls:
            return True

        # Allow agent-specific syscalls
        agent_specific = self._load_agent_specific_policy()
        if syscall_name in agent_specific:
            return True

        # Default: deny
        return False

    def get_policy_summary(self) -> Dict[str, Any]:
        """
        Get summary of current policy

        Returns:
            Dict with policy information
        """
        return {
            'agent_type': self.agent_type.value if self.agent_type else None,
            'base_allowed_count': len(self.allowed_syscalls),
            'blocked_count': len(self.blocked_syscalls),
            'network_allowed': self.settings.network_access_allowed,
            'sandbox_enabled': self.settings.sandbox_enabled
        }


def load_syscall_policy(agent_type: Optional[AgentType] = None, settings=None) -> SyscallPolicy:
    """
    Load syscall policy for an agent type

    Args:
        agent_type: Type of agent loading the policy
        settings: Optional settings override

    Returns:
        Configured SyscallPolicy instance
    """
    return SyscallPolicy(agent_type, settings)


def get_default_policy() -> SyscallPolicy:
    """Get default syscall policy (no agent type specified)"""
    return SyscallPolicy()
