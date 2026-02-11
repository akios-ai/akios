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
UI utilities for command suggestions and user guidance.

This module provides context-aware command suggestions that adapt
to the deployment environment (Docker vs Native Linux).
"""

import os


def get_command_prefix() -> str:
    """
    Get the appropriate command prefix based on deployment mode.

    Returns:
        str: "./akios" for Docker mode, "akios" for native Linux mode
    """
    # Check env var first (set by Docker wrapper script)
    if os.environ.get('AKIOS_DOCKER_WRAPPER') == '1':
        return "./akios"

    # Check container marker files
    docker_indicators = [
        '/.dockerenv',
        '/run/.containerenv'
    ]
    if any(os.path.exists(indicator) for indicator in docker_indicators):
        return "./akios"

    return "akios"


def suggest_command(command: str) -> str:
    """
    Generate a context-aware command suggestion.

    Args:
        command: The command without prefix (e.g., "setup --force")

    Returns:
        str: Full command with appropriate prefix
    """
    prefix = get_command_prefix()
    return f"{prefix} {command}"


# Common command suggestions
SETUP_COMMAND = suggest_command("setup")
HELLO_WORKFLOW_COMMAND = suggest_command("run templates/hello-workflow.yml")
DOCUMENT_INGESTION_COMMAND = suggest_command("run templates/document_ingestion.yml")
BATCH_PROCESSING_COMMAND = suggest_command("run templates/batch_processing.yml")
FILE_ANALYSIS_COMMAND = suggest_command("run templates/file_analysis.yml")
STATUS_COMMAND = suggest_command("status")
HELP_COMMAND = suggest_command("--help")
TEMPLATES_LIST_COMMAND = suggest_command("templates list")
