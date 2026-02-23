# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Template Renderer — Step parameter resolution and output path transformation.

Handles template substitution (``{previous_output}``, ``{step_X_output}``)
and output path transformation to timestamped directories.
"""

import re
import logging
from typing import Any, Dict, Optional

from akios.config.constants import TEMPLATE_SUBSTITUTION_MAX_DEPTH
from akios.core.runtime.engine.output_extractor import extract_output_value

logger = logging.getLogger(__name__)


def resolve_step_parameters(
    params: Dict[str, Any],
    previous_step_id: int,
    execution_context: Dict[str, Any],
    output_dir: Optional[Any] = None,
    workflow_id: Optional[str] = None,
    max_depth: int = TEMPLATE_SUBSTITUTION_MAX_DEPTH,
) -> Dict[str, Any]:
    """
    Resolve step parameters by substituting templates with actual values.

    Substitutes ``{previous_output}`` and ``{step_X_output}`` templates
    with the corresponding step results from the execution context.
    Also transforms output paths to timestamped directories.

    Args:
        params:            Step parameters that may contain templates.
        previous_step_id:  ID of the previous step (1-indexed).
        execution_context: Engine's execution context dict.
        output_dir:        Pre-created output directory Path (or None).
        workflow_id:       Current workflow ID (for output dir creation).
        max_depth:         Maximum recursion depth to prevent infinite loops.

    Returns:
        Parameters with templates resolved and output paths transformed.
    """
    if not params:
        return params

    # SECURITY: Prevent DoS through excessively large parameter structures
    _check_size(params)

    # Get the previous step's result if it exists
    previous_result = None
    if previous_step_id > 0:
        previous_result_key = f"step_{previous_step_id}_result"
        previous_result = execution_context.get(previous_result_key)

    def substitute_value(value: Any, depth: int = 0) -> Any:
        """Recursively substitute templates in a value with depth protection."""
        if depth > max_depth:
            raise RuntimeError(
                f"Template substitution exceeded maximum depth of {max_depth}. "
                f"Possible circular reference or excessive nesting in step {previous_step_id + 1}."
            )

        # SECURITY: size check at each substitution level
        if depth > 0 and isinstance(value, str) and len(value) > 10000:
            raise RuntimeError(
                f"Template substitution value too large ({len(value)} chars) at depth {depth} "
                f"in step {previous_step_id + 1}. Possible DoS attempt."
            )

        if isinstance(value, str):
            value = _substitute_previous_output(value, previous_result, previous_step_id)
            value = _substitute_step_outputs(value, execution_context, previous_step_id)
            return value
        elif isinstance(value, dict):
            return {k: substitute_value(v, depth + 1) for k, v in value.items()}
        elif isinstance(value, list):
            return [substitute_value(item, depth + 1) for item in value]
        return value

    resolved_params = substitute_value(params)
    resolved_params = transform_output_paths(resolved_params, output_dir, workflow_id)
    return resolved_params


def transform_output_paths(
    params: Dict[str, Any],
    output_dir: Optional[Any] = None,
    workflow_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transform output paths to organized directories with symlinks.

    Transforms paths like ``./data/output/file.txt`` to
    ``./data/output/run_YYYY-MM-DD_HH-MM-SS/file.txt``.

    Args:
        params:      Parameters that may contain output paths.
        output_dir:  Pre-created output directory Path (or None).
        workflow_id: Current workflow ID (for output dir creation).

    Returns:
        Parameters with output paths transformed.
    """
    if output_dir is None and workflow_id is not None:
        from ..output.manager import create_output_directory
        output_dir = create_output_directory(workflow_id)

    if output_dir is None:
        return params

    def transform_value(value: Any) -> Any:
        """Recursively transform output paths in values."""
        if isinstance(value, str):
            if value.startswith('./data/output/'):
                filename = value.replace('./data/output/', '', 1)
                return str(output_dir / filename)
            return value
        elif isinstance(value, dict):
            return {k: transform_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [transform_value(item) for item in value]
        return value

    return transform_value(params)


# ── Internal helpers ────────────────────────────────────────────────

def _check_size(obj: Any, max_size: int = 10000) -> int:
    """Check object size to prevent memory exhaustion attacks."""
    if isinstance(obj, dict):
        size = len(obj)
        for v in obj.values():
            size += _check_size(v, max_size)
            if size > max_size:
                raise RuntimeError(
                    f"Parameter structure too large (> {max_size} elements) - possible DoS attack"
                )
        return size
    elif isinstance(obj, (list, tuple)):
        size = len(obj)
        for item in obj:
            size += _check_size(item, max_size)
            if size > max_size:
                raise RuntimeError(
                    f"Parameter structure too large (> {max_size} elements) - possible DoS attack"
                )
        return size
    return 1


def _substitute_previous_output(
    value: str,
    previous_result: Any,
    previous_step_id: int,
) -> str:
    """Substitute ``{previous_output}`` in a string value."""
    if '{previous_output}' not in value:
        return value

    if previous_result is None:
        raise RuntimeError(
            f"Template '{{previous_output}}' used in step {previous_step_id + 1} "
            f"but no previous step result is available. "
            f"Ensure step {previous_step_id} completed successfully."
        )

    if isinstance(previous_result, dict):
        result_str = extract_output_value(previous_result)
    elif isinstance(previous_result, (list, tuple)):
        result_str = '\n'.join(str(item) for item in previous_result)
    else:
        result_str = str(previous_result)

    return value.replace('{previous_output}', result_str)


def _substitute_step_outputs(
    value: str,
    execution_context: Dict[str, Any],
    previous_step_id: int,
) -> str:
    """Substitute ``{step_X_output}`` and ``{step_X_output[key]}`` patterns."""
    # Use [^\]]+ to capture any key (including invalid ones) so validation can reject them
    step_pattern = re.compile(r'\{step_(\d+)_output(?:\[([^\]]+)\])?\}')
    matches = step_pattern.findall(value)
    if not matches:
        return value

    result_value = value
    for step_num_str, key in matches:
        step_num = int(step_num_str)

        # SECURITY: Validate step number range
        if step_num < 1 or step_num > 1000:
            raise RuntimeError(
                f"Template step number {step_num} is out of valid range (1-1000) "
                f"in step {previous_step_id + 1}. This may indicate a malformed template."
            )

        # SECURITY: Validate key name
        if key and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            raise RuntimeError(
                f"Template key '{key}' contains invalid characters in step {previous_step_id + 1}. "
                f"Keys must be valid Python identifiers."
            )

        step_result_key = f"step_{step_num}_result"
        step_result = execution_context.get(step_result_key)

        if step_result is None:
            template_name = f'step_{step_num}_output'
            if key:
                template_name += f'[{key}]'
            raise RuntimeError(
                f"Template '{{{template_name}}}' used in step {previous_step_id + 1} "
                f"but step {step_num} result is not available. "
                f"Ensure step {step_num} completed successfully."
            )

        if key:
            if isinstance(step_result, dict) and key in step_result:
                step_str = str(step_result[key])
            else:
                raise RuntimeError(
                    f"Template '{{step_{step_num}_output[{key}]}}' used in step {previous_step_id + 1} "
                    f"but key '{key}' not found in step {step_num} result."
                )
        else:
            if isinstance(step_result, dict):
                step_str = extract_output_value(step_result)
            elif isinstance(step_result, (list, tuple)):
                step_str = '\n'.join(str(item) for item in step_result)
            else:
                step_str = str(step_result)

        template_pattern = f'{{step_{step_num}_output'
        if key:
            template_pattern += f'[{key}]'
        template_pattern += '}'
        result_value = result_value.replace(template_pattern, step_str)

    return result_value
