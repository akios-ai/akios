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
Workflow parser - Parse YAML into sequential steps (agent + action + params)

Strict schema validation for simple sequential workflows.
"""

import os
import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from .validator import validate_workflow
from ...cache.manager import get_cache_manager, get_template_cache_key


def _substitute_env_vars(data: Any) -> Any:
    """
    Recursively substitute environment variables in strings using ${VAR:-default} syntax.

    In mock mode, skips substitution of LLM-related variables to allow testing without configuration.

    Args:
        data: The data structure to process (dict, list, or string)

    Returns:
        The data with environment variables substituted
    """
    # Check if we're in mock mode - if so, skip LLM provider substitution
    is_mock_mode = os.getenv('AKIOS_MOCK_LLM') == '1'

    if isinstance(data, str):
        # Handle ${VAR:-default} syntax
        def replace_var(match):
            var_expr = match.group(1)
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
            else:
                var_name = var_expr
                default_value = ''

            # In mock mode, skip LLM provider variables to allow testing without configuration
            if is_mock_mode and var_name in ['AKIOS_LLM_PROVIDER', 'AKIOS_LLM_MODEL']:
                # Use default values for mock mode or skip substitution
                return default_value if default_value else 'mock'

            # Get environment variable, use default if not set or empty
            env_value = os.getenv(var_name) or default_value
            if not env_value:
                # If env var is not set and no default, treat as missing
                raise ValueError(f"Missing environment variable '{var_name}' required for workflow execution. Please set it with: export {var_name}='your-value'")
            return env_value

        # Replace ${VAR:-default} patterns
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_var, data)

    elif isinstance(data, dict):
        return {key: _substitute_env_vars(value) for key, value in data.items()}

    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]

    else:
        return data


class WorkflowStep:
    """Represents a single workflow step"""

    def __init__(self, step_id: int, agent: str, action: str,
                 parameters: Optional[Dict[str, Any]] = None,
                 config: Optional[Dict[str, Any]] = None,
                 condition: Optional[str] = None,
                 on_error: Optional[str] = None):
        self.step_id = step_id
        self.agent = agent
        self.action = action
        self.parameters = parameters or {}
        self.config = config or {}
        self.condition = condition  # e.g. "step_1_output.status == 'success'"
        self.on_error = on_error    # "skip" | "fail" | "retry"

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        d = {
            "step_id": self.step_id,
            "agent": self.agent,
            "action": self.action,
            "parameters": self.parameters,
            "config": self.config
        }
        if self.condition:
            d["condition"] = self.condition
        if self.on_error:
            d["on_error"] = self.on_error
        return d

    def __repr__(self) -> str:
        return f"WorkflowStep({self.step_id}: {self.agent}.{self.action})"


class Workflow:
    """Represents a parsed workflow"""

    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []

    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow"""
        self.steps.append(step)

    def get_step(self, step_id: int) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps]
        }

    def __len__(self) -> int:
        return len(self.steps)

    def __repr__(self) -> str:
        return f"Workflow({self.name}, {len(self.steps)} steps)"


def parse_workflow(workflow_path: str) -> Workflow:
    """
    Parse a YAML workflow file into a Workflow object.

    Uses intelligent caching to optimize repeated parsing of the same workflows.

    Args:
        workflow_path: Path to YAML workflow file

    Returns:
        Parsed Workflow object

    Raises:
        FileNotFoundError: If workflow file doesn't exist
        ValueError: If workflow format is invalid
        yaml.YAMLError: If YAML parsing fails
    """
    workflow_file = Path(workflow_path)

    if not workflow_file.exists():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

    # Use caching for performance optimization
    cache_manager = get_cache_manager()

    def _parse_workflow():
        """Parse workflow without caching."""
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f)

            # Substitute environment variables in the workflow data
            workflow_data = _substitute_env_vars(workflow_data)

            # Validate the workflow structure
            validate_workflow(workflow_data)

            # Parse the workflow
            workflow = _parse_workflow_data(workflow_data)

            return workflow

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in workflow file {workflow_path}: {e}") from e

    # Get file modification time for cache key
    mtime = workflow_file.stat().st_mtime

    # Create cache key including file path and modification time
    cache_key = get_template_cache_key(str(workflow_path), str(mtime))

    # DISABLED: Workflow caching causes JSON serialization failures with Workflow objects
    # Workflow parsing is fast enough (<50ms) that caching provides minimal benefit
    # return cache_manager.get_or_compute(cache_key, _parse_workflow, ttl_seconds=1800)

    # Direct parse every time - eliminates the JSON serialization bug
    return _parse_workflow()


def parse_workflow_string(workflow_yaml: str) -> Workflow:
    """
    Parse a YAML workflow string into a Workflow object.

    Args:
        workflow_yaml: YAML workflow content as string

    Returns:
        Parsed Workflow object

    Raises:
        ValueError: If workflow format is invalid
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        workflow_data = yaml.safe_load(workflow_yaml)

        # Validate the workflow structure
        validate_workflow(workflow_data)

        # Parse the workflow
        workflow = _parse_workflow_data(workflow_data)

        return workflow

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in workflow string: {e}") from e


def _parse_workflow_data(workflow_data: Dict[str, Any]) -> Workflow:
    """
    Parse validated workflow data into Workflow object.

    Args:
        workflow_data: Validated workflow dictionary

    Returns:
        Workflow object
    """
    # Extract workflow metadata
    name = workflow_data.get('name', 'unnamed_workflow')
    description = workflow_data.get('description')

    workflow = Workflow(name=name, description=description)

    # Parse steps
    steps_data = workflow_data.get('steps', [])

    for step_data in steps_data:
        step_id = step_data.get('step', len(workflow.steps) + 1)
        agent = step_data.get('agent', '')
        action = step_data.get('action', '')
        parameters = step_data.get('parameters', {})
        config = step_data.get('config', {})
        condition = step_data.get('condition', None)
        on_error = step_data.get('on_error', None)

        step = WorkflowStep(
            step_id=step_id,
            agent=agent,
            action=action,
            parameters=parameters,
            config=config,
            condition=condition,
            on_error=on_error,
        )

        workflow.add_step(step)

    return workflow


def parse_workflow_from_dict(workflow_data: Dict[str, Any]) -> Workflow:
    """
    Parse a workflow dictionary directly.

    Args:
        workflow_data: Workflow data as dictionary

    Returns:
        Parsed Workflow object

    Raises:
        ValueError: If workflow format is invalid
    """
    # Validate first
    validate_workflow(workflow_data)

    # Parse
    return _parse_workflow_data(workflow_data)
