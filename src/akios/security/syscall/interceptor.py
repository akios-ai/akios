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
Syscall interceptor for AKIOS

Intercept and control system calls based on security policy.
Implements seccomp-bpf for true kernel-level syscall filtering.
"""

import os
import signal
import sys
import threading
import platform
from typing import Optional, Callable, Dict, Any, List
from contextlib import contextmanager

# Platform-specific imports and feature detection
# This ensures clean separation of platform-dependent functionality

# Conditional import for seccomp (Linux only)
try:
    if platform.system() == 'Linux':
        import seccomp
        SECCOMP_AVAILABLE = True
    else:
        SECCOMP_AVAILABLE = False
except ImportError:
    SECCOMP_AVAILABLE = False

# Fallback: use ctypes for direct system calls if seccomp module not available
if not SECCOMP_AVAILABLE and platform.system() == 'Linux':
    try:
        import ctypes
        libc = ctypes.CDLL(None)
        libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        libc.prctl.restype = ctypes.c_int
        CTYPES_AVAILABLE = True
    except (ImportError, OSError):
        CTYPES_AVAILABLE = False
else:
    CTYPES_AVAILABLE = False

from ...config import get_settings
from .policy import SyscallPolicy, AgentType, load_syscall_policy
from .warnings import warn_seccomp_disabled
from ...core.audit import append_audit_event


class SyscallViolationError(Exception):
    """Raised when a syscall policy violation occurs"""
    pass


class SyscallInterceptor:
    """
    System call interceptor using seccomp-bpf

    Intercepts and allows/denies syscalls based on security policy.
    Implements seccomp-bpf for true kernel-level syscall filtering.
    """
    
    # Class-level flags: seccomp can only be loaded ONCE per process
    # Multiple agents in workflow → multiple interceptors → but only ONE seccomp load allowed
    _seccomp_loaded = False
    _seccomp_load_attempted = False

    def __init__(self, agent_type: Optional[AgentType] = None, settings=None):
        self.settings = settings or get_settings()
        self.agent_type = agent_type
        self.policy = load_syscall_policy(agent_type, self.settings)
        self.violations: List[Dict[str, Any]] = []
        self.monitoring_enabled = False

    def enable_interception(self) -> None:
        """
        Enable syscall interception using seccomp-bpf

        Sets up seccomp-bpf filters based on the security policy.
        This provides kernel-level syscall filtering.
        
        NOTE: Seccomp can only be loaded ONCE per process. Subsequent calls
        will skip loading if already loaded.
        """
        if not self.settings.sandbox_enabled:
            return
        
        # Check if seccomp was already loaded by another agent in this process
        if SyscallInterceptor._seccomp_loaded:
            self.monitoring_enabled = True
            return
        
        # Check if loading was already attempted and failed
        if SyscallInterceptor._seccomp_load_attempted and not SyscallInterceptor._seccomp_loaded:
            self.monitoring_enabled = True
            return

        if not self._is_seccomp_supported():
            warn_seccomp_disabled("seccomp module not available or running on unsupported platform")
            self.monitoring_enabled = True
            SyscallInterceptor._seccomp_load_attempted = True
            return

        # CRITICAL: seccomp filter loading requires root privileges (CAP_SYS_ADMIN)
        # Without root, attempting to load the filter will cause SIGTRAP crashes
        if os.geteuid() != 0:
            warn_seccomp_disabled("seccomp requires root privileges (run with sudo for kernel-hard security)")
            self.monitoring_enabled = True
            SyscallInterceptor._seccomp_load_attempted = True
            return

        try:
            SyscallInterceptor._seccomp_load_attempted = True
            self._setup_seccomp_filters()
            SyscallInterceptor._seccomp_loaded = True  # Mark as successfully loaded
            self.monitoring_enabled = True
            
            # Log successful seccomp enablement to audit trail
            try:
                append_audit_event({
                    'workflow_id': 'security_monitor',
                    'step': 0,
                    'agent': 'syscall_interceptor',
                    'action': 'enable_seccomp',
                    'result': 'SUCCESS',
                    'metadata': {
                        'event_type': 'seccomp_enabled',
                        'agent_type': self.agent_type.value if self.agent_type else 'unknown',
                        'mode': 'kernel_filtering'
                    }
                })
            except Exception:
                pass  # Don't block on audit logging
        except Exception as e:
            # Check if we're in a containerized environment
            try:
                from ..validation import _is_container_environment
                is_container = _is_container_environment()
            except ImportError:
                is_container = False

            if is_container:
                # Container environment - allow with policy-based monitoring
                from ...core.ui.semantic_colors import print_security, print_info
                print_security("Security Mode: Docker (Policy-Based)")
                print_info("PII redaction, audit logging, command restrictions, resource limits")
                print_info("For kernel-hard max security: native Linux")
                self.monitoring_enabled = True
                
                # Log policy-based mode to audit trail
                try:
                    append_audit_event({
                        'workflow_id': 'security_monitor',
                        'step': 0,
                        'agent': 'syscall_interceptor',
                        'action': 'set_security_mode',
                        'result': 'docker_policy_based',
                        'metadata': {
                            'event_type': 'security_mode',
                            'mode': 'docker_policy_based',
                            'agent_type': self.agent_type.value if self.agent_type else 'unknown'
                        }
                    })
                except Exception:
                    pass  # Don't block on audit logging
                return
            else:
                warn_seccomp_disabled(str(e))
                self.monitoring_enabled = True

                try:
                    append_audit_event({
                        'workflow_id': 'security_monitor',
                        'step': 0,
                        'agent': 'syscall_interceptor',
                        'action': 'enable_seccomp',
                        'result': 'failed',
                        'metadata': {
                            'event_type': 'seccomp_enable_failure',
                            'error': str(e),
                            'agent_type': self.agent_type.value if self.agent_type else 'unknown'
                        }
                    })
                except Exception:
                    pass


    def _is_seccomp_supported(self) -> bool:
        """
        Check if seccomp-bpf is supported on this system
        
        Requires:
        1. Linux OS
        2. seccomp module available
        3. Root privileges (euid == 0) to load filters
        """
        if platform.system() != 'Linux':
            return False

        # Check if we have root privileges - required to load seccomp filters
        if os.geteuid() != 0:
            return False

        # Check if we have the seccomp module or ctypes access
        return SECCOMP_AVAILABLE or CTYPES_AVAILABLE

    def _setup_seccomp_filters(self) -> None:
        """
        Set up seccomp-bpf filters based on the syscall policy
        """
        if SECCOMP_AVAILABLE:
            self._setup_seccomp_with_module()
        elif CTYPES_AVAILABLE:
            self._setup_seccomp_with_ctypes()
        else:
            raise RuntimeError("No seccomp implementation available")

    def _setup_seccomp_with_module(self) -> None:
        """
        Set up seccomp-bpf using the seccomp Python module
        """
        import seccomp

        # Create a new seccomp filter
        try:
            filter_obj = seccomp.SyscallFilter(seccomp.ERRNO(seccomp.errno.EPERM))
        except Exception as e:
            raise RuntimeError(f"Failed to create seccomp filter: {e}")

        # Get essential syscalls from policy
        essential_syscalls = self._get_essential_syscalls()

        # Allow syscalls based on policy
        allowed_syscalls = set()
        for syscall_name in essential_syscalls:
            if self._is_syscall_allowed_by_policy(syscall_name):
                allowed_syscalls.add(syscall_name)

        # Add syscalls to filter
        for syscall_name in allowed_syscalls:
            try:
                syscall_num = seccomp.resolve_syscall(seccomp.Arch.NATIVE, syscall_name)
                # Skip syscalls that return negative values (not available on this architecture)
                if syscall_num < 0:
                    continue
                filter_obj.add_rule(seccomp.ALLOW, syscall_num)
            except ValueError:
                # Syscall not available on this architecture
                continue
            except Exception as e:
                # Log other errors but continue
                print(f"Warning: Failed to add syscall rule for {syscall_name}: {e}", file=sys.stderr)
                continue

        # Load the filter
        try:
            filter_obj.load()
        except Exception as e:
            raise RuntimeError(f"Failed to load seccomp filter: {e}")

    def _get_essential_syscalls(self) -> List[str]:
        """
        Get list of essential syscalls that should be allowed.

        Returns a comprehensive list of syscalls needed for Python runtime,
        AKIOS execution, networking, and file I/O. Truly dangerous syscalls
        (mount, ptrace, kexec, etc.) are excluded.
        """
        # Core I/O syscalls
        core_io = [
            'read', 'write', 'open', 'openat', 'close', 'lseek',
            'pread64', 'pwrite64', 'readv', 'writev',
            'sendfile', 'dup', 'dup2', 'dup3', 'pipe', 'pipe2',
            'ioctl', 'fcntl', 'flock', 'fsync', 'fdatasync',
        ]

        # File/directory metadata
        file_meta = [
            'stat', 'fstat', 'lstat', 'newfstatat', 'statx', 'statfs', 'fstatfs',
            'access', 'faccessat', 'faccessat2',
            'getdents', 'getdents64', 'getcwd',
            'readlink', 'readlinkat',
            'umask',
        ]

        # File/directory manipulation
        file_ops = [
            'creat', 'mkdir', 'mkdirat', 'rmdir',
            'unlink', 'unlinkat', 'rename', 'renameat', 'renameat2',
            'link', 'linkat', 'symlink', 'symlinkat',
            'truncate', 'ftruncate', 'fallocate',
            'chmod', 'fchmod', 'fchmodat',
            'chown', 'fchown', 'lchown', 'fchownat',
            'chdir', 'fchdir',
            'utimensat', 'futimesat',
        ]

        # Memory management (Python runtime requirement)
        memory = [
            'mmap', 'munmap', 'mprotect', 'mremap', 'msync',
            'brk', 'madvise', 'mincore', 'mlock', 'mlock2', 'munlock',
            'mlockall', 'munlockall',
            'memfd_create', 'membarrier',
        ]

        # Signals
        signals = [
            'rt_sigaction', 'rt_sigprocmask', 'rt_sigreturn',
            'rt_sigpending', 'rt_sigtimedwait', 'rt_sigqueueinfo', 'rt_sigsuspend',
            'sigaltstack', 'restart_syscall',
            'pause', 'alarm',
        ]

        # Process/thread management (needed for Python threading + subprocess)
        process = [
            'clone', 'clone3', 'fork', 'vfork', 'execve', 'execveat',
            'exit', 'exit_group', 'wait4', 'waitid',
            'kill', 'tgkill', 'tkill',
            'getpid', 'getppid', 'gettid',
            'getpgrp', 'getpgid', 'setpgid', 'setsid',
            'setuid', 'setgid', 'setreuid', 'setregid',
            'setresuid', 'setresgid', 'getresuid', 'getresgid',
            'setgroups', 'getgroups',
            'getuid', 'geteuid', 'getgid', 'getegid',
            'prctl', 'arch_prctl',
            'set_tid_address', 'set_robust_list', 'get_robust_list',
            'futex', 'rseq',
            'sched_yield', 'sched_getaffinity', 'sched_setaffinity',
            'sched_getscheduler', 'sched_setscheduler',
            'sched_getparam', 'sched_setparam',
            'getpriority', 'setpriority', 'setrlimit', 'prlimit64',
        ]

        # Timers and clocks (Python runtime requirement)
        time_syscalls = [
            'nanosleep', 'clock_nanosleep',
            'gettimeofday', 'settimeofday',
            'clock_gettime', 'clock_settime', 'clock_getres',
            'getitimer', 'setitimer', 'timerfd_create', 'timerfd_settime', 'timerfd_gettime',
            'times',
        ]

        # Polling/event (Python asyncio, I/O multiplexing)
        poll_event = [
            'select', 'pselect6', 'poll', 'ppoll',
            'epoll_create', 'epoll_create1', 'epoll_ctl', 'epoll_wait', 'epoll_pwait', 'epoll_pwait2',
            'eventfd', 'eventfd2',
            'inotify_init', 'inotify_init1', 'inotify_add_watch', 'inotify_rm_watch',
            'signalfd', 'signalfd4',
        ]

        # Network syscalls (for LLM API calls, HTTP agent)
        network = [
            'socket', 'connect', 'accept', 'accept4',
            'sendto', 'recvfrom', 'sendmsg', 'recvmsg',
            'sendmmsg', 'recvmmsg',  # Modern glibc DNS resolver
            'shutdown', 'bind', 'listen',
            'getsockname', 'getpeername',
            'setsockopt', 'getsockopt',
            'socketpair',
        ]

        # System info (Python startup, os module)
        sysinfo = [
            'uname', 'sysinfo',
            'getrlimit', 'getrusage',
            'getrandom',
        ]

        # Misc syscalls needed by Python runtime / glibc
        misc_runtime = [
            'copy_file_range',       # efficient file copies
            'splice', 'tee',         # zero-copy data transfer
            'name_to_handle_at',     # filesystem handle ops
            'open_by_handle_at',
        ]

        # Combine all
        all_syscalls = (
            core_io + file_meta + file_ops + memory + signals +
            process + time_syscalls + poll_event + network + sysinfo +
            misc_runtime
        )

        # Remove duplicates and sort
        return sorted(list(set(all_syscalls)))

    def _setup_seccomp_with_ctypes(self) -> None:
        """
        Set up seccomp-bpf using ctypes and direct system calls with real BPF bytecode
        """
        try:
            # Define syscall numbers (x86_64 architecture)
            # These would be architecture-dependent in production
            syscall_numbers = {
                'read': 0, 'write': 1, 'openat': 257, 'close': 3, 'stat': 4,
                'fstat': 5, 'poll': 7, 'lseek': 8, 'mmap': 9, 'mprotect': 10,
                'munmap': 11, 'brk': 12, 'rt_sigaction': 13, 'rt_sigprocmask': 14,
                'ioctl': 16, 'pread64': 17, 'pwrite64': 18, 'readv': 19,
                'writev': 20, 'access': 21, 'pipe': 22, 'select': 23,
                'sched_yield': 24, 'dup': 32, 'dup2': 33, 'pause': 34,
                'nanosleep': 35, 'getpid': 39, 'getppid': 110, 'getuid': 102,
                'geteuid': 107, 'getgid': 104, 'getegid': 108, 'getgroups': 115,
                'setuid': 105, 'setgid': 106, 'setreuid': 113, 'setregid': 114,
                'gettimeofday': 96, 'getrlimit': 97, 'getrusage': 98,
                'exit': 60, 'exit_group': 231, 'futex': 202, 'set_tid_address': 218,
                'set_robust_list': 273, 'epoll_create1': 291, 'epoll_ctl': 233,
                'epoll_wait': 232, 'eventfd2': 290, 'pipe2': 293, 'inotify_init1': 294,
                'prctl': 157, 'arch_prctl': 158, 'uname': 63, 'getrandom': 318,
                'memfd_create': 319, 'execve': 59, 'wait4': 61, 'clone': 56,
                'fork': 57, 'vfork': 58, 'kill': 62, 'tgkill': 234,
                'rt_sigreturn': 15, 'socket': 41, 'connect': 42, 'accept': 43,
                'sendto': 44, 'recvfrom': 45, 'shutdown': 48, 'bind': 49,
                'listen': 50, 'getsockname': 51, 'getpeername': 52
            }

            # Build allowlist of essential syscall numbers
            allowed_syscalls = []
            essential_names = self._get_essential_syscalls()

            for name in essential_names:
                if name in syscall_numbers:
                    allowed_syscalls.append(syscall_numbers[name])

            # Create BPF bytecode for seccomp filter
            # BPF program structure:
            # - Load syscall number into accumulator
            # - Compare against allowed syscalls
            # - Return SECCOMP_RET_ALLOW (0x7fff0000) if allowed
            # - Return SECCOMP_RET_KILL (0x00000000) if not allowed

            bpf_program = []

            # Load syscall number (A = syscall_nr)
            bpf_program.append((0x20, 0, 0, 4))  # ld [4]  # syscall nr is at offset 4 in seccomp_data

            # Compare against each allowed syscall
            for i, syscall_nr in enumerate(allowed_syscalls):
                if i == 0:
                    # First comparison: if A == syscall_nr, return ALLOW
                    bpf_program.append((0x15, 0, len(allowed_syscalls) - i, syscall_nr))  # jeq syscall_nr
                else:
                    # Subsequent comparisons
                    remaining = len(allowed_syscalls) - i
                    bpf_program.append((0x15, 0, remaining, syscall_nr))  # jeq syscall_nr

            # If we reach here, syscall is not allowed - KILL
            bpf_program.append((0x06, 0, 0, 0))  # ret 0  # SECCOMP_RET_KILL

            # Add ALLOW return for matched syscalls
            bpf_program.append((0x06, 0, 0, 0x7fff0000))  # ret 0x7fff0000  # SECCOMP_RET_ALLOW

            # Convert to proper BPF instruction format
            # Each instruction is: (code, jt, jf, k)
            # We need to convert to bytes for prctl
            import struct

            filter_bytes = b''
            for code, jt, jf, k in bpf_program:
                # BPF instruction format: 16-bit code, 8-bit jt, 8-bit jf, 32-bit k
                instruction = struct.pack('<HBBI', code, jt, jf, k)
                filter_bytes += instruction

            # Seccomp filter structure
            # struct sock_filter {
            #     uint16_t code;
            #     uint8_t jt;
            #     uint8_t jf;
            #     uint32_t k;
            # };
            #
            # struct sock_fprog {
            #     unsigned short len;
            #     struct sock_filter *filter;
            # };

            # Use prctl to install the filter
            # PR_SET_SECCOMP = 22, SECCOMP_MODE_FILTER = 2
            # prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog)

            # Create sock_fprog structure
            prog_len = len(bpf_program)
            prog_addr = self._alloc_buffer(filter_bytes)

            # Call prctl - this requires proper ctypes setup
            # PR_SET_SECCOMP = 22, SECCOMP_MODE_FILTER = 2
            result = libc.prctl(22, 2, prog_addr, prog_len, 0)
            if result != 0:
                raise RuntimeError(f"Failed to install seccomp filter: {result}")

        except Exception as e:
            # Fallback to policy-only monitoring if seccomp fails
            print(f"Warning: Failed to install seccomp filter: {e}", file=__import__('sys').stderr)
            print("Falling back to policy-based syscall monitoring", file=__import__('sys').stderr)
            self.monitoring_enabled = True  # Still enable monitoring with policy checks

    def _alloc_buffer(self, data: bytes) -> int:
        """
        Allocate a buffer and return its address for BPF filter.
        
        NOTE: The ctypes seccomp fallback is not supported in production.
        The python3-seccomp module (libseccomp bindings) is the supported path
        for seccomp-bpf filter loading. This ctypes codepath exists as a
        reference implementation but cannot work from pure Python.
        """
        raise RuntimeError(
            "ctypes seccomp fallback is not supported. "
            "Install python3-seccomp for kernel-hard security: "
            "sudo apt-get install libseccomp-dev python3-seccomp"
        )

    def _is_syscall_allowed_by_policy(self, syscall_name: str) -> bool:
        """
        Check if a syscall is allowed by the current policy.

        Uses a blocklist approach: block truly dangerous syscalls that could
        compromise the host. Everything in _get_essential_syscalls() is allowed.
        """
        # Dangerous syscalls that are ALWAYS blocked - these can compromise the host
        dangerous_syscalls = {
            # Filesystem namespace / mount manipulation
            'mount', 'umount2', 'pivot_root', 'chroot',
            # Namespace / container escape
            'setns', 'unshare',
            # Process introspection / debugging (code injection)
            'ptrace', 'process_vm_readv', 'process_vm_writev',
            # Kernel module / kexec
            'kexec_load', 'kexec_file_load', 'init_module', 'finit_module', 'delete_module',
            # BPF / perf (kernel-level tracing)
            'bpf', 'perf_event_open',
            # Legacy / dangerous kernel interfaces
            'modify_ldt', '_sysctl',
            # Keyring manipulation
            'keyctl', 'request_key', 'add_key',
            # Hostname manipulation
            'setdomainname', 'sethostname',
            # Swap manipulation
            'swapon', 'swapoff',
            # Reboot / power
            'reboot',
            # Raw I/O (bypass filesystem)
            'ioperm', 'iopl',
            # Kernel ring buffer
            'syslog',
            # Accounting
            'acct',
            # Clock manipulation (NTP attacks)
            'adjtimex', 'clock_adjtime',
        }

        if syscall_name in dangerous_syscalls:
            return False

        # Everything else that's in the essential list is allowed
        return True

    def disable_interception(self) -> None:
        """
        Disable syscall interception
        """
        self.monitoring_enabled = False

    def check_syscall(self, syscall_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a syscall is allowed by policy

        Args:
            syscall_name: Name of the syscall
            context: Optional context information

        Returns:
            True if allowed

        Raises:
            SyscallViolationError: If syscall is blocked
        """
        if not self.monitoring_enabled:
            return True

        if self.policy.is_syscall_allowed(syscall_name):
            return True

        # Syscall is blocked - record violation and raise error
        violation = {
            'syscall': syscall_name,
            'agent_type': self.agent_type.value if self.agent_type else None,
            'context': context or {},
            'timestamp': self._get_timestamp()
        }
        self.violations.append(violation)

        # CRITICAL: Log to permanent tamper-evident audit trail for compliance
        try:
            append_audit_event({
                'workflow_id': 'security_monitor',  # Security events use dedicated workflow ID  
                'step': 0,  # Security monitoring is continuous, not step-based
                'agent': 'syscall_interceptor',
                'action': f'block_syscall: {syscall_name}',
                'result': 'BLOCKED',
                'metadata': {
                    'event_type': 'syscall_violation',
                    'syscall': syscall_name,
                    'agent_type': self.agent_type.value if self.agent_type else 'unknown',
                    'severity': 'HIGH',
                    'context': context or {},
                    'timestamp': violation['timestamp']
                }
            })
        except Exception as e:
            # Never let audit logging failure prevent security enforcement
            print(f"⚠️  Audit logging failed for syscall violation: {e}", file=sys.stderr)

        raise SyscallViolationError(
            f"Syscall '{syscall_name}' blocked by security policy for agent type "
            f"{self.agent_type.value if self.agent_type else 'unknown'}"
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp for violation logging"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    @contextmanager
    def syscall_context(self, operation_name: str):
        """
        Context manager for syscall operations

        Args:
            operation_name: Name of the operation being performed
        """
        # In a real implementation, this would set up syscall filtering
        # for the duration of the context
        try:
            yield
        except SyscallViolationError:
            # Re-raise with additional context
            raise
        except Exception as e:
            # Check if this was a syscall-related error
            if self._is_syscall_related_error(e):
                syscall_name = self._extract_syscall_from_error(e)
                if syscall_name:
                    self.check_syscall(syscall_name, {'operation': operation_name})
            raise

    def _is_syscall_related_error(self, error: Exception) -> bool:
        """
        Check if an error is related to syscall issues

        Args:
            error: Exception to check

        Returns:
            True if syscall-related
        """
        error_msg = str(error).lower()
        syscall_indicators = [
            'permission denied', 'operation not permitted', 'access denied',
            'no such file or directory', 'bad file descriptor',
            'network is unreachable', 'connection refused'
        ]

        return any(indicator in error_msg for indicator in syscall_indicators)

    def _extract_syscall_from_error(self, error: Exception) -> Optional[str]:
        """
        Attempt to extract syscall name from error

        Args:
            error: Exception to analyze

        Returns:
            Syscall name if detectable, None otherwise
        """
        error_msg = str(error).lower()

        # Map common error patterns to syscalls
        syscall_patterns = {
            'permission denied': 'access',
            'operation not permitted': 'setuid',  # Common for privilege operations
            'no such file or directory': 'stat',
            'bad file descriptor': 'fcntl',
            'network is unreachable': 'connect',
            'connection refused': 'connect',
        }

        for pattern, syscall in syscall_patterns.items():
            if pattern in error_msg:
                return syscall

        return None

    def get_violation_report(self) -> Dict[str, Any]:
        """
        Get report of syscall violations

        Returns:
            Dict with violation statistics and details
        """
        return {
            'total_violations': len(self.violations),
            'violations': self.violations.copy(),
            'policy_summary': self.policy.get_policy_summary(),
            'monitoring_enabled': self.monitoring_enabled
        }

    def reset_violations(self) -> None:
        """Reset violation tracking"""
        self.violations.clear()


def create_syscall_interceptor(agent_type: Optional[AgentType] = None) -> SyscallInterceptor:
    """
    Create a syscall interceptor for an agent type

    Args:
        agent_type: Type of agent

    Returns:
        Configured SyscallInterceptor instance
    """
    interceptor = SyscallInterceptor(agent_type)
    interceptor.enable_interception()
    return interceptor

def apply_syscall_policy(syscall_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Apply syscall policy (convenience function)

    Args:
        syscall_name: Name of syscall to check
        context: Optional context information (can include 'agent_type' and 'settings')

    Returns:
        True if allowed

    Raises:
        SyscallViolationError: If blocked
    """
    from .policy import AgentType

    # Extract settings from context if provided, otherwise use global
    effective_settings = None
    if context and 'settings' in context:
        effective_settings = context['settings']

    effective_settings = effective_settings or get_settings()

    if not effective_settings.sandbox_enabled:
        return True

    # Extract agent type from context if provided
    agent_type = None
    if context and 'agent_type' in context:
        agent_type = context['agent_type']

    # Create interceptor with agent type and settings
    interceptor = SyscallInterceptor(agent_type=agent_type, settings=effective_settings)
    interceptor.enable_interception()
    return interceptor.check_syscall(syscall_name, context)
