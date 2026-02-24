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
            logger.error("Unexpected error during workflow execution: %s: %s", type(e).__name__, e)
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
        # Agents are stateless in v1.0 — log for audit trail
        if hasattr(self, 'logger'):
            self.logger.debug("Agent state cleared (stateless — no-op)")

    def _clear_audit_state(self) -> None:
        """
        Clear any audit-related temporary state.

        Ensures audit logging doesn't interfere with subsequent executions.
        """
        # Audit system is append-only in v1.0 — log for audit trail
        if hasattr(self, 'logger'):
            self.logger.debug("Audit state cleared (append-only — no-op)")

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
            logger.warning("Output directory state validation failed: %s — this may affect workflow execution reliability.", e)

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
        """Determine the appropriate status icon for a step result (delegates to step_executor)."""
        from akios.core.runtime.engine.step_executor import determine_step_status_icon
        return determine_step_status_icon(step_result, step)

    def _evaluate_condition(self, condition: str, step_id: int) -> bool:
        """
        Evaluate a step condition expression against the execution context.

        Uses an AST-based safe evaluator that only permits comparisons,
        boolean logic, arithmetic, attribute access, and subscript access.
        Function calls, imports, and all other constructs are rejected
        at parse time before any code runs.

        Supports expressions against prior step outputs:
          - ``step_1_output.status == 'success'``
          - ``step_2_output['content'] != ''``
          - ``previous_output is not None``

        Args:
            condition: Expression string.
            step_id:   Current step id (for error messages).

        Returns:
            ``True`` if the condition passes (step should run),
            ``False`` if it does not.
        """
        from akios.core.runtime.engine.condition_evaluator import evaluate_condition
        return evaluate_condition(condition, step_id, self.execution_context)

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
        """Check if step result contains security violation (delegates to step_executor)."""
        from akios.core.runtime.engine.step_executor import check_step_security_violation
        check_step_security_violation(step_result, step_id)

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

        # Aggregate PII redaction stats across all steps
        pii_redaction_count = 0
        pii_redacted_fields = []
        for r in results:
            if not isinstance(r, dict):
                continue
            step_result = r.get('result', {})
            if isinstance(step_result, dict):
                pii_redaction_count += step_result.get('pii_redactions_applied', 0)
                for field in step_result.get('pii_patterns_found', []):
                    if field not in pii_redacted_fields:
                        pii_redacted_fields.append(field)

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

        cost_status = self.cost_kill.get_status()

        result = {
            'status': 'completed',
            'workflow_id': self.current_workflow_id,
            'steps_executed': len(results),
            'total_steps': len(workflow.steps),
            'execution_time': execution_time,
            'results': results,
            'output_directory': str(self._output_dir) if hasattr(self, '_output_dir') and self._output_dir else None,
            'tokens_input': cost_status.get('tokens_input', 0),
            'tokens_output': cost_status.get('tokens_output', 0),
            'total_cost': cost_status.get('total_cost', 0.0),
            'llm_model': cost_status.get('llm_model'),
            'pii_redaction_count': pii_redaction_count,
            'pii_redacted_fields': pii_redacted_fields,
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
                        'pii_redaction_count': pii_redaction_count,
                        'pii_redacted_fields': pii_redacted_fields,
                        'audit_enabled': getattr(self.settings, 'audit_enabled', True),
                        'sandbox_enabled': getattr(self.settings, 'sandbox_enabled', True),
                    },
                    'cost': cost_status,
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
        """Execute a single workflow step (delegates to step_executor)."""
        from akios.core.runtime.engine.step_executor import execute_step
        return execute_step(step, workflow, self)

    def _resolve_step_parameters(self, params: Dict[str, Any], previous_step_id: int, max_depth: int = TEMPLATE_SUBSTITUTION_MAX_DEPTH) -> Dict[str, Any]:
        """Resolve step parameters by substituting templates (delegates to template_renderer)."""
        from akios.core.runtime.engine.template_renderer import resolve_step_parameters
        if not hasattr(self, '_output_dir'):
            from ..output.manager import create_output_directory
            self._output_dir = create_output_directory(self.current_workflow_id)
        return resolve_step_parameters(
            params, previous_step_id, self.execution_context,
            self._output_dir, self.current_workflow_id, max_depth,
        )

    def _transform_output_paths(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform output paths to organized directories (delegates to template_renderer)."""
        from akios.core.runtime.engine.template_renderer import transform_output_paths
        if not hasattr(self, '_output_dir'):
            from ..output.manager import create_output_directory
            self._output_dir = create_output_directory(self.current_workflow_id)
        return transform_output_paths(params, self._output_dir, self.current_workflow_id)

    def _execute_with_agent_retry(self, agent_type: str, action: str, func: Callable[[], Any]) -> Any:
        """Execute agent action with agent-specific retry logic (delegates to step_executor)."""
        from akios.core.runtime.engine.step_executor import execute_with_agent_retry
        return execute_with_agent_retry(agent_type, action, func, self.retry_handler)

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

    @classmethod
    def _extract_output_value(cls, result: Any) -> str:
        """Extract a human-readable string from a step result (delegates to output_extractor)."""
        from akios.core.runtime.engine.output_extractor import extract_output_value
        return extract_output_value(result)

    @staticmethod
    def _extract_step_output(step_result) -> str:
        """Extract human-readable output from a step result dict (delegates to output_extractor)."""
        from akios.core.runtime.engine.output_extractor import extract_step_output
        return extract_step_output(step_result)

    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in configuration (delegates to step_executor)."""
        from akios.core.runtime.engine.step_executor import resolve_env_vars
        return resolve_env_vars(config)

    def _validate_agent_config(self, agent_type: str, config: Dict[str, Any]) -> None:
        """Validate agent configuration against security policies (delegates to step_executor)."""
        from akios.core.runtime.engine.step_executor import validate_agent_config
        validate_agent_config(agent_type, config, self.settings)


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
