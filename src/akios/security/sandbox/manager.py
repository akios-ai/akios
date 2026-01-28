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
Sandbox process manager for AKIOS

Create and manage sandboxed processes with resource quotas.
Implements cgroups v2 + seccomp-bpf for true kernel-level isolation.
"""

import os
import subprocess
import signal
import threading
import time
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

from ...config import get_settings
from ...core.audit import append_audit_event
from .quotas import ResourceQuotas, enforce_hard_limits, QuotaViolationError
from ..syscall.interceptor import SyscallInterceptor


class SandboxViolationError(Exception):
    """Raised when sandbox constraints are violated"""
    pass


class SandboxManager:
    """
    Process sandbox manager using kernel isolation

    Creates sandboxed processes with resource limits and syscall restrictions.
    Uses cgroups v2 + seccomp-bpf for true kernel-level isolation.
    """

    def __init__(self):
        self.settings = get_settings()
        self.active_processes: Dict[int, subprocess.Popen] = {}
        self.quotas = ResourceQuotas()
        self.monitoring_threads: Dict[int, threading.Thread] = {}
        self.monitoring_active = False
        self.monitoring_lock = threading.Lock()
        self.cgroups_supported = self._check_cgroups_v2_support()
        self.cgroup_base_path = Path("/sys/fs/cgroup/akios")
        self.active_cgroups: Dict[int, Path] = {}

    def _check_cgroups_v2_support(self) -> bool:
        """
        Check if cgroups v2 is supported and available
        """
        cgroup_mount = Path("/sys/fs/cgroup")
        if not cgroup_mount.exists():
            return False

        # Check if cgroups v2 is mounted (unified hierarchy)
        try:
            # Check for cgroup.controllers file (cgroups v2 indicator)
            controllers_file = cgroup_mount / "cgroup.controllers"
            if controllers_file.exists():
                controllers = controllers_file.read_text().strip()
                if controllers:  # If controllers are available, cgroups v2 is active
                    return True

            # Alternative: check filesystem type
            with open("/proc/mounts", "r") as f:
                for line in f:
                    if "cgroup2" in line and "/sys/fs/cgroup" in line:
                        return True

        except (OSError, IOError):
            pass

        return False

    def _create_cgroup(self, process_name: str) -> Optional[Path]:
        """
        Create a cgroups v2 hierarchy for process isolation
        """
        if not self.cgroups_supported:
            return None

        try:
            # Ensure base cgroup directory exists
            self.cgroup_base_path.mkdir(parents=True, exist_ok=True)

            # Create unique cgroup path
            cgroup_path = self.cgroup_base_path / f"{process_name}_{int(time.time())}"
            cgroup_path.mkdir(parents=True, exist_ok=True)

            # Set resource limits using cgroups v2 interface
            self._configure_cgroup_limits(cgroup_path)

            return cgroup_path

        except (OSError, PermissionError) as e:
            # Check if we're in a containerized environment where cgroups are read-only
            # This is expected behavior in Docker containers - suppress warning
            if self._is_container_environment():
                # Silent failure in container environments - this is expected
                return None
            else:
                # Show warning in native environments where cgroup creation should work
                cgroup_name = f"{process_name}_{int(time.time())}"
                print(f"Warning: Failed to create cgroup {self.cgroup_base_path / cgroup_name}: {e}", file=__import__('sys').stderr)
                return None

    def _is_container_environment(self) -> bool:
        """
        Detect if we're running in a containerized environment.

        Uses centralized detection from security.validation module.
        """
        try:
            from ..validation import _is_container_environment
            return _is_container_environment()
        except ImportError:
            # Fallback to basic detection if validation module not available
            import os
            return os.path.exists('/.dockerenv')

    def _configure_cgroup_limits(self, cgroup_path: Path) -> None:
        """
        Configure resource limits for a cgroups v2 hierarchy
        """
        try:
            # CPU limit (convert percentage to quota)
            if hasattr(self.settings, 'cpu_limit') and self.settings.cpu_limit:
                cpu_quota = int(self.settings.cpu_limit * 100000)  # cgroup uses micro-seconds per period
                cpu_max_file = cgroup_path / "cpu.max"
                cpu_max_file.write_text(f"{cpu_quota} 100000\n")

            # Memory limit
            if hasattr(self.settings, 'memory_limit_mb') and self.settings.memory_limit_mb:
                memory_bytes = self.settings.memory_limit_mb * 1024 * 1024
                memory_max_file = cgroup_path / "memory.max"
                memory_max_file.write_text(f"{memory_bytes}\n")

        except (OSError, PermissionError, AttributeError) as e:
            print(f"Warning: Failed to configure cgroup limits: {e}", file=__import__('sys').stderr)

    def _move_process_to_cgroup(self, pid: int, cgroup_path: Path) -> bool:
        """
        Move a process into a cgroups v2 hierarchy
        """
        if not self.cgroups_supported or not cgroup_path.exists():
            return False

        try:
            # Write PID to cgroup.procs to move process into cgroup
            cgroup_procs_file = cgroup_path / "cgroup.procs"
            cgroup_procs_file.write_text(f"{pid}\n")
            return True

        except (OSError, PermissionError) as e:
            print(f"Warning: Failed to move process {pid} to cgroup: {e}", file=__import__('sys').stderr)
            return False

    def _cleanup_cgroup(self, cgroup_path: Path) -> None:
        """
        Clean up a cgroups v2 hierarchy
        """
        if not self.cgroups_supported or not cgroup_path.exists():
            return

        try:
            # Move processes back to root cgroup first
            cgroup_procs_file = cgroup_path / "cgroup.procs"
            root_procs_file = self.cgroup_base_path.parent / "cgroup.procs"

            if cgroup_procs_file.exists():
                try:
                    procs = cgroup_procs_file.read_text().strip().split('\n')
                    for proc in procs:
                        if proc.strip():
                            root_procs_file.write_text(f"{proc}\n")
                except (OSError, PermissionError):
                    pass

            # Remove the cgroup directory
            cgroup_path.rmdir()

        except (OSError, PermissionError) as e:
            # Retry once after a short delay in case of temporary permission issues
            try:
                time.sleep(0.1)  # Brief delay before retry
                cgroup_path.rmdir()
            except (OSError, PermissionError):
                print(f"Warning: Failed to cleanup cgroup {cgroup_path}: {e}", file=__import__('sys').stderr)

    def create_sandboxed_process(self, command: List[str], **kwargs) -> subprocess.Popen:
        """
        Create a sandboxed subprocess with resource limits

        Args:
            command: Command to execute as list
            **kwargs: Additional subprocess arguments

        Returns:
            Sandboxed subprocess.Popen instance

        Raises:
            SandboxViolationError: If sandbox setup fails
        """
        if not self.settings.sandbox_enabled:
            # Create process without sandboxing
            try:
                process = subprocess.Popen(command, **kwargs)
                self.active_processes[process.pid] = process
                return process
            except Exception as e:
                raise SandboxViolationError(f"Failed to create process: {e}") from e

        # Set up sandbox environment
        try:
            # Apply resource limits to current process before forking
            enforce_hard_limits()

            # Create environment with restricted variables
            env = self._create_restricted_environment()

            # Set up process arguments with restrictions
            proc_kwargs = {
                'env': env,
                'preexec_fn': self._setup_process_restrictions,
                **kwargs
            }

            # Create the subprocess
            process = subprocess.Popen(command, **proc_kwargs)
            self.active_processes[process.pid] = process

            # Create and apply cgroups v2 limits if available
            cgroup_path = self._create_cgroup(f"process_{process.pid}")
            if cgroup_path:
                if self._move_process_to_cgroup(process.pid, cgroup_path):
                    self.active_cgroups[process.pid] = cgroup_path
                else:
                    # Clean up cgroup if we couldn't move the process
                    self._cleanup_cgroup(cgroup_path)

            # Start resource monitoring for this process
            self._start_resource_monitoring(process)

            return process

        except QuotaViolationError:
            # Re-raise quota violations
            raise
        except Exception as e:
            raise SandboxViolationError(f"Failed to create sandboxed process: {e}") from e

    def _create_restricted_environment(self) -> Dict[str, str]:
        """
        Create restricted environment variables for sandboxed processes

        Removes potentially dangerous environment variables and sets safe defaults.
        """
        # Start with minimal environment
        safe_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',  # Minimal PATH
            'HOME': '/tmp',  # Safe home directory
            'TMPDIR': '/tmp',
            'USER': 'sandbox',
            'SHELL': '/bin/sh',
        }

        # Copy only safe environment variables from current environment
        safe_vars = {'LANG', 'LC_ALL', 'LC_CTYPE', 'TERM'}

        for var in safe_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]

        return safe_env

    def _setup_process_restrictions(self) -> None:
        """
        Set up process restrictions before execution

        This runs in the child process before the target command executes.
        Applies additional restrictions using POSIX mechanisms.
        """
        try:
            # Set process group to prevent signals from affecting parent
            os.setpgrp()

            # Change to safe working directory
            os.chdir('/tmp')

            # Apply additional resource limits
            self.quotas.apply_all_quotas()

            # Remove supplementary groups
            try:
                os.setgroups([])
            except (OSError, PermissionError):
                pass  # May not be allowed in some environments

            # Set restrictive umask
            os.umask(0o077)

            # Enable syscall interception using seccomp-bpf
            try:
                interceptor = SyscallInterceptor()
                interceptor.enable_interception()
            except Exception as e:
                # If seccomp setup fails, log but don't fail - fall back to policy checking
                # Suppress warning in container environments where seccomp is not available
                if not self._is_container_environment():
                    print(f"Warning: Failed to setup syscall interception: {e}", file=__import__('sys').stderr)

        except Exception:
            # If restrictions fail, exit immediately
            os._exit(1)

    def destroy_sandboxed_process(self, process: subprocess.Popen, timeout: float = 5.0) -> None:
        """
        Safely destroy a sandboxed process

        Args:
            process: Process to destroy
            timeout: Seconds to wait before force-killing
        """
        if process.pid not in self.active_processes:
            return

        try:
            # Try graceful termination first
            process.terminate()

            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't respond
                process.kill()
                try:
                    process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    # If still alive, something is very wrong
                    try:
                        os.kill(process.pid, signal.SIGKILL)
                    except (OSError, ProcessLookupError):
                        pass  # Process may already be gone

        except (OSError, ProcessLookupError):
            pass  # Process may already be gone
        finally:
            # Clean up tracking
            self.active_processes.pop(process.pid, None)

    def cleanup_all_processes(self) -> None:
        """Clean up all active sandboxed processes"""
        for process in list(self.active_processes.values()):
            self.destroy_sandboxed_process(process)

        # Clean up cgroups
        for pid, cgroup_path in list(self.active_cgroups.items()):
            self._cleanup_cgroup(cgroup_path)

        self.active_processes.clear()
        self.active_cgroups.clear()

    def get_process_status(self, pid: int) -> Optional[Dict[str, Any]]:
        """
        Get status information for a sandboxed process

        Args:
            pid: Process ID

        Returns:
            Dict with process status info, or None if not found
        """
        if pid not in self.active_processes:
            return None

        process = self.active_processes[pid]

        try:
            return {
                'pid': pid,
                'alive': process.poll() is None,
                'returncode': process.returncode,
                'command': process.args if hasattr(process, 'args') else None
            }
        except Exception:
            return {
                'pid': pid,
                'alive': False,
                'error': 'Unable to get process status'
            }

    def _start_resource_monitoring(self, process: subprocess.Popen) -> None:
        """
        Start resource monitoring for a subprocess

        Args:
            process: The subprocess to monitor
        """
        if not self.settings.sandbox_enabled:
            return

        def monitor_resources():
            """Monitor process resources and kill if limits exceeded"""
            try:
                import psutil
                psutil_process = psutil.Process(process.pid)
                monitoring_start = time.time()

                while process.poll() is None:  # While process is still running
                    try:
                        # Check CPU usage
                        cpu_percent = psutil_process.cpu_percent(interval=0.1)
                        if cpu_percent > (self.settings.cpu_limit * 100):
                            self._kill_process_for_quota_violation(
                                process, 'cpu', cpu_percent, self.settings.cpu_limit * 100
                            )
                            return

                        # Check memory usage
                        memory_info = psutil_process.memory_info()
                        memory_mb = memory_info.rss / (1024 * 1024)
                        if memory_mb > self.settings.memory_limit_mb:
                            self._kill_process_for_quota_violation(
                                process, 'memory', memory_mb, self.settings.memory_limit_mb
                            )
                            return

                        # Check if process has been running too long
                        runtime = time.time() - monitoring_start
                        if runtime > 300:  # 5 minutes max runtime
                            self._kill_process_for_quota_violation(
                                process, 'runtime', runtime, 300
                            )
                            return

                        time.sleep(1.0)  # Check every 1000ms

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process ended or we can't monitor it
                        break
                    except Exception as e:
                        # Log monitoring error but continue
                        print(f"Resource monitoring error for PID {process.pid}: {e}", file=__import__('sys').stderr)
                        break

            except Exception as e:
                # Suppress monitoring warnings in container environments where process monitoring
                # may not work reliably due to container isolation
                if not self._is_container_environment():
                    print(f"Failed to monitor process {process.pid}: {e}", file=__import__('sys').stderr)
            finally:
                with self.monitoring_lock:
                    self.monitoring_threads.pop(process.pid, None)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()

        with self.monitoring_lock:
            self.monitoring_threads[process.pid] = monitor_thread

    def _kill_process_for_quota_violation(self, process: subprocess.Popen,
                                        resource_type: str, actual_value: float,
                                        limit_value: float) -> None:
        """
        Kill a process for exceeding resource quota and log the event

        Args:
            process: Process to kill
            resource_type: Type of resource that was exceeded
            actual_value: Actual resource usage
            limit_value: Resource limit that was exceeded
        """
        try:
            # Kill the process
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)

        except Exception as e:
            print(f"Error killing process {process.pid}: {e}", file=__import__('sys').stderr)

        # Log quota violation event
        append_audit_event({
            'workflow_id': 'system',  # System-level event
            'step': 0,
            'agent': 'sandbox',
            'action': 'quota_violation_kill',
            'result': 'success',
            'metadata': {
                'pid': process.pid,
                'resource_type': resource_type,
                'actual_value': actual_value,
                'limit_value': limit_value,
                'violation_type': f'{resource_type}_limit_exceeded'
            }
        })

        # Remove from active processes
        with self.monitoring_lock:
            self.active_processes.pop(process.pid, None)


# Global manager instance
_manager = None

def get_sandbox_manager() -> SandboxManager:
    """Get the global sandbox manager instance"""
    global _manager
    if _manager is None:
        _manager = SandboxManager()
    return _manager

def create_sandboxed_process(command: List[str], **kwargs) -> subprocess.Popen:
    """
    Create a sandboxed subprocess

    Convenience function that uses the global manager.
    """
    manager = get_sandbox_manager()
    return manager.create_sandboxed_process(command, **kwargs)

def destroy_sandboxed_process(process: subprocess.Popen, timeout: float = 5.0) -> None:
    """
    Destroy a sandboxed subprocess

    Convenience function that uses the global manager.
    """
    manager = get_sandbox_manager()
    manager.destroy_sandboxed_process(process, timeout)

def cleanup_sandbox_processes() -> None:
    """
    Clean up all sandboxed processes

    Convenience function that uses the global manager.
    """
    manager = get_sandbox_manager()
    manager.cleanup_all_processes()
