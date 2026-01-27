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
CLI commands module - Registry and base classes for CLI commands.

Groups all commands together for the main CLI dispatcher.
"""

import argparse
from typing import Dict, Callable, Any

# Lazy import commands for performance optimization
_command_modules = {}

def _import_command_module(module_name: str):
    """Direct import a command module for PyInstaller compatibility"""
    # Direct imports for reliable binary builds
    module = __import__(f'akios.cli.commands.{module_name}',
                       fromlist=[f'register_{module_name}_command'])
    return module


def register_all_commands(subparsers: argparse._SubParsersAction) -> None:
    """
    Register all CLI commands with the argument parser using lazy loading for performance.

    Args:
        subparsers: Subparsers action from main parser
    """
    # Register each command with lazy loading
    init_module = _import_command_module('init')
    init_module.register_init_command(subparsers)

    run_module = _import_command_module('run')
    run_module.register_run_command(subparsers)

    audit_module = _import_command_module('audit')
    audit_module.register_audit_command(subparsers)

    logs_module = _import_command_module('logs')
    logs_module.register_logs_command(subparsers)

    status_module = _import_command_module('status')
    status_module.register_status_command(subparsers)

    templates_module = _import_command_module('templates')
    templates_module.register_templates_command(subparsers)

    clean_module = _import_command_module('clean')
    clean_module.register_clean_command(subparsers)

    testing_module = _import_command_module('testing')
    testing_module.register_testing_command(subparsers)

    setup_module = _import_command_module('setup')
    setup_module.register_setup_command(subparsers)

    doctor_module = _import_command_module('doctor')
    doctor_module.register_doctor_command(subparsers)

    files_module = _import_command_module('files')
    files_module.register_files_command(subparsers)

    compliance_module = _import_command_module('compliance')
    compliance_module.register_compliance_command(subparsers)

    output_module = _import_command_module('output')
    output_module.register_output_command(subparsers)

    # workflow_module = _lazy_import_command('workflow')
    # workflow_module.register_workflow_command(subparsers)  # Removed for v1.0.0 minimal scope


def get_command_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all commands.

    Returns:
        Dict mapping command names to descriptions
    """
    return {
        "init": "Create minimal project structure (config, example template)",
        "run": "Execute a workflow",
        "audit": "Export audit reports",
        "logs": "Show recent logs",
        "status": "Show current status and last run summary",
        "templates": "Manage workflow templates",
        "clean": "Clean up old workflow runs and data",
        "testing": "View environment notes and testing context",
        "setup": "Interactive setup wizard for first-time configuration",
        "doctor": "Run diagnostics and security checks",
        "files": "Show available input and output files",
        "compliance": "Generate compliance reports",
        "output": "Manage workflow outputs",
        # "workflow": "Manage workflow instances"  # Removed for v1.0.0 minimal scope
    }


__all__ = ["register_all_commands", "get_command_descriptions"]
