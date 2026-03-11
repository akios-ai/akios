# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Step Executor — Single-step execution, agent dispatch, retry, and validation.

Handles the mechanics of executing a single workflow step: resolving config,
creating the agent, calling it, handling errors, and emitting audit events.
"""

import os
import sys
import time
import logging
from typing import Any, Callable, Dict

from akios.config.constants import (
    SECURITY_VIOLATION_PATTERNS,
    AUDIT_ERROR_CONTEXT_KEY,
    AUDIT_EXECUTION_TIME_KEY,
)

logger = logging.getLogger(__name__)


def execute_step(
    step,
    workflow,
    engine,
) -> Dict[str, Any]:
    """
    Execute a single workflow step.

    Args:
        step:     WorkflowStep to execute.
        workflow: Parent workflow object.
        engine:   RuntimeEngine instance (for context, settings, kill-switches).

    Returns:
        Step execution result dict.
    """
    from akios.core.runtime.engine.engine import _get_agent_class, _get_append_audit_event

    step_start = time.time()

    try:
        # Get agent class
        agent_class = _get_agent_class()(step.agent)

        # Resolve agent configuration
        step_config = step.config
        if step.agent == 'llm' and 'api_key' in step_config:
            config_for_resolution = {k: v for k, v in step_config.items() if k != 'api_key'}
            resolved_config = resolve_env_vars(config_for_resolution)
            resolved_config['api_key'] = step_config['api_key']
        else:
            resolved_config = resolve_env_vars(step_config)

        validate_agent_config(step.agent, resolved_config, engine.settings)

        # Override read_only for filesystem write actions
        if step.agent == 'filesystem' and step.action == 'write':
            resolved_config = dict(resolved_config)
            resolved_config['read_only'] = False

        # Create agent
        agent = agent_class(**resolved_config)

        # Prepare step parameters with template substitution
        step_params = engine._resolve_step_parameters(step.parameters.copy(), step.step_id - 1)

        # Add standard workflow metadata
        step_params.update({
            'workflow_id': engine.current_workflow_id,
            'step': step.step_id,
            'workflow_name': workflow.name,
        })

        # Execute with retry
        result = execute_with_agent_retry(
            step.agent, step.action,
            lambda: agent.execute(step.action, step_params),
            engine.retry_handler,
        )

        # Log LLM output
        _log_llm_output(step, result)

        # Update execution context
        engine.execution_context[f"step_{step.step_id}_result"] = result

        # Track cost
        if isinstance(result, dict) and 'cost_incurred' in result:
            engine.cost_kill.add_cost(result['cost_incurred'])

        # Track token usage (input/output breakdown)
        # Check top-level keys first, then fallback to nested usage dict
        if isinstance(result, dict):
            prompt_tok = result.get('prompt_tokens', 0)
            completion_tok = result.get('completion_tokens', 0)

            # Fallback: check nested usage dict (some providers return tokens here)
            if prompt_tok == 0 and completion_tok == 0:
                usage = result.get('usage', {})
                if isinstance(usage, dict):
                    prompt_tok = usage.get('prompt_tokens', 0)
                    completion_tok = usage.get('completion_tokens', 0)

            # Fallback: use tokens_used as total if individual counts missing
            if prompt_tok == 0 and completion_tok == 0:
                tokens_used = result.get('tokens_used', 0)
                if tokens_used > 0:
                    # Estimate 30/70 split when only total is available
                    prompt_tok = int(tokens_used * 0.3)
                    completion_tok = tokens_used - prompt_tok

            if prompt_tok > 0 or completion_tok > 0:
                engine.cost_kill.add_tokens(
                    prompt_tokens=prompt_tok,
                    completion_tokens=completion_tok,
                    model=result.get('llm_model'),
                )

        # Audit
        step_time = time.time() - step_start
        if getattr(engine.settings, 'audit_enabled', True):
            _get_append_audit_event()({
                'workflow_id': engine.current_workflow_id,
                'step': step.step_id,
                'agent': step.agent,
                'action': step.action,
                'result': 'success',
                'metadata': {
                    'execution_time': step_time,
                    'agent_type': step.agent,
                    'has_result': bool(result),
                },
            })

        return {
            'step_id': step.step_id,
            'agent': step.agent,
            'action': step.action,
            'status': 'success',
            'result': result,
            'execution_time': step_time,
        }

    except (RuntimeError, ValueError, ConnectionError, TimeoutError) as exc:
        return _build_error_result(step, workflow, engine, step_start, exc)

    except Exception as exc:
        logger.error("Unexpected error in step %s: %s: %s", step.step_id, type(exc).__name__, exc)
        return _build_error_result(step, workflow, engine, step_start, exc, unexpected=True)


def execute_with_agent_retry(
    agent_type: str,
    action: str,
    func: Callable[[], Any],
    retry_handler: Any,
) -> Any:
    """
    Execute agent action with agent-specific retry logic.

    Args:
        agent_type:     Type of agent being executed.
        action:         Action being performed.
        func:           Function to execute.
        retry_handler:  RetryHandler instance.

    Returns:
        Function result.
    """
    retry_policies = {
        'llm': {'max_attempts': 3, 'retryable': True},
        'http': {'max_attempts': 3, 'retryable': True},
        'filesystem': {'max_attempts': 1, 'retryable': False},
        'tool_executor': {'max_attempts': 1, 'retryable': False},
        'webhook': {'max_attempts': 3, 'retryable': True},
        'database': {'max_attempts': 1, 'retryable': False},
    }

    policy = retry_policies.get(agent_type, {'max_attempts': 1, 'retryable': False})

    if policy['retryable'] and policy['max_attempts'] > 1:
        return retry_handler.execute_with_retry(func)
    return func()


def determine_step_status_icon(step_result: Dict[str, Any], step) -> str:
    """
    Determine the appropriate status icon for a step result.

    Args:
        step_result: Result dictionary from agent execution.
        step:        The workflow step object.

    Returns:
        Status icon string: ✅ (success), ❌ (error), ⚠️ (warning/unknown).
    """
    status = step_result.get('status')
    if status == 'success':
        return "✅"
    elif status == 'error':
        return "❌"

    if step.agent == 'tool_executor':
        returncode = step_result.get('returncode')
        if returncode == 0:
            return "✅"
        elif returncode is not None:
            return "❌"

    if step.agent == 'filesystem':
        if step_result.get('error') or 'error' in step_result.get('message', '').lower():
            return "❌"
        return "✅"

    if step.agent in ('http', 'webhook'):
        status_code = step_result.get('status_code')
        if status_code and 200 <= status_code < 300:
            return "✅"
        elif status_code:
            return "❌"

    return "⚠️"


def check_step_security_violation(step_result: Dict[str, Any], step_id: int) -> None:
    """Check if step result contains a security violation."""
    if step_result.get('status') == 'error':
        error_msg = step_result.get('error', 'Unknown error')
        error_lower = error_msg.lower()
        if any(pattern in error_lower for pattern in SECURITY_VIOLATION_PATTERNS):
            raise RuntimeError(f"Security violation in step {step_id}: {error_msg}")


def resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve environment variables in configuration.

    Entries like ``${VAR_NAME}`` are replaced with the value of the
    corresponding environment variable.

    Args:
        config: Configuration dictionary.

    Returns:
        Configuration with environment variables resolved.

    Raises:
        ConfigurationError: If a required environment variable is missing.
    """
    from akios.core.runtime.engine.engine import ConfigurationError

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


def validate_agent_config(agent_type: str, config: Dict[str, Any], settings: Any) -> None:
    """
    Validate agent configuration against security policies.

    Args:
        agent_type: Type of agent.
        config:     Resolved configuration dictionary.
        settings:   AKIOS settings object.

    Raises:
        SecurityViolationError: If configuration violates security policies.
    """
    from akios.core.runtime.engine.engine import SecurityViolationError

    if agent_type == "llm":
        if "provider" in config:
            provider = config["provider"]
            if provider not in settings.allowed_providers:
                raise SecurityViolationError(
                    f"Provider '{provider}' not allowed. Must be one of: {', '.join(settings.allowed_providers)}"
                )
        if "model" in config:
            allowed_models = set(getattr(settings, 'allowed_models', []))
            if config["model"] not in allowed_models:
                raise SecurityViolationError(
                    f"Invalid model '{config['model']}'. Must be one of: {', '.join(sorted(allowed_models))}"
                )

    elif agent_type == "filesystem":
        allowed_paths = config.get("allowed_paths", [])
        if allowed_paths:
            if not isinstance(allowed_paths, list):
                raise SecurityViolationError("Filesystem agent allowed_paths must be a list")
            dangerous_paths = ['/', '/etc', '/usr', '/var', '/home', '/root']
            for path in allowed_paths:
                path_str = str(path)
                for dangerous in dangerous_paths:
                    if path_str.startswith(dangerous) and path_str != dangerous:
                        raise SecurityViolationError(
                            f"Filesystem agent path '{path_str}' is too permissive. "
                            f"Avoid system directories like {dangerous}"
                        )
        read_only = config.get("read_only", True)
        if not isinstance(read_only, bool):
            raise SecurityViolationError("Filesystem agent read_only must be a boolean")

    elif agent_type == "http":
        timeout = config.get("timeout", 30)
        if timeout > 300:
            raise SecurityViolationError(f"HTTP timeout {timeout}s exceeds maximum 300s")
        max_redirects = config.get("max_redirects", 5)
        if max_redirects > 10:
            raise SecurityViolationError(f"HTTP max_redirects {max_redirects} exceeds maximum 10")

    elif agent_type == "tool_executor":
        step_commands = set(config.get("allowed_commands", []))
        global_commands = set(settings.allowed_commands if hasattr(settings, 'allowed_commands') else [])
        if step_commands and not step_commands.issubset(global_commands):
            raise SecurityViolationError(
                f"Step allowed_commands {step_commands} not subset of global allowed_commands {global_commands}"
            )
        timeout = config.get("timeout", 30)
        if timeout > 300:
            raise SecurityViolationError(f"Tool timeout {timeout}s exceeds maximum 300s")
        max_output = config.get("max_output_size", 1024 * 1024)
        if max_output > 10 * 1024 * 1024:
            raise SecurityViolationError(f"Tool max_output_size {max_output} exceeds maximum 10MB")
        # Content rule check via EnforceCore (v1.2.0+, only if enabled)
        if getattr(settings, 'use_enforcecore', False) and getattr(settings, 'enforcecore_content_rules', True):
            from akios.security.content_rules import check_agent_config
            violations = check_agent_config(agent_type, config)
            if violations:
                raise SecurityViolationError(
                    f"Content rule violation in tool_executor config [{violations[0]['rule']}]: "
                    f"{violations[0]['matched']!r}"
                )

    elif agent_type == "webhook":
        timeout = config.get("timeout", 10)
        if timeout > 30:
            raise SecurityViolationError(f"Webhook timeout {timeout}s exceeds maximum 30s")
        platform = config.get("platform", "generic")
        valid_platforms = ["slack", "discord", "teams", "generic"]
        if platform.lower() not in valid_platforms:
            raise SecurityViolationError(
                f"Webhook platform '{platform}' not recognized. Must be one of: {', '.join(valid_platforms)}"
            )

    elif agent_type == "database":
        timeout = config.get("timeout", 30)
        if timeout > 60:
            raise SecurityViolationError(f"Database timeout {timeout}s exceeds maximum 60s")
        max_rows = config.get("max_rows", 1000)
        if max_rows > 10000:
            raise SecurityViolationError(f"Database max_rows {max_rows} exceeds maximum 10000")
        # Content rule check for database queries via EnforceCore (v1.2.0+)
        if getattr(settings, 'use_enforcecore', False) and getattr(settings, 'enforcecore_content_rules', True):
            from akios.security.content_rules import check_agent_config
            violations = check_agent_config(agent_type, config)
            if violations:
                raise SecurityViolationError(
                    f"Content rule violation in database config [{violations[0]['rule']}]: "
                    f"{violations[0]['matched']!r}"
                )


# ── Internal helpers ────────────────────────────────────────────────

def _log_llm_output(step, result: Any) -> None:
    """Log LLM step output to console."""
    if step.agent != 'llm' or not result or 'text' not in result:
        return

    mock_indicator = ""
    if os.getenv('AKIOS_MOCK_LLM') == '1':
        mock_indicator = " [🎭 MOCK MODE]"

    try:
        from rich.console import Console
        from akios.core.ui.rich_output import get_theme_color
        console = Console()
        console.print(
            f"[bold {get_theme_color('header')}]🤖 Step {step.step_id} Output{mock_indicator}:"
            f"[/bold {get_theme_color('header')}]"
        )
        output_text = result['text']
        if len(output_text) > 300:
            console.print(f"{output_text[:300]}[dim]...[/dim]")
        else:
            console.print(f"{output_text}")
    except ImportError:
        print(f"🤖 Step {step.step_id} Output{mock_indicator}: {result['text']}", file=sys.stdout)
    sys.stdout.flush()


def _build_error_result(
    step, workflow, engine, step_start: float, exc: Exception, unexpected: bool = False,
) -> Dict[str, Any]:
    """Build a step error result dict and emit audit event."""
    from akios.core.runtime.engine.engine import _get_append_audit_event

    step_time = time.time() - step_start
    if getattr(engine.settings, 'audit_enabled', True):
        metadata = {
            'error': str(exc),
            'error_type': type(exc).__name__,
            AUDIT_EXECUTION_TIME_KEY: step_time,
            AUDIT_ERROR_CONTEXT_KEY: (
                f"Workflow '{workflow.name}' Step {step.step_id}: "
                f"{'Unexpected ' if unexpected else ''}{type(exc).__name__}: {exc}"
            ),
        }
        if unexpected:
            metadata['unexpected_error'] = True

        _get_append_audit_event()({
            'workflow_id': engine.current_workflow_id,
            'step': step.step_id,
            'agent': step.agent,
            'action': step.action,
            'result': 'error',
            'metadata': metadata,
        })

    result = {
        'step_id': step.step_id,
        'agent': step.agent,
        'action': step.action,
        'status': 'error',
        'error': f"{'Unexpected error: ' if unexpected else ''}{type(exc).__name__}: {exc}" if unexpected else str(exc),
        'error_type': type(exc).__name__,
        'execution_time': step_time,
    }
    if unexpected:
        result['unexpected_error'] = True
    return result
