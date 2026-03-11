# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# GPL-3.0-only
"""
Lifecycle hooks bridge — AKIOS workflow events to EnforceCore HookRegistry (v1.2.0-rc).

Fires hooks at key workflow lifecycle points when EnforceCore is available:
- pre_workflow: before workflow execution starts
- post_workflow: after workflow execution completes
- step_complete: after each step executes

Hooks are always optional. Missing EnforceCore → no hooks → no change in behavior.
Install with: pip install akios[enforcecore]
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def fire_workflow_hook(event: str, context: Dict[str, Any]) -> None:
    """
    Fire a workflow lifecycle hook via EnforceCore's HookRegistry.

    Args:
        event: One of 'pre_workflow', 'post_workflow', 'step_complete'
        context: Dict with workflow context (name, steps, status, etc.)

    This is a no-op when:
    - EnforceCore is not installed
    - use_enforcecore is False in settings
    - No hooks are registered
    - Any error occurs (hooks never block execution)
    """
    try:
        from akios.config import get_settings
        if not getattr(get_settings(), 'use_enforcecore', False):
            return

        from enforcecore.plugins.hooks import HookRegistry
        registry = HookRegistry.global_registry()

        if event == "pre_workflow":
            if registry._pre_call:
                # Build a minimal HookContext-compatible dict
                _fire_hooks(registry._pre_call, context)
        elif event == "post_workflow":
            if registry._post_call:
                _fire_hooks(registry._post_call, context)
        elif event == "step_complete":
            # Use post_call hooks for step completion
            if registry._post_call:
                _fire_hooks(registry._post_call, context)

    except ImportError:
        pass  # No EnforceCore — skip silently
    except Exception as e:
        logger.debug("Lifecycle hook error (non-fatal): %s", e)


def _fire_hooks(hooks: list, context: Dict[str, Any]) -> None:
    """Fire a list of hooks with context. Errors are caught per-hook."""
    for hook in hooks:
        try:
            hook(context)
        except Exception as e:
            logger.debug("Hook %s error (non-fatal): %s", getattr(hook, '__name__', '?'), e)
