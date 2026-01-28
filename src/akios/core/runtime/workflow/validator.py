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
Workflow validator - Validate steps, agents, params, fail fast on invalid YAML

Strict schema validation for sequential workflows.
"""

import os
import json
from typing import Dict, List, Any, Set

# Conditional import for schema validation
try:
    import jsonschema
    SCHEMA_VALIDATION_AVAILABLE = True
except ImportError:
    SCHEMA_VALIDATION_AVAILABLE = False

# Allowed agents
ALLOWED_AGENTS = {'llm', 'http', 'filesystem', 'tool_executor'}

# Agent-specific allowed actions
ALLOWED_ACTIONS = {
    'llm': {'generate', 'complete', 'chat'},
    'http': {'get', 'post', 'put', 'delete', 'patch'},
    'filesystem': {'read', 'write', 'list', 'exists', 'stat', 'analyze'},
    'tool_executor': {'execute', 'run', 'call'}
}


# Global schema cache for performance
_SCHEMA_CACHE = None

def validate_workflow_schema(workflow_data: Dict[str, Any]) -> None:
    """
    JSON schema validation for structural completeness.

    Validates workflow structure against formal JSON schema.
    Provides enhanced error messages for structural issues.
    """
    if not SCHEMA_VALIDATION_AVAILABLE:
        return  # Graceful degradation if jsonschema not available

    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        try:
            # Load schema from package (cached for performance)
            schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'schema', 'workflow_schema.json')
            with open(schema_path, 'r', encoding='utf-8') as f:
                _SCHEMA_CACHE = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Log warning but don't print to stderr in production workflows
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Workflow schema not found or corrupted - skipping enhanced validation")
            return

    try:
        # Validate against cached schema
        jsonschema.validate(instance=workflow_data, schema=_SCHEMA_CACHE)

    except jsonschema.ValidationError as e:
        raise WorkflowValidationError(_format_schema_error(e))


def _format_schema_error(error: jsonschema.ValidationError) -> str:
    """
    Convert JSON schema errors to user-friendly messages with helpful hints.

    Provides clear, actionable error messages for workflow structure issues.
    """
    path = list(error.absolute_path)

    # Handle missing required fields
    if error.validator == 'required':
        missing_field = error.message.split("'")[1]

        # Check if this is a step-level missing field
        if len(path) >= 2 and path[0] == 'steps' and isinstance(path[1], int):
            step_num = path[1] + 1
            if missing_field == 'action':
                return ("Error: Invalid workflow configuration\n"
                       f"Step {step_num} is missing the 'action' field\n\n"
                       "Each step needs: agent, action, parameters\n"
                       "Hint: Check your workflow.yml and compare with the original template.")
            elif missing_field == 'agent':
                return ("Error: Invalid workflow configuration\n"
                       f"Step {step_num} is missing the 'agent' field\n\n"
                       "Each step needs: agent, action, parameters\n"
                       "Hint: Add one of: filesystem, http, llm, tool_executor")
            elif missing_field == 'parameters':
                return ("Error: Invalid workflow configuration\n"
                       f"Step {step_num} is missing the 'parameters' field\n\n"
                       "Each step needs: agent, action, parameters\n"
                       "Hint: Add a parameters object with the required fields for this action")
            elif missing_field == 'config':
                return ("Error: Invalid workflow configuration\n"
                       f"Step {step_num} is missing the 'config' field\n\n"
                       "Most agents require configuration (e.g., filesystem needs allowed_paths)\n"
                       "Hint: Check the template for the correct config structure")
            else:
                return f"Step {step_num}: missing required field '{missing_field}'"
        # Workflow-level missing fields
        else:
            if missing_field == 'name':
                return ("Error: Invalid workflow configuration\n"
                       "Workflow is missing the 'name' field\n\n"
                       "Every workflow needs a name to identify it\n"
                       "Hint: Add name: \"Your Workflow Name\"")
            elif missing_field == 'description':
                return ("Error: Invalid workflow configuration\n"
                       "Workflow is missing the 'description' field\n\n"
                       "Every workflow needs a description\n"
                       "Hint: Add description: \"What this workflow does\"")
            elif missing_field == 'steps':
                return ("Error: Invalid workflow configuration\n"
                       "Workflow is missing the 'steps' field\n\n"
                       "Every workflow needs steps to execute\n"
                       "Hint: Add steps: [] and define your workflow steps")
            else:
                return f"Workflow missing required field '{missing_field}'"

    # Handle invalid enum values
    if error.validator == 'enum':
        if 'agent' in str(error.absolute_path):
            step_num = path[0] + 1 if path and isinstance(path[0], int) else '?'
            return ("Error: Invalid workflow configuration\n"
                   f"Step {step_num} uses unknown agent '{error.instance}'\n\n"
                   "Valid agents: filesystem, http, llm, tool_executor\n"
                   "Hint: Choose one of the 4 supported agents")
        return f"Invalid value '{error.instance}' for field '{'.'.join(str(p) for p in path)}'"

    # Handle type errors
    if error.validator == 'type':
        field_name = '.'.join(str(p) for p in path) if path else 'workflow'
        expected_type = error.validator_value
        if isinstance(expected_type, list):
            expected_type = ' or '.join(expected_type)
        if path and len(path) >= 2 and path[0] == 'steps' and isinstance(path[1], int):
            step_num = path[1] + 1
            return f"Error: Invalid workflow configuration\nStep {step_num} has wrong type for '{path[2] if len(path) > 2 else 'field'}'\n\nExpected type: {expected_type}\nHint: Check the template for correct value types"
        return f"'{field_name}' must be of type {expected_type}"

    # Generic fallback with helpful hint
    return f"Error: Invalid workflow structure\n{error.message}\n\nHint: Compare your workflow.yml with the original template structure"


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""
    pass


def validate_workflow(workflow_data: Dict[str, Any]) -> None:
    """
    Validate workflow data structure.

    Args:
        workflow_data: Workflow data dictionary

    Raises:
        WorkflowValidationError: If validation fails
    """
    errors = []

    # Check basic structure
    if not isinstance(workflow_data, dict):
        errors.append("Workflow must be a dictionary")

    # Check required fields
    if 'steps' not in workflow_data:
        errors.append("Workflow must have 'steps' field")

    # Validate steps
    if 'steps' in workflow_data:
        steps_errors = _validate_steps(workflow_data['steps'])
        errors.extend(steps_errors)

    # Check for forbidden features
    forbidden_errors = _check_forbidden_features(workflow_data)
    errors.extend(forbidden_errors)

    # Schema validation for structural completeness
    try:
        validate_workflow_schema(workflow_data)
    except WorkflowValidationError as e:
        errors.append(str(e))

    if errors:
        error_msg = "Workflow validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        raise WorkflowValidationError(error_msg)


def _validate_steps(steps_data: Any) -> List[str]:
    """Validate the steps array"""
    errors = []

    if not isinstance(steps_data, list):
        errors.append("'steps' must be a list")
        return errors

    if not steps_data:
        errors.append("'steps' cannot be empty")
        return errors

    # Check each step
    for i, step_data in enumerate(steps_data):
        step_errors = _validate_single_step(step_data, i + 1)
        errors.extend(step_errors)

    return errors


def _validate_single_step(step_data: Any, step_num: int) -> List[str]:
    """Validate a single workflow step"""
    errors = []

    if not isinstance(step_data, dict):
        errors.append(f"Step {step_num}: must be a dictionary")
        return errors

    # Check required fields
    required_fields = ['agent', 'action']
    for field in required_fields:
        if field not in step_data:
            errors.append(f"Step {step_num}: missing required field '{field}'")

    # Validate agent
    if 'agent' in step_data:
        agent_errors = _validate_agent(step_data['agent'], step_num)
        errors.extend(agent_errors)

        # Validate action for this agent
        if 'action' in step_data:
            action_errors = _validate_action(step_data['agent'], step_data['action'], step_num)
            errors.extend(action_errors)

    # Validate parameters
    if 'parameters' in step_data:
        param_errors = _validate_parameters(step_data['parameters'], step_num)
        errors.extend(param_errors)

    # Check for step ID (optional but validated if present)
    if 'step' in step_data:
        step_id = step_data['step']
        if not isinstance(step_id, int) or step_id < 1:
            errors.append(f"Step {step_num}: 'step' must be a positive integer")

    # Validate agent-specific configuration
    if 'agent' in step_data and 'config' in step_data:
        config_errors = _validate_agent_config(step_data['agent'], step_data['config'], step_num)
        errors.extend(config_errors)

    return errors


def _validate_agent(agent: str, step_num: int) -> List[str]:
    """Validate agent name"""
    errors = []

    if not isinstance(agent, str):
        errors.append(f"Step {step_num}: 'agent' must be a string")
        return errors

    if agent not in ALLOWED_AGENTS:
        errors.append(f"Step {step_num}: agent '{agent}' not allowed. Must be one of: {', '.join(ALLOWED_AGENTS)}")

    return errors


def _validate_action(agent: str, action: str, step_num: int) -> List[str]:
    """Validate action for the given agent"""
    errors = []

    if not isinstance(action, str):
        errors.append(f"Step {step_num}: 'action' must be a string")
        return errors

    if agent in ALLOWED_ACTIONS:
        allowed_actions = ALLOWED_ACTIONS[agent]
        if action not in allowed_actions:
            errors.append(f"Step {step_num}: action '{action}' not allowed for agent '{agent}'. Must be one of: {', '.join(allowed_actions)}")

    return errors


def _validate_parameters(parameters: Any, step_num: int) -> List[str]:
    """Validate parameters structure"""
    errors = []

    if not isinstance(parameters, dict):
        errors.append(f"Step {step_num}: 'parameters' must be a dictionary")
        return errors

    # SECURITY: Comprehensive parameter validation - prevent code injection and dangerous operations
    dangerous_patterns = [
        # Code execution patterns
        'eval(', 'exec(', '__import__', 'subprocess', 'os.system', 'os.popen',
        'os.spawn', 'os.exec', 'os.fork', 'multiprocessing', 'threading',
        # File system patterns
        '/etc/passwd', '/etc/shadow', '/etc/hosts', '../', '..\\',
        # Network patterns (basic detection)
        'socket', 'urllib', 'requests', 'http://', 'https://', 'ftp://',
        # Dangerous imports
        'import os', 'import sys', 'import subprocess', 'from os import',
        'from sys import', 'from subprocess import'
    ]

    for key, value in parameters.items():
        if isinstance(value, str):
            value_lower = value.lower()
            for pattern in dangerous_patterns:
                if pattern in value_lower:
                    errors.append(f"Step {step_num}: parameter '{key}' contains dangerous pattern '{pattern}' - "
                                f"potentially unsafe operation detected")

            # Additional validation: check for suspicious template patterns
            if '{' in value and '}' in value:
                # Allow known safe templates but flag suspicious ones
                suspicious_templates = ['{__import__', '{eval', '{exec', '{os.', '{subprocess.']
                for suspicious in suspicious_templates:
                    if suspicious in value:
                        errors.append(f"Step {step_num}: parameter '{key}' contains suspicious template pattern "
                                    f"'{suspicious}' - template injection risk")

    return errors


def _check_forbidden_features(workflow_data: Dict[str, Any]) -> List[str]:
    """Check for features forbidden in current scope"""
    errors = []

    # Check for conditional logic
    forbidden_keys = ['if', 'condition', 'conditions', 'when', 'unless', 'switch', 'case']

    def check_dict_for_forbidden(data: Any, path: str = "") -> List[str]:
        forbidden_found = []

        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in forbidden_keys:
                    forbidden_found.append(f"Forbidden conditional '{key}' at {path}")

                # Recursively check nested structures
                if isinstance(value, (dict, list)):
                    nested_path = f"{path}.{key}" if path else key
                    forbidden_found.extend(check_dict_for_forbidden(value, nested_path))

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    nested_path = f"{path}[{i}]"
                    forbidden_found.extend(check_dict_for_forbidden(item, nested_path))

        return forbidden_found

    errors.extend(check_dict_for_forbidden(workflow_data))

    # Check for parallel/loop constructs in workflow structure only
    # Only check actual workflow keys and step parameters, not names/descriptions
    parallel_indicators = ['parallel', 'parallel_steps', 'loop', 'for_each', 'map', 'reduce']

    def check_workflow_structure(data: Any) -> bool:
        """Check workflow structure for forbidden constructs (excluding names/descriptions)"""
        if isinstance(data, dict):
            for key, value in data.items():
                # Skip name and description fields
                if key.lower() in ['name', 'description']:
                    continue
                # Check step parameters and workflow-level keys
                if key.lower() in parallel_indicators:
                    return True
                if isinstance(value, (dict, list)):
                    if check_workflow_structure(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                if check_workflow_structure(item):
                    return True
        return False

    if check_workflow_structure(workflow_data):
        errors.append("Forbidden parallel/loop construct detected (sequential only)")

    return errors


def _validate_agent_config(agent: str, config: Any, step_num: int) -> List[str]:
    """Validate agent-specific configuration requirements"""
    errors = []

    if not isinstance(config, dict):
        errors.append(f"Step {step_num}: 'config' must be a dictionary for {agent} agent")
        return errors

    # Filesystem agent requires allowed_paths
    if agent == 'filesystem':
        if 'allowed_paths' not in config:
            errors.append(f"Step {step_num}: filesystem agent requires 'allowed_paths' in config")
            errors.append(f"Example: config: {{ allowed_paths: ['./data/input', './data/output'] }}")
        elif not isinstance(config['allowed_paths'], list):
            errors.append(f"Step {step_num}: filesystem 'allowed_paths' must be a list of paths")
        elif not config['allowed_paths']:
            errors.append(f"Step {step_num}: filesystem 'allowed_paths' cannot be empty")
        else:
            # Validate each path is a string
            for i, path in enumerate(config['allowed_paths']):
                if not isinstance(path, str):
                    errors.append(f"Step {step_num}: filesystem allowed_paths[{i}] must be a string")

    # Add more agent-specific validations as needed in future
    # Example: HTTP agent might need timeout validation
    # if agent == 'http':
    #     if 'timeout' in config and not isinstance(config['timeout'], (int, float)):
    #         errors.append(f"Step {step_num}: http 'timeout' must be a number")

    return errors


def get_allowed_agents() -> Set[str]:
    """Get the set of allowed agents"""
    return ALLOWED_AGENTS.copy()


def get_allowed_actions_for_agent(agent: str) -> Set[str]:
    """Get allowed actions for a specific agent"""
    return ALLOWED_ACTIONS.get(agent, set()).copy()
