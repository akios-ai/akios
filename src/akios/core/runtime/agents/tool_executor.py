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
Tool Executor Agent - External tool/command executor with sandboxed subprocess

Executes external commands while enforcing security boundaries.
"""

import subprocess
import shlex
import re
import os
from typing import Dict, Any, Optional, List

from .base import BaseAgent, AgentError
from akios.config import get_settings  # For test patching
# Delay security imports to avoid validation during package import
from akios.security.sandbox import get_sandbox_manager
from akios.core.audit import append_audit_event

# Pre-import PII redaction to avoid import hangs during agent execution
try:
    from akios.security.pii import apply_pii_redaction
except Exception:
    # SECURITY: Never silently disable PII redaction. If the module fails to import,
    # replace all content with a warning marker to prevent data leakage.
    import logging as _logging
    _logging.getLogger(__name__).critical(
        "PII redaction module failed to import — all content will be masked"
    )
    apply_pii_redaction = lambda x: "[PII_REDACTION_UNAVAILABLE]"


class ToolExecutorAgent(BaseAgent):
    """
    Tool executor agent for running external commands.

    Provides sandboxed subprocess execution with strict security controls.
    """

    _sandbox_info_emitted_workflows = set()

    def __init__(self, allowed_commands: Optional[List[str]] = None,
                 timeout: int = 30, max_output_size: int = 1024*1024, **kwargs):
        super().__init__(**kwargs)
        self.allowed_commands = allowed_commands or self._get_default_allowed_commands()
        self.timeout = timeout
        self.max_output_size = max_output_size

    def _emit_sandbox_info_once(self, parameters: Dict[str, Any]) -> None:
        workflow_id = parameters.get('workflow_id', 'unknown')
        if workflow_id in self._sandbox_info_emitted_workflows:
            return
        append_audit_event({
            'workflow_id': workflow_id,
            'step': parameters.get('step', 0),
            'agent': 'tool_executor',
            'action': 'sandbox_info',
            'result': 'info',
            'metadata': {
                'message': 'Sandbox validation/cleanup not supported (Docker policy-based mode)',
                'environment': 'docker' if os.path.exists('/.dockerenv') else 'native'
            }
        })
        self._sandbox_info_emitted_workflows.add(workflow_id)

    def _get_default_allowed_commands(self) -> List[str]:
        """Get default allowed commands (very restrictive)"""
        # Only allow safe, commonly needed commands
        return [
            'echo',
            'cat',
            'grep',
            'head',
            'tail',
            'wc',
            'sort',
            'uniq',
            'cut',
            'tr',
            'date',
            'pwd',
            'ls',
            'find',  # with restrictions
            'ps',    # for process monitoring
            'df',    # for disk space monitoring
            'free',  # for memory monitoring
            'sh',    # for shell scripts (safe usage)
            'true',  # for testing exit codes
            'false', # for testing exit codes
            'sleep', # for timeout testing
            'env',   # for environment variable testing
            'file'   # file type identification
        ]

    def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool/command action.

        Args:
            action: Action to perform ('execute', 'run', 'call')
            parameters: Command parameters

        Returns:
            Command execution result
        """
        self.validate_parameters(action, parameters)

        # Apply security before executing commands (delayed import)
        from akios.security import enforce_sandbox
        from akios.security.syscall.policy import AgentType
        enforce_sandbox(agent_type=AgentType.TOOL_EXECUTOR)

        # Extract args from parameters
        args = parameters.get('args', [])

        # Apply PII redaction to command arguments
        if args:
            original_args = args.copy()
            args = [apply_pii_redaction(str(arg)) if isinstance(arg, str) else arg for arg in args]
            if args != original_args:
                # Log PII redaction event
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'tool_executor',
                    'action': 'pii_redaction',
                    'result': 'success',
                    'command': parameters.get('command', ''),
                    'args_redacted': len([a for a, oa in zip(args, original_args) if a != oa])
                })

        # Build command from parameters
        command = parameters.get('command', '')
        # Apply PII redaction to command if it contains sensitive data
        original_command = command
        command = apply_pii_redaction(command)
        if command != original_command:
            append_audit_event({
                'workflow_id': parameters.get('workflow_id', 'unknown'),
                'step': parameters.get('step', 0),
                'agent': 'tool_executor',
                'action': 'pii_redaction',
                'result': 'success',
                'command_redacted': True
            })

        # Execute the command (validation happens inside _execute_command)
        result = self._execute_command(command, args if args else [], parameters)

        # Audit the command execution
        append_audit_event({
            'workflow_id': parameters.get('workflow_id', 'unknown'),
            'step': parameters.get('step', 0),
            'agent': 'tool_executor',
            'action': action,
            'result': 'success' if result.get('returncode') == 0 else 'error',
            'metadata': {
                'command': self._sanitize_command(command),
                'returncode': result.get('returncode'),
                'execution_time': result.get('execution_time', 0),
                'output_size': len(result.get('stdout', '')) + len(result.get('stderr', ''))
            }
        })

        # Apply PII redaction to command outputs
        if 'stdout' in result and isinstance(result['stdout'], str):
            original_stdout = result['stdout']
            result['stdout'] = apply_pii_redaction(result['stdout'])
            if result['stdout'] != original_stdout:
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'tool_executor',
                    'action': 'pii_output_redaction',
                    'result': 'success',
                    'command': self._sanitize_command(command),
                    'stdout_redacted': True
                })

        if 'stderr' in result and isinstance(result['stderr'], str):
            original_stderr = result['stderr']
            result['stderr'] = apply_pii_redaction(result['stderr'])
            if result['stderr'] != original_stderr:
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'tool_executor',
                    'action': 'pii_output_redaction',
                    'result': 'success',
                    'command': self._sanitize_command(command),
                    'stderr_redacted': True
                })

        return result

    def _execute_command(self, command: str, args: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the command in a sandboxed subprocess"""
        try:
            # Build command arguments
            if isinstance(command, str) and not args:
                # Use shlex to prevent shell injection for string commands
                cmd_args = shlex.split(command)
            elif isinstance(command, str) and args:
                # Command string with additional args
                cmd_args = [command] + args
            elif isinstance(command, list):
                # Command as list
                cmd_args = command
            else:
                # Default fallback
                cmd_args = [command] + args

            # Validate the complete command including all arguments
            self._validate_command_security(cmd_args)

            # Set up sandboxed execution environment
            env = self._get_sandboxed_env()

            # Merge in custom environment variables if provided
            custom_env = parameters.get('env', {})
            if custom_env:
                # Create a copy and merge custom vars (but don't override security-critical ones)
                env = env.copy()
                dangerous_vars = ['LD_PRELOAD', 'LD_LIBRARY_PATH', 'PYTHONPATH', 'PERL5LIB', 'PATH', 'SHELL']
                for key, value in custom_env.items():
                    if key not in dangerous_vars:
                        env[key] = str(value)

            work_dir = self._get_safe_working_directory()

            # Execute with sandboxed process manager for resource monitoring
            sandbox_manager = get_sandbox_manager()

            # Create monitored subprocess
            process = sandbox_manager.create_sandboxed_process(
                cmd_args,
                env=env,
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                if hasattr(sandbox_manager, "cleanup_process"):
                    sandbox_manager.cleanup_process(process.pid)
                else:
                    self._emit_sandbox_info_once(parameters)
                raise AgentError(f"Command timed out after {self.timeout} seconds: {command}")

            # Validate sandbox enforcement
            try:
                # Docker uses policy-based sandbox - skip kernel-specific validation/cleanup
                if hasattr(sandbox_manager, "validate_sandbox_enforcement"):
                    sandbox_status = sandbox_manager.validate_sandbox_enforcement(process.pid)
                    if not sandbox_status['enforced']:
                        # Log warning but don't fail - some sandbox features may not be available
                        append_audit_event({
                            'workflow_id': parameters.get('workflow_id', 'unknown'),
                            'step': parameters.get('step', 0),
                            'agent': 'tool_executor',
                            'action': 'sandbox_validation_warning',
                            'result': 'warning',
                            'metadata': {
                                'command': command,
                                'sandbox_issues': sandbox_status['issues'],
                                'pid': process.pid
                            }
                        })
                else:
                    self._emit_sandbox_info_once(parameters)
            except Exception as e:
                # Sandbox validation failed - log but don't break execution
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'tool_executor',
                    'action': 'sandbox_validation_error',
                    'result': 'warning',
                    'metadata': {
                        'command': command,
                        'validation_error': str(e),
                        'pid': process.pid
                    }
                })

            # Clean up sandbox resources
            try:
                if hasattr(sandbox_manager, "cleanup_process"):
                    sandbox_manager.cleanup_process(process.pid)
                else:
                    self._emit_sandbox_info_once(parameters)
            except Exception as e:
                # Cleanup failure is not critical
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'tool_executor',
                    'action': 'sandbox_cleanup_warning',
                    'result': 'warning',
                    'metadata': {
                        'command': command,
                        'cleanup_error': str(e),
                        'pid': process.pid
                    }
                })

            # Simulate subprocess.CompletedProcess result
            result = type('CompletedProcess', (), {
                'returncode': returncode,
                'stdout': stdout,
                'stderr': stderr
            })()

            # Apply PII redaction to command output

            original_stdout = result.stdout
            original_stderr = result.stderr

            result.stdout = apply_pii_redaction(result.stdout)
            result.stderr = apply_pii_redaction(result.stderr)

            # Check output size limits (after redaction)
            total_output = len(result.stdout) + len(result.stderr)
            if total_output > self.max_output_size:
                result.stdout = result.stdout[:self.max_output_size//2]
                result.stderr = result.stderr[:self.max_output_size//2]
                truncated = True
            else:
                truncated = False

            # Audit PII redaction in output
            stdout_redacted = result.stdout != original_stdout
            stderr_redacted = result.stderr != original_stderr

            if stdout_redacted or stderr_redacted:
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'tool_executor',
                    'action': 'pii_redaction_output',
                    'result': 'success',
                    'metadata': {
                        'command': command,
                        'stdout_redacted': stdout_redacted,
                        'stderr_redacted': stderr_redacted,
                        'truncated': truncated
                    }
                })

            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': command,
                'truncated': truncated,
                'timeout': self.timeout
            }

        except subprocess.TimeoutExpired:
            raise AgentError(f"Command timed out after {self.timeout} seconds: {command}")
        except (OSError, subprocess.SubprocessError) as e:
            raise AgentError(f"Command execution failed: {command} - {e}") from e

    def _get_sandboxed_env(self) -> Dict[str, str]:
        """Get sandboxed environment variables"""
        # Start with minimal environment
        safe_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',  # Restricted PATH
            'HOME': '/tmp',  # Safe home directory
            'USER': 'akios_agent',
            'SHELL': '/bin/sh'
        }

        # Remove potentially dangerous environment variables
        dangerous_vars = ['LD_PRELOAD', 'LD_LIBRARY_PATH', 'PYTHONPATH', 'PERL5LIB']
        for var in dangerous_vars:
            safe_env.pop(var, None)

        return safe_env

    def _get_safe_working_directory(self) -> str:
        """Get safe working directory for command execution"""
        import os
        import tempfile

        # Create a secure temporary directory for command execution
        work_dir = "/tmp/akios_work"
        try:
            # Create directory if it doesn't exist
            os.makedirs(work_dir, exist_ok=True)
            # Ensure proper permissions (owner read/write/execute only)
            os.chmod(work_dir, 0o700)
        except (OSError, PermissionError) as e:
            # Fallback to system temp directory if we can't create our preferred location
            work_dir = tempfile.mkdtemp(prefix="akios_work_")
            os.chmod(work_dir, 0o700)

        return work_dir

    def _validate_command_security(self, command: str) -> None:
        """Validate that the command is allowed and secure"""
        if isinstance(command, str):
            args = shlex.split(command)
        else:
            args = command

        if not args:
            raise AgentError("Empty command not allowed")

        # Check if base command is allowed
        base_command = args[0]
        if base_command not in self.allowed_commands:
            raise AgentError(f"Command not in allowed list: {base_command}")

        # Additional security checks
        dangerous_patterns = [
            'sudo', 'su', 'chmod', 'chown', 'rm', 'rmdir', 'dd', 'mkfs',
            'fdisk', 'mount', 'umount', 'kill', 'killall', 'pkill',
            'wget', 'curl', 'ssh', 'scp', 'ftp', 'telnet',
            'python', 'perl', 'ruby', 'bash', 'sh', 'zsh',
            '|', ';', '&&', '||', '`', '$('  # Shell operators
        ]

        for arg in args:
            arg_lower = arg.lower()
            for pattern in dangerous_patterns:
                # For shell operators, always check with regex (dangerous even embedded)
                if pattern in ['|', ';', '&&', '||', '`', '$(']:
                    if re.search(re.escape(pattern), arg):
                        raise AgentError(f"Dangerous shell operator detected: {pattern}")
                # For commands, check if pattern is in arg first, then validate as whole word
                elif pattern in arg and re.search(r'\b' + re.escape(pattern.lower()) + r'\b', arg_lower):
                    raise AgentError(f"Dangerous command detected: {pattern}")

        # Check for path traversal and validate absolute paths
        for arg in args:
            if '..' in arg:
                raise AgentError("Path traversal not allowed in commands")
            if arg.startswith('/'):
                # Allow specific project data paths for analysis
                if arg.startswith('/app/data/input/') or arg.startswith('/app/data/output/'):
                    continue  # Allow legitimate analysis file access
                elif arg.startswith('/app/audit'):
                    raise AgentError("Access to audit directory is not allowed")
                else:
                    raise AgentError("Absolute paths not allowed in commands (except project data)")

        # Check for audit directory access (critical security protection)
        # Only block actual filesystem paths, not harmless text mentions
        for arg in args:
            if self._is_filesystem_path(arg):
                raise AgentError("Access to audit directory is not allowed")

    def _is_filesystem_path(self, arg: str) -> bool:
        """
        Determine if argument looks like a filesystem path vs text content.

        Returns True if argument should be blocked (likely filesystem path).
        Returns False if argument should be allowed (likely text content).
        """
        # Skip arguments that are clearly text content
        if ' ' in arg:  # Contains spaces = likely text message
            return False
        if len(arg) > 100:  # Very long = likely text content
            return False
        if any(char in arg for char in ['@', '://', '\n', '\t']):  # Special chars = text
            return False

        # Check for actual filesystem path patterns to audit directory
        arg_lower = arg.lower()
        result = (
            arg_lower.startswith('./audit') or
            arg_lower.startswith('/audit') or
            arg_lower.startswith('audit/') or
            arg_lower == 'audit' or
            arg_lower == './audit' or
            arg_lower == '/audit'
        )
        return result

    def _sanitize_command(self, command: str) -> str:
        """Sanitize command for audit logging"""
        # Remove or mask sensitive information
        # For now, return as-is since the command validation already ensures safety
        return command

    def validate_parameters(self, action: str, parameters: Dict[str, Any]) -> None:
        """Validate action parameters"""
        if 'command' not in parameters:
            raise AgentError("Tool execution requires 'command' parameter")

        command = parameters['command']
        if not isinstance(command, (str, list)):
            raise AgentError("'command' must be a string or list")

    def get_supported_actions(self) -> List[str]:
        """Get supported actions"""
        return ['execute', 'run', 'call']

    def add_allowed_command(self, command: str) -> None:
        """Add an allowed command (admin operation)"""
        self.allowed_commands.append(command)

    @property
    def command_whitelist(self) -> List[str]:
        """Get the current command whitelist"""
        return self.allowed_commands.copy()
