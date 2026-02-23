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
Workflow validation command — akios workflow validate <file.yml>

Validates a workflow YAML file against the AKIOS schema:
- YAML syntax check
- Required fields (name, steps)
- Agent/action existence checks
- Step schema validation
"""

import argparse
from pathlib import Path
from typing import Dict, List, Any

from ..helpers import CLIError, output_result, check_project_context
from ...core.ui.rich_output import print_panel, get_theme_color


# Valid agents and their allowed actions (from AGENTS.md)
VALID_AGENTS: Dict[str, List[str]] = {
    "filesystem": ["read", "write", "list", "exists", "stat"],
    "http": ["get", "post", "put", "delete"],
    "llm": ["complete", "chat"],
    "tool_executor": ["run"],
}


def register_workflow_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the workflow command with its subcommands."""
    parser = subparsers.add_parser(
        "workflow",
        help="Workflow management commands",
        description="Validate and inspect AKIOS workflow files",
    )

    workflow_subs = parser.add_subparsers(
        dest="workflow_subcommand",
        help="Workflow action",
    )

    # workflow validate <file>
    validate_parser = workflow_subs.add_parser(
        "validate",
        help="Validate a workflow YAML file",
    )
    validate_parser.add_argument(
        "file",
        help="Path to the workflow YAML file to validate",
    )
    validate_parser.add_argument(
        "--json", action="store_true", default=False,
        help="Output validation results as JSON",
    )
    validate_parser.set_defaults(func=run_workflow_validate)


def run_workflow_validate(args: argparse.Namespace) -> int:
    """Execute workflow validation."""
    check_project_context()

    filepath = Path(args.file)
    json_mode = getattr(args, "json", False)

    try:
        result = validate_workflow(filepath)
    except CLIError:
        raise
    except Exception as e:
        raise CLIError(f"Validation error: {e}")

    if json_mode:
        output_result(result, json_mode=True)
    else:
        _display_validation_result(result, filepath)

    return 0 if result["valid"] else 1


def validate_workflow(filepath: Path) -> Dict[str, Any]:
    """
    Validate a workflow YAML file.

    Returns:
        Dict with 'valid' (bool), 'errors' (list), 'warnings' (list),
        'steps' (int), 'agents_used' (list).
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. File existence
    if not filepath.exists():
        return {
            "valid": False,
            "errors": [f"File not found: {filepath}"],
            "warnings": [],
            "steps": 0,
            "agents_used": [],
        }

    if filepath.suffix not in (".yml", ".yaml"):
        warnings.append(f"File extension '{filepath.suffix}' is not .yml or .yaml")

    # 2. YAML parse
    try:
        import yaml
    except ImportError:
        return {
            "valid": False,
            "errors": ["PyYAML not installed — cannot parse workflow"],
            "warnings": warnings,
            "steps": 0,
            "agents_used": [],
        }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {
            "valid": False,
            "errors": [f"Invalid YAML: {e}"],
            "warnings": warnings,
            "steps": 0,
            "agents_used": [],
        }

    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": ["Workflow must be a YAML mapping (dict), not a list or scalar"],
            "warnings": warnings,
            "steps": 0,
            "agents_used": [],
        }

    # 3. Required top-level fields
    if "name" not in data:
        errors.append("Missing required field: 'name'")

    if "steps" not in data:
        errors.append("Missing required field: 'steps'")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "steps": 0,
            "agents_used": [],
        }

    steps = data["steps"]
    if not isinstance(steps, list):
        errors.append("'steps' must be a list")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "steps": 0,
            "agents_used": [],
        }

    if len(steps) == 0:
        errors.append("Workflow has no steps")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "steps": 0,
            "agents_used": [],
        }

    # 4. Validate each step
    agents_used = set()
    step_numbers = []

    for idx, step in enumerate(steps):
        step_label = f"Step {idx + 1}"

        if not isinstance(step, dict):
            errors.append(f"{step_label}: must be a mapping (dict)")
            continue

        # Step number
        if "step" in step:
            step_num = step["step"]
            if not isinstance(step_num, int):
                errors.append(f"{step_label}: 'step' must be an integer")
            else:
                step_numbers.append(step_num)

        # Agent check
        agent = step.get("agent")
        if not agent:
            errors.append(f"{step_label}: missing required field 'agent'")
        elif agent not in VALID_AGENTS:
            errors.append(
                f"{step_label}: unknown agent '{agent}'. "
                f"Valid agents: {', '.join(sorted(VALID_AGENTS.keys()))}"
            )
        else:
            agents_used.add(agent)

            # Action check (only if agent is valid)
            action = step.get("action")
            if not action:
                errors.append(f"{step_label}: missing required field 'action'")
            elif action not in VALID_AGENTS[agent]:
                errors.append(
                    f"{step_label}: unknown action '{action}' for agent '{agent}'. "
                    f"Valid actions: {', '.join(VALID_AGENTS[agent])}"
                )

        # Parameters check
        if "parameters" not in step:
            warnings.append(f"{step_label}: no 'parameters' defined")
        else:
            params = step.get("parameters", {})
            if isinstance(params, dict):
                # File existence checks for filesystem agent paths
                if agent == "filesystem" and isinstance(params.get("path"), str):
                    ref_path = Path(params["path"])
                    action = step.get("action", "")
                    # Only warn for read/exists/stat actions (write creates files)
                    if action in ("read", "stat") and not ref_path.exists():
                        warnings.append(
                            f"{step_label}: referenced path '{params['path']}' does not exist"
                        )

    # 5. Step numbering validation
    if step_numbers:
        expected = list(range(1, len(steps) + 1))
        if sorted(step_numbers) != expected:
            warnings.append(
                f"Step numbers {sorted(step_numbers)} "
                f"don't match expected sequence {expected}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "steps": len(steps),
        "agents_used": sorted(agents_used),
    }


def _display_validation_result(result: Dict[str, Any], filepath: Path) -> None:
    """Display validation result as a Rich panel."""
    success_color = get_theme_color("success")
    error_color = get_theme_color("error")
    warning_color = get_theme_color("warning")

    lines = []

    if result["valid"]:
        lines.append(f"[bold {success_color}]✓ Workflow is valid[/]\n")
    else:
        lines.append(f"[bold {error_color}]✗ Workflow has errors[/]\n")

    lines.append(f"  File:   {filepath}")
    lines.append(f"  Steps:  {result['steps']}")
    if result["agents_used"]:
        lines.append(f"  Agents: {', '.join(result['agents_used'])}")

    if result["errors"]:
        lines.append(f"\n[bold {error_color}]Errors:[/]")
        for err in result["errors"]:
            lines.append(f"  [{error_color}]✗[/] {err}")

    if result["warnings"]:
        lines.append(f"\n[bold {warning_color}]Warnings:[/]")
        for warn in result["warnings"]:
            lines.append(f"  [{warning_color}]⚠[/] {warn}")

    title = "✓ Workflow Valid" if result["valid"] else "✗ Workflow Invalid"
    color = success_color if result["valid"] else error_color
    print_panel(title, "\n".join(lines), style=color)