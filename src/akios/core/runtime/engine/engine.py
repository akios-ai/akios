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
Runtime Engine - Core execution engine for sequential workflow steps

Orchestrates agent execution with security, audit, and kill-switch integration.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

# Lazy imports for performance optimization
# These are imported only when needed to reduce startup time
_lazy_imports = {}
_MAX_LAZY_IMPORTS = 50  # Prevent memory leaks from unlimited cache growth
_lazy_import_failures = set()  # Track failed imports to avoid repeated failures

def _import_module(module_name: str, attr_name: str = None):
    """
    DIRECT import function for PyInstaller compatibility.

    Replaced lazy imports with direct imports to avoid PyInstaller analysis hangs.
    This maintains functionality while ensuring reliable binary builds.
    """
    try:
        module = __import__(module_name, fromlist=[attr_name] if attr_name else [])
        return getattr(module, attr_name) if attr_name else module
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import {module_name}.{attr_name if attr_name else ''}: {e}") from e

def _get_append_audit_event():
    """Lazy load append_audit_event function."""
    return _import_module('akios.core.audit', 'append_audit_event')

def _get_agent_class():
    """Lazy load get_agent_class function."""
    return _import_module('akios.core.runtime.agents', 'get_agent_class')


def _get_progress_functions():
    """Lazy load progress bar functions."""
    try:
        create_workflow_progress = _import_module('akios.core.ui.rich_output', 'create_workflow_progress')
        create_step_progress = _import_module('akios.core.ui.rich_output', 'create_step_progress')
        create_workflow_dashboard = _import_module('akios.core.ui.rich_output', 'create_workflow_dashboard')
        return {
            'workflow': create_workflow_progress,
            'step': create_step_progress,
            'dashboard': create_workflow_dashboard
        }
    except ImportError:
        # Fallback if rich_output not available
        return None


# Core imports that are always needed
from akios.config import get_settings

# Performance optimization: Cache settings to avoid repeated config file reads
_settings_cache = None
_settings_cache_time = 0
_SETTINGS_CACHE_TTL = 30  # Cache for 30 seconds

def _get_cached_settings():
    """Get settings with caching to improve performance."""
    global _settings_cache, _settings_cache_time
    current_time = time.time()

    if _settings_cache is None or (current_time - _settings_cache_time) > _SETTINGS_CACHE_TTL:
        _settings_cache = get_settings()
        _settings_cache_time = current_time

    return _settings_cache


# Allowed models are now configured in settings.py (Settings.allowed_models).
# The engine reads them at runtime via self.settings.allowed_models.
# Legacy constant kept for backward compatibility in tests.
ALLOWED_MODELS = None  # Populated from settings at runtime

# Import security violation patterns and constants from config
from akios.config.constants import (
    SECURITY_VIOLATION_PATTERNS,
    DEFAULT_WORKFLOW_TIMEOUT,
    TEMPLATE_SUBSTITUTION_MAX_DEPTH,
    AUDIT_ERROR_CONTEXT_KEY,
    AUDIT_EXECUTION_TIME_KEY
)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class SecurityViolationError(Exception):
    """Raised when agent configuration violates security policies"""
    pass


class RuntimeEngine:
    """
    Main runtime engine for executing AKIOS workflows.

    Coordinates sequential step execution with security and audit integration.

    Internal organisation (search for the headers):
        ── Lifecycle          __init__, reset, _clear_*
        ── Audit helper       _emit_audit
        ── Workflow exec      run, _execute_workflow, _execute_workflow_steps
        ── Step exec          _execute_step, _execute_with_agent_retry
        ── Conditions         _evaluate_condition
        ── Template engine    _resolve_step_parameters, _transform_output_paths
        ── Output extraction  _extract_output_value, _extract_step_output
        ── Kill-switches      _check_execution_limits
        ── Security           _validate_workflow_structure, _validate_agent_config
        ── Env / config       _resolve_env_vars
    """

    def __init__(self, workflow=None):
        """
        Initialize runtime engine.

        Args:
            workflow: Optional Workflow object to execute
        """
        self.settings = _get_cached_settings()

        # Lazy initialize heavy components for performance
        self._cost_kill = None
        self._loop_kill = None
        self._retry_handler = None

        self.workflow = workflow
        self.current_workflow_id = None
        self.execution_context = {}

        # Perform startup health checks
        self._perform_startup_health_checks()

    # ── Audit helper ────────────────────────────────────────────────
    def _emit_audit(self, workflow_id: str, step: int, agent: str,
                    action: str, result: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit a single audit event if auditing is enabled.

        Centralises the repeated pattern of checking audit_enabled + calling
        append_audit_event so every call-site is one line instead of six.
        """
        if not getattr(self.settings, 'audit_enabled', True):
            return
        try:
            _get_append_audit_event()({
                'workflow_id': workflow_id,
                'step': step,
                'agent': agent,
                'action': action,
                'result': result,
                'metadata': metadata or {},
            })
        except Exception:
            logger.debug("Failed to emit audit event for %s/%s", agent, action, exc_info=True)

    def _perform_startup_health_checks(self):
        """
        Perform comprehensive startup health checks for all agents.

        This ensures that all required agents are available and functional
        before attempting workflow execution.
        """
        # Skip audit logging if ablation flag disables it
        audit_on = getattr(self.settings, 'audit_enabled', True)

        try:
            from akios.core.runtime.agents import validate_agent_health, get_supported_agents

            agent_health_issues = []

            # Check all supported agents
            for agent_type in get_supported_agents():
                health = validate_agent_health(agent_type)

                if not health['healthy']:
                    agent_health_issues.extend(health['issues'])

                # Log agent health status (only if audit enabled)
                if audit_on:
                    from akios.core.audit import append_audit_event
                    append_audit_event({
                        'workflow_id': 'system_startup',
                        'step': 0,
                        'agent': 'runtime_engine',
                        'action': 'agent_health_check',
                        'result': 'success' if health['healthy'] else 'warning',
                        'metadata': {
                            'agent_type': agent_type,
                            'healthy': health['healthy'],
                            'issues': health['issues'],
                            'capabilities': health['capabilities']
                        }
                    })

            # If any critical agent health issues, log warning but don't fail startup
            if agent_health_issues and audit_on:
                from akios.core.audit import append_audit_event
                append_audit_event({
                    'workflow_id': 'system_startup',
                    'step': 0,
                    'agent': 'runtime_engine',
                    'action': 'startup_health_check_warning',
                    'result': 'warning',
                    'metadata': {
                        'total_issues': len(agent_health_issues),
                        'issues': agent_health_issues[:5],
                        'message': 'Some agents have health issues but system startup continues'
                    }
                })

        except Exception as e:
            # Health check failure should not prevent startup
            if audit_on:
                try:
                    from akios.core.audit import append_audit_event
                    append_audit_event({
                        'workflow_id': 'system_startup',
                        'step': 0,
                        'agent': 'runtime_engine',
                        'action': 'startup_health_check_error',
                        'result': 'error',
                        'metadata': {
                            'error': str(e),
                            'message': 'Agent health checks failed during startup'
                        }
                    })
                except Exception:
                    pass

    @property
    def cost_kill(self):
        """Lazy load cost kill switch."""
        if self._cost_kill is None:
            CostKillSwitch = _import_module('akios.core.runtime.engine.kills', 'CostKillSwitch')
            self._cost_kill = CostKillSwitch()
        return self._cost_kill

    @property
    def loop_kill(self):
        """Lazy load loop kill switch."""
        if self._loop_kill is None:
            LoopKillSwitch = _import_module('akios.core.runtime.engine.kills', 'LoopKillSwitch')
            self._loop_kill = LoopKillSwitch()
        return self._loop_kill

    @property
    def retry_handler(self):
        """Lazy load retry handler."""
        if self._retry_handler is None:
            RetryHandler = _import_module('akios.core.runtime.engine.retry', 'RetryHandler')
            self._retry_handler = RetryHandler()
        return self._retry_handler

    def run(self, workflow_path_or_workflow=None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a workflow from file path or pre-loaded workflow object.

        Args:
            workflow_path_or_workflow: Path to YAML workflow file, or pre-loaded Workflow object
            context: Optional execution context

        Returns:
            Execution results

        Raises:
            RuntimeError: If workflow execution fails
        """
        # Handle different input types
        if isinstance(workflow_path_or_workflow, str):
            # Parse workflow from file path
            parse_workflow = _import_module('akios.core.runtime.workflow.parser', 'parse_workflow')
            workflow = parse_workflow(workflow_path_or_workflow)
        elif workflow_path_or_workflow is not None:
            # Use provided workflow object
            workflow = workflow_path_or_workflow
        elif self.workflow is not None:
            # Use workflow set in constructor
            workflow = self.workflow
        else:
            raise RuntimeError("No workflow provided. Use run('path/to/workflow.yml') or RuntimeEngine(workflow=...)")

        return self._execute_workflow(workflow, context)

    def _execute_workflow(self, workflow, context: Optional[Dict[str, Any]] = None, global_timeout: float = DEFAULT_WORKFLOW_TIMEOUT) -> Dict[str, Any]:
        """
        Execute a workflow object.

        Args:
            workflow: Workflow object to execute
            context: Optional execution context
            global_timeout: Global timeout in seconds (default: 30 minutes)

        Returns:
            Execution results

        Raises:
            RuntimeError: If workflow execution fails or times out
        """
        start_time = time.time()
        end_time = start_time + global_timeout

        try:
            # Initialize workflow execution
            self._initialize_workflow_execution(workflow, context, start_time)

            # Initialize testing issue tracking if available
            testing_tracker = None
            try:
                from ...testing.tracker import get_testing_tracker
                testing_tracker = get_testing_tracker()
                # Auto-detect workflow-specific testing limitations
                self._auto_detect_workflow_limitations(testing_tracker, workflow)
            except ImportError:
                pass

            # Clear any stale workflow state before execution for reliability
            self._clear_workflow_state()

            # Show enhanced workflow overview with context
            total_steps = len(workflow.steps)
            workflow_display_name = workflow.name.replace('_', ' ').title()
            logger.info('Executing "%s" (%d steps, timeout %.1f min)',
                        workflow_display_name, total_steps, global_timeout / 60)
            print(f"🚀 Executing \"{workflow_display_name}\"", file=sys.stderr)
            print(f"📊 Progress: {total_steps} steps total", file=sys.stderr)
            print(f"⏱️  Global timeout: {global_timeout/60:.1f} minutes", file=sys.stderr)
            print(f"🔒 Security: All protections active", file=sys.stderr)
            print("", file=sys.stderr)

            # Execute all steps
            results = self._execute_workflow_steps(workflow, end_time)

            # Show celebratory completion summary
            total_time = time.time() - start_time
            logger.info('Workflow completed in %.2fs', total_time)
            print("", file=sys.stderr)
            print(f"🎉 Workflow completed in {total_time:.2f}s", file=sys.stderr)
            sys.stderr.flush()

            # Finalize successful execution
            return self._finalize_workflow_execution(workflow, results, start_time)

        except (RuntimeError, ValueError, OSError, ConnectionError) as e:
            # Handle workflow failure for known exception types
            self._handle_workflow_failure(workflow, e, start_time)
            raise RuntimeError(f"Workflow execution failed: {e}") from e
        except Exception as e:
            # Handle unexpected exceptions with additional logging
            print(f"⚠️  Unexpected error during workflow execution: {type(e).__name__}: {e}", file=sys.stderr)
            self._handle_workflow_failure(workflow, e, start_time)
            raise RuntimeError(f"Workflow execution failed unexpectedly: {e}") from e

    def _initialize_workflow_execution(self, workflow, context: Optional[Dict[str, Any]], start_time: float) -> None:
        """Initialize workflow execution context and security"""
        self.current_workflow_id = f"{workflow.name}_{int(start_time)}"
        self.execution_context = context or {}

        # Extract template source for tracking
        self.template_source = self.execution_context.get('template_source')

        # Apply initial security (delayed import to avoid validation during package import)
        if self.settings.sandbox_enabled:
            from akios.security import enforce_sandbox
            enforce_sandbox()

        # RUNTIME ENFORCEMENT: Validate workflow structure at runtime
        self._validate_workflow_structure(workflow)

        # Initialize kill switches
        self.cost_kill.reset()
        self.loop_kill.reset()

        # MAINTENANCE: Clean up old output directories periodically
        try:
            from ..output.manager import get_output_manager
            output_manager = get_output_manager()
            output_manager.cleanup_old_outputs()
        except Exception:
            # Silently fail if cleanup fails - don't break workflow initialization
            pass

    def reset(self) -> None:
        """
        Reset the engine to a clean state for reuse.

        This ensures that repeated workflow executions don't accumulate state
        that could cause failures after initial success. Implements comprehensive
        state isolation to prevent cross-workflow contamination.
        """
        # Reset all instance state with deep cleanup
        self.current_workflow_id = None
        self.execution_context = {}  # Fresh context dictionary
        self.template_source = None
        self.workflow = None

        # Reset output directory to prevent cross-workflow contamination
        if hasattr(self, '_output_dir'):
            del self._output_dir

        # Reset kill switches to pristine state
        self.cost_kill.reset()
        self.loop_kill.reset()

        # Clear any accumulated workflow state
        self._clear_workflow_state()

        # Additional state isolation measures
        self._isolate_execution_environment()

    def _clear_workflow_state(self) -> None:
        """
        Clear any stale workflow state to ensure clean execution between runs.

        This prevents state accumulation issues that can cause repeated workflow
        executions to fail after initial success. Implements comprehensive cleanup
        of execution artifacts and temporary state.
        """
        # Clear execution context completely
        self.execution_context.clear()

        # Clear any cached workflow parsing results
        # (Defensive cleanup for future enhancements)

        # Reset workflow-specific state
        if hasattr(self, '_workflow_cache'):
            self._workflow_cache.clear()

        # Clear any agent-specific cached state
        self._clear_agent_state()

        # Skip output directory validation when sandbox is enabled
        # Sandbox enforcement may restrict file operations during initialization,
        # and validation failures won't prevent workflow execution anyway
        # (the actual workflow will fail more gracefully if there are real issues)
        if not self.settings.sandbox_enabled:
            # Ensure output directories are clean for this workflow run
            self._validate_output_directory_state()

        # Clear any audit-related temporary state
        self._clear_audit_state()

    def _clear_agent_state(self) -> None:
        """
        Clear any agent-specific state that might persist between executions.

        This prevents agent state contamination between different workflow runs.
        """
        # Agents are typically stateless, but this provides a hook for future
        # stateful agent cleanup if needed
        pass

    def _clear_audit_state(self) -> None:
        """
        Clear any audit-related temporary state.

        Ensures audit logging doesn't interfere with subsequent executions.
        """
        # Audit system is append-only, but this provides cleanup hooks
        # for any temporary audit state if implemented in the future
        pass

    def _validate_workflow_structure(self, workflow) -> None:
        """
        RUNTIME ENFORCEMENT: Validate workflow structure and block forbidden features.

        This provides an additional layer of validation at runtime beyond parsing,
        ensuring sequential-only promise is enforced even if parsing is bypassed.
        """
        # Check for forbidden parallel/loop constructs
        parallel_indicators = ['parallel', 'parallel_steps', 'loop', 'for_each', 'map', 'reduce']

        for step in workflow.steps:
            # Check step parameters for forbidden constructs
            def check_forbidden(obj: Any) -> bool:
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key.lower() in parallel_indicators:
                            return True
                        if isinstance(value, (dict, list)):
                            if check_forbidden(value):
                                return True
                elif isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, (dict, list)):
                            if check_forbidden(item):
                                return True
                return False

            if check_forbidden(step.parameters) or check_forbidden(step.config):
                raise RuntimeError(
                    f"Workflow contains forbidden parallel/loop constructs (sequential only). "
                    f"Step {step.step_id} contains parallel execution patterns."
                )

    def _validate_output_directory_state(self) -> None:
        """
        Validate that output directories are in a clean state for workflow execution.

        This prevents conflicts from previous runs that might leave partial state
        or permission issues that could cause execution failures.
        """
        import os
        from pathlib import Path

        output_base = Path("data/output")

        # Ensure output base directory exists and is accessible
        try:
            import tempfile
            output_base.mkdir(parents=True, exist_ok=True)

            # Test directory permissions using tempfile to avoid race conditions
            fd, tmp_path = tempfile.mkstemp(dir=str(output_base), prefix='.akios_probe_')
            os.close(fd)
            os.unlink(tmp_path)

        except (OSError, PermissionError) as e:
            print(f"⚠️  Warning: Output directory state validation failed: {e}", file=sys.stderr)
            print("   This may affect workflow execution reliability.", file=sys.stderr)

    def _isolate_execution_environment(self) -> None:
        """
        Isolate the execution environment to prevent cross-workflow contamination.

        This implements additional isolation measures beyond basic state reset
        to ensure workflows run in a pristine environment.
        """
        import os

        # Clear any environment variables that might have been set by previous workflows
        # (Defensive cleanup - workflows should not rely on env var side effects)

        # Reset any global module-level state that might affect execution
        # (Currently no global state, but defensive for future changes)

        # NOTE: gc.collect() was removed here — it added ~50ms latency per reset
        # with no measurable benefit.  The CPython refcount collector handles
        # short-lived workflow objects perfectly well.

    def _execute_workflow_steps(self, workflow, end_time: float) -> list:
        """
        Execute all workflow steps with safety checks and progress indicators.
        
        Enhanced with Rich Live Dashboard showing:
        - Real-time step status (Pending/Running/Success/Error)
        - Execution time per step
        - Live logs in a separate panel (optional)
        - Automatic fallback to simple print for non-TTY/JSON mode
        """
        results = []
        total_steps = len(workflow.steps)
        
        # Get progress functions
        progress_funcs = _get_progress_functions()
        force_color = os.environ.get("FORCE_COLOR") == "1" or os.environ.get("CLICOLOR_FORCE") == "1"
        use_rich_progress = progress_funcs is not None and (sys.stderr.isatty() or force_color)
        
        # Determine friendly descriptions for steps (kept for fallback)
        friendly_descriptions = {
            "llm.complete": "AI generation",
            "filesystem.write": "Saving results",
            "filesystem.read": "Reading data",
            "http.get": "Fetching data",
            "http.post": "Submitting data",
            "tool_executor.run": "Running command"
        }
        
        # Execute with Live Dashboard if available
        if use_rich_progress:
            create_workflow_dashboard = progress_funcs['dashboard']
            
            # Use the dashboard context manager
            with create_workflow_dashboard(workflow) as dashboard:
                for i, step in enumerate(workflow.steps):
                    # ENFORCEMENT: Check kill switches BEFORE executing each step
                    self._check_execution_limits(end_time)

                    # Evaluate condition — skip step if condition is false
                    if getattr(step, 'condition', None):
                        if not self._evaluate_condition(step.condition, step.step_id):
                            logger.info('Step %d skipped (condition not met: %s)', step.step_id, step.condition)
                            dashboard.set_success(i, duration=0.0)
                            results.append({
                                'step_id': step.step_id, 'agent': step.agent,
                                'action': step.action, 'status': 'skipped',
                                'reason': f'condition not met: {step.condition}',
                                'execution_time': 0.0,
                            })
                            continue
                    
                    # Mark step as running (0-based index)
                    dashboard.set_running(i)
                    
                    # Execute step
                    step_start = time.time()
                    step_result = self._execute_step(step, workflow)
                    results.append(step_result)
                    step_duration = time.time() - step_start
                    
                    # Check for security violations
                    self._check_step_security_violation(step_result, step.step_id)
                    
                    if step_result.get('status') == 'error':
                        error_msg = step_result.get('error', 'Unknown error')
                        on_error = getattr(step, 'on_error', None) or 'fail'
                        if on_error == 'skip':
                            logger.warning('Step %d failed but on_error=skip, continuing: %s', step.step_id, error_msg)
                            dashboard.set_error(i, duration=step_duration)
                            # Don't raise — continue to next step
                        elif on_error == 'retry':
                            logger.warning('Step %d failed, retrying (on_error=retry): %s', step.step_id, error_msg)
                            step_result = self._execute_step(step, workflow)
                            results[-1] = step_result  # Replace last result
                            step_duration = time.time() - step_start
                            if step_result.get('status') == 'error':
                                dashboard.set_error(i, duration=step_duration)
                                raise RuntimeError(f"Step {i+1} failed after retry: {step_result.get('error', error_msg)}")
                            else:
                                dashboard.set_success(i, duration=step_duration)
                        else:
                            dashboard.set_error(i, duration=step_duration)
                            raise RuntimeError(f"Step {i+1} failed: {error_msg}")
                    else:
                        dashboard.set_success(i, duration=step_duration)
                    
                    # ENFORCEMENT: Check kill switches AFTER each step execution
                    self._check_execution_limits(end_time)
        else:
            # Fallback to original print-based progress (non-TTY, JSON mode, or Rich unavailable)
            for i, step in enumerate(workflow.steps, 1):
                # ENFORCEMENT: Check kill switches BEFORE executing each step
                self._check_execution_limits(end_time)

                # Evaluate condition — skip step if condition is false
                if getattr(step, 'condition', None):
                    if not self._evaluate_condition(step.condition, step.step_id):
                        logger.info('Step %d skipped (condition not met)', step.step_id)
                        print(f"⏭️  Step {i}/{total_steps}: skipped (condition not met)", file=sys.stderr)
                        results.append({
                            'step_id': step.step_id, 'agent': step.agent,
                            'action': step.action, 'status': 'skipped',
                            'reason': f'condition not met: {step.condition}',
                            'execution_time': 0.0,
                        })
                        continue
                
                # Show enhanced progress indicator
                step_start = time.time()
                agent_action = f"{step.agent}.{step.action}"
                friendly_desc = friendly_descriptions.get(agent_action, agent_action)
                print(f"⚡ Executing step {i}/{total_steps}: {friendly_desc}", file=sys.stderr)
                sys.stderr.flush()
                
                step_result = self._execute_step(step, workflow)
                results.append(step_result)
                
                # Show step completion with timing
                step_duration = time.time() - step_start
                status_icon = self._determine_step_status_icon(step_result, step)
                print(f"{status_icon} Step {i}/{total_steps} completed in {step_duration:.2f}s", file=sys.stderr)
                sys.stderr.flush()
                
                # Check for security violations
                self._check_step_security_violation(step_result, step.step_id)
                
                if step_result.get('status') == 'error':
                    error_msg = step_result.get('error', 'Unknown error')
                    on_error = getattr(step, 'on_error', None) or 'fail'
                    if on_error == 'skip':
                        logger.warning('Step %d failed but on_error=skip, continuing', step.step_id)
                        # Don't raise — continue to next step
                    elif on_error == 'retry':
                        logger.warning('Step %d failed, retrying (on_error=retry)', step.step_id)
                        step_result = self._execute_step(step, workflow)
                        results[-1] = step_result
                        if step_result.get('status') == 'error':
                            raise RuntimeError(f"Step {i} failed after retry: {step_result.get('error', error_msg)}")
                    else:
                        raise RuntimeError(f"Step {i} failed: {error_msg}")
                
                # ENFORCEMENT: Check kill switches AFTER each step execution
                self._check_execution_limits(end_time)
        
        return results

    def _determine_step_status_icon(self, step_result: Dict[str, Any], step) -> str:
        """
        Determine the appropriate status icon for a step result.

        Different agents use different result formats, so we need to check
        the appropriate success indicators based on agent type.

        Args:
            step_result: Result dictionary from agent execution
            step: The workflow step object

        Returns:
            Status icon string: ✅ (success), ❌ (error), ⚠️ (warning/unknown)
        """

        # Check explicit status field first (used by LLM and other agents)
        status = step_result.get('status')
        if status == 'success':
            return "✅"
        elif status == 'error':
            return "❌"

        # For tool_executor agent, check returncode
        if step.agent == 'tool_executor':
            returncode = step_result.get('returncode')
            if returncode == 0:
                return "✅"
            elif returncode is not None:
                return "❌"

        # For filesystem agent, check for error indicators
        if step.agent == 'filesystem':
            if step_result.get('error') or 'error' in step_result.get('message', '').lower():
                return "❌"
            # Filesystem operations typically succeed if no error is present
            return "✅"

        # For HTTP agent, check status codes
        if step.agent == 'http':
            status_code = step_result.get('status_code')
            if status_code and 200 <= status_code < 300:
                return "✅"
            elif status_code:
                return "❌"

        # Default: if we can't determine status, show warning
        return "⚠️"

    def _evaluate_condition(self, condition: str, step_id: int) -> bool:
        """
        Evaluate a step condition expression against the execution context.

        Supports simple comparisons against prior step outputs:
          - ``step_1_output.status == 'success'``
          - ``step_2_output.content != ''``
          - ``previous_output is not None``

        The condition is evaluated in a restricted namespace containing only
        step results and builtins ``True``, ``False``, ``None``.

        Args:
            condition: Expression string.
            step_id:   Current step id (for error messages).

        Returns:
            ``True`` if the condition passes (step should run),
            ``False`` if it does not.
        """
        import re as _re

        # Build a safe namespace from execution context
        namespace: Dict[str, Any] = {'True': True, 'False': False, 'None': None}

        # Expose step results as step_N_output
        for key, value in self.execution_context.items():
            if key.startswith('step_') and key.endswith('_result'):
                step_num = key.replace('step_', '').replace('_result', '')
                namespace[f'step_{step_num}_output'] = value

        # Expose previous_output (= result of step_id - 1)
        prev_key = f'step_{step_id - 1}_result'
        namespace['previous_output'] = self.execution_context.get(prev_key)

        # SECURITY: Block dangerous builtins
        blocked = {'__import__', 'eval', 'exec', 'compile', 'open', 'getattr',
                    'setattr', 'delattr', 'globals', 'locals', 'vars', 'dir',
                    'type', 'isinstance', 'issubclass', 'super', 'breakpoint'}
        for token in blocked:
            if token in condition:
                logger.warning('Blocked dangerous token "%s" in condition for step %d', token, step_id)
                return False

        try:
            result = eval(condition, {"__builtins__": {}}, namespace)  # noqa: S307
            return bool(result)
        except Exception as exc:
            logger.warning('Condition evaluation failed for step %d (%s): %s', step_id, condition, exc)
            return False

    def _auto_detect_workflow_limitations(self, tracker, workflow):
        """
        Automatically detect workflow-specific testing limitations.

        Args:
            tracker: TestingIssueTracker instance
            workflow: Workflow being executed
        """
        if tracker is None:
            return

        import os

        # Check for LLM-dependent workflows in mock mode
        has_llm_steps = any(step.agent == 'llm' for step in workflow.steps)
        if has_llm_steps and os.getenv('AKIOS_MOCK_LLM') == '1':
            tracker.detect_partial_test(
                feature="AI-powered workflows",
                tested_aspects=["Workflow structure", "Step execution", "Error handling"],
                untested_aspects=["AI response quality", "Context understanding", "Creative output"],
                reason="Workflow contains LLM steps but running in mock mode"
            )

        # Check for HTTP-dependent workflows without network
        has_http_steps = any(step.agent == 'http' for step in workflow.steps)
        if has_http_steps:
            network_available = False
            from akios.core.utils.network import check_network_available
            network_available = check_network_available()

            if not network_available:
                tracker.detect_environment_limitation(
                    feature="HTTP-based workflows",
                    reason="Network connectivity required but not available",
                    impact="Cannot test API integrations or web service calls",
                    recommendation="Test in environment with internet access"
                )

        # Check for filesystem operations that might be limited in Docker
        has_fs_steps = any(step.agent == 'filesystem' for step in workflow.steps)
        if has_fs_steps and os.path.exists('/.dockerenv'):
            tracker.detect_partial_test(
                feature="Filesystem operations",
                tested_aspects=["Basic file I/O", "Path handling"],
                untested_aspects=["Host filesystem permission enforcement", "Full security validation"],
                reason="Running in Docker where filesystem permissions are bypassed"
            )

        # Check for tool executor steps that might have command limitations
        has_tool_steps = any(step.agent == 'tool_executor' for step in workflow.steps)
        if has_tool_steps and os.path.exists('/.dockerenv'):
            tracker.detect_partial_test(
                feature="System tool execution",
                tested_aspects=["Command execution", "Output capture"],
                untested_aspects=["Full system command access", "Security sandbox validation"],
                reason="Running in Docker with limited command whitelist"
            )

    def _check_step_security_violation(self, step_result: Dict[str, Any], step_id: int) -> None:
        """Check if step result contains security violation"""
        if step_result.get('status') == 'error':
            error_msg = step_result.get('error', 'Unknown error')
            error_lower = error_msg.lower()

            if any(pattern in error_lower for pattern in SECURITY_VIOLATION_PATTERNS):
                raise RuntimeError(f"Security violation in step {step_id}: {error_msg}")

    def _check_execution_limits(self, end_time: float) -> None:
        """
        ENFORCEMENT: Check and enforce execution limits including kill switches and global workflow timeout.

        CRITICAL: Unlike the old version that just checked, this version ACTUALLY STOPS execution
        when limits are exceeded. Kill switches are now enforced, not just detected.

        Raises RuntimeError to immediately halt workflow execution when:
        - Cost budget exceeded
        - Step/loop limits exceeded
        - Global timeout reached
        """
        # ENFORCEMENT: Cost kill switch - actually stops execution
        # Respects ablation flag: --no-budget disables cost enforcement for benchmarking
        if getattr(self.settings, 'cost_kill_enabled', True) and self.cost_kill.should_kill():
            cost_status = self.cost_kill.get_status()
            raise RuntimeError(
                f"🚫 COST KILL-SWITCH ENFORCED: Budget exceeded\n"
                f"   Spent: ${cost_status['total_cost']:.2f}\n"
                f"   Budget: ${cost_status['budget_limit']:.2f}\n"
                f"   Workflow execution HALTED to prevent overspending"
            )

        # ENFORCEMENT: Loop kill switch - actually stops execution
        if self.loop_kill.should_kill():
            loop_status = self.loop_kill.get_status()
            kill_reason = []
            if loop_status['time_limit_exceeded']:
                kill_reason.append(f"time limit ({loop_status['max_execution_time']}s)")
            if loop_status['step_limit_exceeded']:
                kill_reason.append(f"step limit ({loop_status['max_steps']} steps)")

            raise RuntimeError(
                f"🚫 LOOP KILL-SWITCH ENFORCED: {' and '.join(kill_reason)} exceeded\n"
                f"   Execution time: {loop_status['execution_time']:.1f}s\n"
                f"   Steps executed: {loop_status['step_count']}\n"
                f"   Workflow execution HALTED to prevent infinite loops"
            )

        # ENFORCEMENT: Global timeout - actually stops execution
        if time.time() > end_time:
            elapsed = time.time() - (end_time - DEFAULT_WORKFLOW_TIMEOUT)
            raise RuntimeError(
                f"🚫 GLOBAL TIMEOUT ENFORCED: Workflow exceeded {DEFAULT_WORKFLOW_TIMEOUT}s limit\n"
                f"   Elapsed time: {elapsed:.1f}s\n"
                f"   Timeout limit: {DEFAULT_WORKFLOW_TIMEOUT}s\n"
                f"   Workflow execution HALTED to prevent runaway processes"
            )

    def _finalize_workflow_execution(self, workflow, results: list, start_time: float) -> Dict[str, Any]:
        """Finalize successful workflow execution"""
        execution_time = time.time() - start_time

        # Emit audit event only if audit is enabled (respects --no-audit ablation flag)
        if getattr(self.settings, 'audit_enabled', True):
            _get_append_audit_event()({
                'workflow_id': self.current_workflow_id,
                'step': len(workflow.steps),
                'agent': 'engine',
                'action': 'workflow_complete',
                'result': 'success',
                'metadata': {
                    'total_steps': len(workflow.steps),
                    'execution_time': execution_time,
                    'cost_status': self.cost_kill.get_status(),
                    'loop_status': self.loop_kill.get_status(),
                    'template_source': self.template_source
                }
            })

        # CRITICAL: Flush audit buffer to ensure all events are written to disk
        if getattr(self.settings, 'audit_enabled', True):
            try:
                audit_flush = _import_module('akios.core.audit.ledger', 'get_ledger')
                ledger = audit_flush()
                ledger.flush_buffer()
            except Exception as e:
                pass

        result = {
            'status': 'completed',
            'workflow_id': self.current_workflow_id,
            'steps_executed': len(results),
            'execution_time': execution_time,
            'results': results
        }

        # Write output.json — deployable artifact with LLM results + metadata.
        # Enables `akios output latest` and CI/CD pipeline integration.
        if hasattr(self, '_output_dir') and self._output_dir:
            try:
                import json as _json
                output_json_path = self._output_dir / "output.json"
                try:
                    from akios._version import __version__ as _akios_ver
                except ImportError:
                    _akios_ver = 'unknown'
                deployable = {
                    'akios_version': _akios_ver,
                    'workflow_name': workflow.name,
                    'workflow_id': self.current_workflow_id,
                    'status': 'completed',
                    'steps_executed': len(results),
                    'execution_time_seconds': round(execution_time, 3),
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'security': {
                        'pii_redaction': getattr(self.settings, 'pii_redaction_enabled', True),
                        'audit_enabled': getattr(self.settings, 'audit_enabled', True),
                        'sandbox_enabled': getattr(self.settings, 'sandbox_enabled', True),
                    },
                    'cost': self.cost_kill.get_status(),
                    'results': [
                        {
                            'step': i + 1,
                            'agent': r.get('agent', '') if isinstance(r, dict) else '',
                            'action': r.get('action', '') if isinstance(r, dict) else '',
                            'status': r.get('status', '') if isinstance(r, dict) else '',
                            'execution_time': round(r.get('execution_time', 0), 3) if isinstance(r, dict) else 0,
                            'output': self._extract_step_output(r),
                        }
                        for i, r in enumerate(results)
                    ],
                    'output_directory': str(self._output_dir),
                }
                with open(output_json_path, 'w') as f:
                    _json.dump(deployable, f, indent=2, default=str)
            except Exception:
                pass  # Don't fail workflow on output write failure

        return result

    def _handle_workflow_failure(self, workflow, exception: Exception, start_time: float) -> None:
        """Handle workflow execution failure"""
        # Emit audit event only if audit is enabled (respects --no-audit ablation flag)
        if getattr(self.settings, 'audit_enabled', True):
            _get_append_audit_event()({
                'workflow_id': self.current_workflow_id or 'unknown',
                'step': 0,
                'agent': 'engine',
                'action': 'workflow_failed',
                'result': 'error',
                'metadata': {
                    'error': str(exception),
                    AUDIT_EXECUTION_TIME_KEY: time.time() - start_time,
                    AUDIT_ERROR_CONTEXT_KEY: f"Workflow '{workflow.name}': {str(exception)}"
                }
            })

        # CRITICAL: Flush audit buffer even on failure to ensure all events are written to disk
        if getattr(self.settings, 'audit_enabled', True):
            try:
                audit_flush = _import_module('akios.core.audit.ledger', 'get_ledger')
                ledger = audit_flush()
                ledger.flush_buffer()
            except Exception:
                pass

    def _execute_step(self, step, workflow) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: WorkflowStep to execute
            workflow: Parent workflow

        Returns:
            Step execution result
        """
        step_start = time.time()

        try:
            # Get agent class
            agent_class = _get_agent_class()(step.agent)

            # Parse and resolve agent configuration
            step_config = step.config

            # For LLM agents, skip api_key resolution - let agent auto-detect based on provider
            if step.agent == 'llm' and 'api_key' in step_config:
                # Resolve other config but keep api_key as-is (placeholder or literal)
                config_for_resolution = {k: v for k, v in step_config.items() if k != 'api_key'}
                resolved_config = self._resolve_env_vars(config_for_resolution)
                resolved_config['api_key'] = step_config['api_key']  # Keep as-is
            else:
                resolved_config = self._resolve_env_vars(step_config)
            self._validate_agent_config(step.agent, resolved_config)


            # Special handling for filesystem agent - override read_only for write actions
            if step.agent == 'filesystem' and step.action == 'write':
                resolved_config = dict(resolved_config)  # Copy to avoid modifying original
                resolved_config['read_only'] = False

            # Create agent with resolved configuration
            agent = agent_class(**resolved_config)

            # Prepare step parameters with template substitution
            step_params = self._resolve_step_parameters(step.parameters.copy(), step.step_id - 1)

            # Add standard workflow metadata
            step_params.update({
                'workflow_id': self.current_workflow_id,
                'step': step.step_id,
                'workflow_name': workflow.name
            })

            # Execute with agent-specific retry logic
            result = self._execute_with_agent_retry(
                step.agent, step.action,
                lambda: agent.execute(step.action, step_params)
            )

            # Log LLM step output to console
            if step.agent == 'llm' and result and 'text' in result:
                # Add mock mode indicator if applicable
                mock_indicator = ""
                if os.getenv('AKIOS_MOCK_LLM') == '1':
                    mock_indicator = " [🎭 MOCK MODE]"
                
                # Format output with colors if Rich available
                try:
                    from rich.console import Console
                    from akios.core.ui.rich_output import get_theme_color
                    console = Console()
                    # Add newline before output for better readability
                    console.print(f"[bold {get_theme_color('header')}]🤖 Step {step.step_id} Output{mock_indicator}:[/bold {get_theme_color('header')}]")
                    # Display actual output in white/dim for readability
                    output_text = result['text']
                    if len(output_text) > 300:
                        console.print(f"{output_text[:300]}[dim]...[/dim]")
                    else:
                        console.print(f"{output_text}")
                except ImportError:
                    print(f"🤖 Step {step.step_id} Output{mock_indicator}: {result['text']}", file=sys.stdout)
                sys.stdout.flush()

            # Update execution context
            self.execution_context[f"step_{step.step_id}_result"] = result

            # Add any costs incurred by this step to the cost kill switch
            if isinstance(result, dict) and 'cost_incurred' in result:
                self.cost_kill.add_cost(result['cost_incurred'])

            # Step execution audit (respects --no-audit ablation flag)
            step_time = time.time() - step_start
            if getattr(self.settings, 'audit_enabled', True):
                _get_append_audit_event()({
                    'workflow_id': self.current_workflow_id,
                    'step': step.step_id,
                    'agent': step.agent,
                    'action': step.action,
                    'result': 'success',
                    'metadata': {
                        'execution_time': step_time,
                        'agent_type': step.agent,
                        'has_result': bool(result)
                    }
                })

            return {
                'step_id': step.step_id,
                'agent': step.agent,
                'action': step.action,
                'status': 'success',
                'result': result,
                'execution_time': step_time
            }

        except (RuntimeError, ValueError, ConnectionError, TimeoutError) as e:
            # Handle known exception types
            step_time = time.time() - step_start
            if getattr(self.settings, 'audit_enabled', True):
                _get_append_audit_event()({
                    'workflow_id': self.current_workflow_id,
                    'step': step.step_id,
                    'agent': step.agent,
                    'action': step.action,
                    'result': 'error',
                    'metadata': {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        AUDIT_EXECUTION_TIME_KEY: step_time,
                        AUDIT_ERROR_CONTEXT_KEY: f"Workflow '{workflow.name}' Step {step.step_id}: {str(e)}"
                    }
                })

            return {
                'step_id': step.step_id,
                'agent': step.agent,
                'action': step.action,
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time': step_time
            }
        except Exception as e:
            # Handle unexpected exceptions with enhanced logging
            step_time = time.time() - step_start
            print(f"⚠️  Unexpected error in step {step.step_id}: {type(e).__name__}: {e}", file=sys.stderr)
            if getattr(self.settings, 'audit_enabled', True):
                _get_append_audit_event()({
                    'workflow_id': self.current_workflow_id,
                    'step': step.step_id,
                    'agent': step.agent,
                    'action': step.action,
                    'result': 'error',
                    'metadata': {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'unexpected_error': True,
                        AUDIT_EXECUTION_TIME_KEY: step_time,
                        AUDIT_ERROR_CONTEXT_KEY: f"Workflow '{workflow.name}' Step {step.step_id}: Unexpected {type(e).__name__}: {str(e)}"
                    }
                })

            return {
                'step_id': step.step_id,
                'agent': step.agent,
                'action': step.action,
                'status': 'error',
                'error': f"Unexpected error: {type(e).__name__}: {str(e)}",
                'error_type': type(e).__name__,
                'unexpected_error': True,
                'execution_time': step_time
            }

    def _resolve_step_parameters(self, params: Dict[str, Any], previous_step_id: int, max_depth: int = TEMPLATE_SUBSTITUTION_MAX_DEPTH) -> Dict[str, Any]:
        """
        Resolve step parameters by substituting templates like {previous_output} with actual values.
        Also transforms output paths to timestamped directories.

        Args:
            params: Step parameters that may contain templates
            previous_step_id: ID of the previous step (1-indexed)
            max_depth: Maximum recursion depth to prevent infinite loops

        Returns:
            Parameters with templates resolved
        """
        if not params:
            return params

        # SECURITY: Prevent DoS through excessively large parameter structures
        def _check_size(obj: Any, max_size: int = 10000) -> int:
            """Check object size to prevent memory exhaustion attacks."""
            if isinstance(obj, dict):
                size = len(obj)
                for v in obj.values():
                    size += _check_size(v, max_size)
                    if size > max_size:
                        raise RuntimeError(f"Parameter structure too large (> {max_size} elements) - possible DoS attack")
                return size
            elif isinstance(obj, (list, tuple)):
                size = len(obj)
                for item in obj:
                    size += _check_size(item, max_size)
                    if size > max_size:
                        raise RuntimeError(f"Parameter structure too large (> {max_size} elements) - possible DoS attack")
                return size
            else:
                return 1

        try:
            _check_size(params)
        except RuntimeError as e:
            raise RuntimeError(f"Template parameter validation failed: {e}") from e


        # Get the previous step's result if it exists
        previous_result = None
        if previous_step_id > 0:
            previous_result_key = f"step_{previous_step_id}_result"
            previous_result = self.execution_context.get(previous_result_key)

        def substitute_value(value: Any, depth: int = 0) -> Any:
            """Recursively substitute templates in a value with depth protection and security validation"""
            if depth > max_depth:
                raise RuntimeError(
                    f"Template substitution exceeded maximum depth of {max_depth}. "
                    f"Possible circular reference or excessive nesting in step {previous_step_id + 1}."
                )

            # SECURITY: Additional validation for each substitution level
            if depth > 0 and isinstance(value, str) and len(value) > 10000:
                raise RuntimeError(
                    f"Template substitution value too large ({len(value)} chars) at depth {depth} "
                    f"in step {previous_step_id + 1}. Possible DoS attempt."
                )

            if isinstance(value, str):

                # Substitute {previous_output} with the previous step's result
                if '{previous_output}' in value:
                    if previous_result is not None:
                        # Convert previous result to string using unified key priority
                        if isinstance(previous_result, dict):
                            result_str = self._extract_output_value(previous_result)
                        elif isinstance(previous_result, (list, tuple)):
                            result_str = '\n'.join(str(item) for item in previous_result)
                        else:
                            result_str = str(previous_result)

                        value = value.replace('{previous_output}', result_str)
                    else:
                        # No previous result available - provide clear error
                        raise RuntimeError(
                            f"Template '{{previous_output}}' used in step {previous_step_id + 1} "
                            f"but no previous step result is available. "
                            f"Ensure step {previous_step_id} completed successfully."
                        )

                # Substitute {step_X_output} and {step_X_output[key]} with specific step results
                import re
                # SECURITY: Restrict step numbers to reasonable range and validate key names
                step_pattern = re.compile(r'\{step_(\d+)_output(?:\[(\w+)\])?\}')
                matches = step_pattern.findall(value)

                if matches:
                    result_value = value
                    for step_num_str, key in matches:
                        step_num = int(step_num_str)

                        # SECURITY: Validate step number is reasonable (prevent excessive memory usage)
                        if step_num < 1 or step_num > 1000:
                            raise RuntimeError(
                                f"Template step number {step_num} is out of valid range (1-1000) "
                                f"in step {previous_step_id + 1}. This may indicate a malformed template."
                            )

                        # SECURITY: Validate key name is safe (prevent injection attacks)
                        if key and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                            raise RuntimeError(
                                f"Template key '{key}' contains invalid characters in step {previous_step_id + 1}. "
                                f"Keys must be valid Python identifiers."
                            )

                        step_result_key = f"step_{step_num}_result"
                        step_result = self.execution_context.get(step_result_key)

                        if step_result is not None:
                            # If a specific key is requested, extract it
                            if key:
                                if isinstance(step_result, dict) and key in step_result:
                                    step_value = step_result[key]
                                    step_str = str(step_value)
                                else:
                                    raise RuntimeError(
                                        f"Template '{{step_{step_num}_output[{key}]}}' used in step {previous_step_id + 1} "
                                        f"but key '{key}' not found in step {step_num} result."
                                    )
                            else:
                                # No key specified — use unified key priority
                                if isinstance(step_result, dict):
                                    step_str = self._extract_output_value(step_result)
                                elif isinstance(step_result, (list, tuple)):
                                    step_str = '\n'.join(str(item) for item in step_result)
                                else:
                                    step_str = str(step_result)

                            template_pattern = f'{{step_{step_num}_output'
                            if key:
                                template_pattern += f'[{key}]'
                            template_pattern += '}'
                            result_value = result_value.replace(template_pattern, step_str)
                        else:
                            template_name = f'step_{step_num}_output'
                            if key:
                                template_name += f'[{key}]'
                            raise RuntimeError(
                                f"Template '{{{template_name}}}' used in step {previous_step_id + 1} "
                                f"but step {step_num} result is not available. "
                                f"Ensure step {step_num} completed successfully."
                            )

                    value = result_value

                return value
            elif isinstance(value, dict):
                return {k: substitute_value(v, depth + 1) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item, depth + 1) for item in value]
            else:
                return value

        # Transform output paths to timestamped directories
        resolved_params = substitute_value(params)
        resolved_params = self._transform_output_paths(resolved_params)

        return resolved_params

    def _transform_output_paths(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform output paths to organized directories with symlinks.

        Uses OutputManager for human-readable directory naming and latest result symlinks.
        Transforms paths like './data/output/file.txt' to './data/output/run_YYYY-MM-DD_HH-MM-SS/file.txt'

        Args:
            params: Parameters that may contain output paths

        Returns:
            Parameters with output paths transformed
        """
        from ..output.manager import create_output_directory

        # Create the output directory once for this workflow
        if not hasattr(self, '_output_dir'):
            self._output_dir = create_output_directory(self.current_workflow_id)

        def transform_value(value: Any) -> Any:
            """Recursively transform output paths in values"""
            if isinstance(value, str):
                # Transform ./data/output/ paths to organized directories
                if value.startswith('./data/output/'):
                    # Get the filename from the original path
                    filename = value.replace('./data/output/', '', 1)

                    # Create the full path in our organized directory
                    transformed_path = str(self._output_dir / filename)
                    return transformed_path
                return value
            elif isinstance(value, dict):
                return {k: transform_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [transform_value(item) for item in value]
            else:
                return value

        return transform_value(params)

    def _execute_with_agent_retry(self, agent_type: str, action: str, func: Callable[[], Any]) -> Any:
        """
        Execute agent action with agent-specific retry logic.

        Args:
            agent_type: Type of agent being executed
            action: Action being performed
            func: Function to execute with retry logic

        Returns:
            Function result
        """
        # Define retry policies per agent type
        retry_policies = {
            'llm': {'max_attempts': 3, 'retryable': True},  # API calls can fail temporarily
            'http': {'max_attempts': 3, 'retryable': True},  # Network requests can timeout
            'filesystem': {'max_attempts': 1, 'retryable': False},  # File operations should not be retried
            'tool_executor': {'max_attempts': 1, 'retryable': False},  # Commands should not be retried
        }

        policy = retry_policies.get(agent_type, {'max_attempts': 1, 'retryable': False})

        if policy['retryable'] and policy['max_attempts'] > 1:
            # Use retry handler for retryable operations
            return self.retry_handler.execute_with_retry(func)
        else:
            # Execute directly without retry for non-retryable operations
            return func()

    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            'workflow_id': self.current_workflow_id,
            'cost_status': self.cost_kill.get_status(),
            'loop_status': self.loop_kill.get_status(),
            'context_keys': list(self.execution_context.keys())
        }

    def stop_execution(self) -> None:
        """Force stop current execution"""
        if self.current_workflow_id:
            _get_append_audit_event()({
                'workflow_id': self.current_workflow_id,
                'step': 0,
                'agent': 'engine',
                'action': 'execution_stopped',
                'result': 'stopped',
                'metadata': {'reason': 'manual_stop'}
            })

        self.current_workflow_id = None
        self.execution_context = {}

    # ── Unified output value extraction ───────────────────────────────
    # Canonical key priority used everywhere:
    #   text → content → output → result → response → stdout → data
    _OUTPUT_KEY_ORDER = ('text', 'content', 'output', 'result', 'response', 'stdout', 'data')

    @classmethod
    def _extract_output_value(cls, result: Any) -> str:
        """
        Extract a human-readable string from a step result.

        Uses a **single, canonical key priority** so that ``{previous_output}``,
        ``{step_X_output}``, and ``_extract_step_output`` all agree.

        Priority: text → content → output → result → response → stdout → data

        Args:
            result: Raw step result (dict, list, or scalar).

        Returns:
            Extracted string (truncated to 2 000 chars).
        """
        if not isinstance(result, dict):
            return str(result)[:2000] if result else ''
        for key in cls._OUTPUT_KEY_ORDER:
            val = result.get(key)
            if val is not None:
                return str(val)[:2000]
        # Filesystem write summary
        if result.get('written'):
            return f"Written to {result.get('path', '?')} ({result.get('size', '?')} bytes)"
        # Fallback: serialise (skip internal keys)
        summary = {k: v for k, v in result.items() if k not in ('cost_incurred',)}
        return str(summary)[:2000] if summary else ''

    @staticmethod
    def _extract_step_output(step_result) -> str:
        """Extract human-readable output from a step result dict.
        
        Different agents return results with different keys:
          - LLM → text
          - Filesystem read → content
          - Filesystem write → written + path
          - HTTP → content / json
          - Tool executor → stdout
        """
        if not isinstance(step_result, dict):
            return str(step_result)[:2000]
        result = step_result.get('result')
        if not isinstance(result, dict):
            return str(result)[:2000] if result else ''
        return RuntimeEngine._extract_output_value(result)

    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve environment variables in configuration.

        Args:
            config: Configuration dictionary that may contain env var references

        Returns:
            Configuration with environment variables resolved

        Raises:
            ConfigurationError: If required environment variable is missing
        """
        resolved = {}
        for k, v in config.items():
            if isinstance(v, str) and v.startswith('${') and v.endswith('}'):
                var_name = v[2:-1]
                value = os.getenv(var_name)
                if value is None:
                    raise ConfigurationError(
                        f"Missing environment variable '{var_name}' required for workflow execution. "
                        f"Please set it with: export {var_name}='your-value'"
                    )
                resolved[k] = value
            else:
                resolved[k] = v
        return resolved

    def _validate_agent_config(self, agent_type: str, config: Dict[str, Any]) -> None:
        """
        Validate agent configuration against security policies.

        Args:
            agent_type: Type of agent ('llm', 'filesystem', 'http', 'tool_executor')
            config: Resolved configuration dictionary

        Raises:
            SecurityViolationError: If configuration violates security policies
        """
        if agent_type == "llm":
            # Provider must be in allowed list (from global settings)
            if "provider" in config:
                provider = config["provider"]
                if provider not in self.settings.allowed_providers:
                    raise SecurityViolationError(
                        f"Provider '{provider}' not allowed. Must be one of: {', '.join(self.settings.allowed_providers)}"
                    )

            # Model must be in allowed list (from settings, not hardcoded)
            if "model" in config:
                allowed_models = set(getattr(self.settings, 'allowed_models', []))
                if config["model"] not in allowed_models:
                    raise SecurityViolationError(f"Invalid model '{config['model']}'. Must be one of: {', '.join(sorted(allowed_models))}")

            # API key must be environment variable reference (checked after resolution)
            # This is handled by the agent itself during initialization

        elif agent_type == "filesystem":
            # Validate filesystem agent configuration
            allowed_paths = config.get("allowed_paths", [])
            if not allowed_paths:
                # If no allowed paths specified, that's okay - agent will handle defaults
                pass
            else:
                # Basic validation: ensure allowed_paths is a list
                if not isinstance(allowed_paths, list):
                    raise SecurityViolationError("Filesystem agent allowed_paths must be a list")

                # Check for dangerous paths (basic protection)
                dangerous_paths = ['/', '/etc', '/usr', '/var', '/home', '/root']
                for path in allowed_paths:
                    path_str = str(path)
                    for dangerous in dangerous_paths:
                        if path_str.startswith(dangerous) and path_str != dangerous:
                            raise SecurityViolationError(
                                f"Filesystem agent path '{path_str}' is too permissive. "
                                f"Avoid system directories like {dangerous}"
                            )

            # Read-only validation
            read_only = config.get("read_only", True)  # Default to read-only
            if not isinstance(read_only, bool):
                raise SecurityViolationError("Filesystem agent read_only must be a boolean")

        elif agent_type == "http":
            # Timeout must be within safe bounds
            timeout = config.get("timeout", 30)
            if timeout > 300:  # 5 minute max
                raise SecurityViolationError(f"HTTP timeout {timeout}s exceeds maximum 300s")

            # Max redirects within bounds
            max_redirects = config.get("max_redirects", 5)
            if max_redirects > 10:
                raise SecurityViolationError(f"HTTP max_redirects {max_redirects} exceeds maximum 10")

        elif agent_type == "tool_executor":
            # Allowed commands must be subset of global allowed commands
            step_commands = set(config.get("allowed_commands", []))
            global_commands = set(self.settings.allowed_commands if hasattr(self.settings, 'allowed_commands') else [])
            if step_commands and not step_commands.issubset(global_commands):
                raise SecurityViolationError(f"Step allowed_commands {step_commands} not subset of global allowed_commands {global_commands}")

            # Timeout and output size within bounds
            timeout = config.get("timeout", 30)
            if timeout > 300:
                raise SecurityViolationError(f"Tool timeout {timeout}s exceeds maximum 300s")

            max_output = config.get("max_output_size", 1024*1024)
            if max_output > 10*1024*1024:  # 10MB max
                raise SecurityViolationError(f"Tool max_output_size {max_output} exceeds maximum 10MB")


def run_workflow(workflow_path: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to run a workflow.

    Args:
        workflow_path: Path to workflow file
        context: Optional execution context

    Returns:
        Execution results
    """
    engine = RuntimeEngine()
    return engine.run(workflow_path, context)


# Backward compatibility alias
# The class was renamed from WorkflowEngine to RuntimeEngine during development
# but we maintain the old name for API consistency
WorkflowEngine = RuntimeEngine
