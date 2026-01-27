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
    # Check if we're in a container environment (Docker)
    docker_indicators = [
        '/.dockerenv',
        '/run/.containerenv'
    ]

    is_docker = any(os.path.exists(indicator) for indicator in docker_indicators)

    if is_docker:
        return "./akios"
    else:
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
SETUP_COMMAND = suggest_command("setup --force")
HELLO_WORKFLOW_COMMAND = suggest_command("run templates/hello-workflow.yml")
DOCUMENT_INGESTION_COMMAND = suggest_command("run templates/document_ingestion.yml")
BATCH_PROCESSING_COMMAND = suggest_command("run templates/batch_processing.yml")
FILE_ANALYSIS_COMMAND = suggest_command("run templates/file_analysis.yml")
STATUS_COMMAND = suggest_command("status")
HELP_COMMAND = suggest_command("--help")
TEMPLATES_LIST_COMMAND = suggest_command("templates list")
