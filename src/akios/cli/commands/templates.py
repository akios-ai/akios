"""
CLI templates command - akios templates list

List available workflow templates with descriptions.
"""

import argparse
from pathlib import Path

from ..helpers import CLIError, output_result, check_project_context


def register_templates_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the templates command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "templates",
        help="Manage workflow templates"
    )

    subparsers_templates = parser.add_subparsers(
        dest="templates_subcommand",
        help="Templates subcommands",
        required=True
    )

    # templates list subcommand
    list_parser = subparsers_templates.add_parser(
        "list",
        help="List available templates"
    )

    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    list_parser.set_defaults(func=run_templates_list)


def run_templates_list(args: argparse.Namespace) -> int:
    """
    Execute the templates list command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()
        templates_data = get_templates_list()

        if args.json:
            output_result(templates_data, json_mode=args.json)
        else:
            formatted = format_templates_list(templates_data)
            print(formatted)

        return 0

    except CLIError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return e.exit_code
    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def get_templates_list() -> list:
    """
    Get list of available templates with descriptions.

    Returns:
        List of template dictionaries
    """
    # Template descriptions based on the official documentation
    templates = [
        {
            "name": "hello-workflow.yml",
            "description": "Hello World Example - Basic AI workflow demonstration with LLM interaction",
            "network_required": True
        },
        {
            "name": "document_ingestion.yml",
            "description": "Document Analysis Pipeline - Processes documents with PII redaction and AI summarization",
            "network_required": True
        },
        {
            "name": "batch_processing.yml",
            "description": "Secure Batch Processing - Multi-file AI analysis with cost tracking and PII protection",
            "network_required": False
        },
        {
            "name": "file_analysis.yml",
            "description": "File Security Scanner - Analyzes files with security-focused AI insights",
            "network_required": False
        }
    ]

    return templates


def format_templates_list(templates_data: list) -> str:
    """
    Format templates list for display with terminal width awareness.

    Args:
        templates_data: List of template dictionaries

    Returns:
        Formatted string
    """
    import shutil
    terminal_width = shutil.get_terminal_size().columns

    lines = []
    lines.append("Available Templates")
    lines.append("=" * 19)

    for template in templates_data:
        name = template["name"]
        description = template["description"]
        network_required = template.get("network_required", True)

        # Add network requirement badge
        if network_required:
            badge = "🌐"
            network_note = " (requires network)"
        else:
            badge = "💾"
            network_note = " (local only)"

        # Calculate available space for description
        # badge (2) + space (1) + name (up to 25) + space (1) + description + network_note
        name_width = min(25, len(name))
        available_desc_width = terminal_width - 2 - 1 - name_width - 1 - len(network_note) - 5  # 5 for safety margin

        # Truncate description if too long
        if len(description) > available_desc_width and available_desc_width > 10:
            truncated_desc = description[:available_desc_width-3] + "..."
        else:
            truncated_desc = description

        lines.append(f"{badge} {name:<{name_width}} {truncated_desc}{network_note}")

    return "\n".join(lines)
