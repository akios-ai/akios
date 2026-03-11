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
CLI templates command - akios templates list

List available workflow templates with descriptions.
"""

import argparse
from pathlib import Path

from ..helpers import CLIError, output_result, check_project_context
from ..template_picker import run_template_picker
from ...core.ui.rich_output import get_theme_color


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

    # templates select subcommand with fuzzy search
    select_parser = subparsers_templates.add_parser(
        "select",
        help="Interactively select a template"
    )

    select_parser.add_argument(
        "--no-search",
        action="store_true",
        help="Disable fuzzy search"
    )

    select_parser.add_argument(
        "--json",
        action="store_true",
        help="Output selected template in JSON format"
    )

    select_parser.set_defaults(func=run_templates_select)


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
            # Prepare data for table
            table_data = []
            for t in templates_data:
                badge = f"[{get_theme_color('info')}]🌐[/{get_theme_color('info')}]" if t.get("network_required", True) else f"[{get_theme_color('success')}]💾[/{get_theme_color('success')}]"
                table_data.append({
                    "Type": badge,
                    "Template": f"[bold]{t['name']}[/bold]",
                    "Description": t["description"]
                })
            
            from ...core.ui.rich_output import print_table
            print_table(table_data, title="Available Templates")

        return 0

    except CLIError as e:
        from ...core.ui.rich_output import print_error
        print_error(str(e))
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


def format_templates_list(templates: list) -> str:
    """
    Format templates list into a human-readable string.

    Args:
        templates: List of template dictionaries with name/description

    Returns:
        Formatted templates string
    """
    lines = []
    lines.append("Available Templates")
    lines.append("=" * 19)
    lines.append("")

    emoji_map = {
        "hello-workflow.yml": "👋",
        "document_ingestion.yml": "📄",
        "batch_processing.yml": "⚙️",
        "file_analysis.yml": "🔍",
    }

    for template in templates:
        name = template.get("name", "unknown.yml")
        description = template.get("description", "")
        emoji = emoji_map.get(name, "📋")
        lines.append(f"{emoji} {name}  {description}")

    return "\n".join(lines)


def run_templates_select(args: argparse.Namespace) -> int:
    """
    Execute the templates select command.
    
    Launches interactive template picker with fuzzy search.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()
        templates_data = get_templates_list()

        # Run interactive picker
        enable_search = not args.no_search
        selected = run_template_picker(templates_data, enable_search=enable_search)

        if selected:
            if args.json:
                output_result(selected, json_mode=True)
            else:
                from ...core.ui.rich_output import print_panel
                content = f"Template: [bold]{selected['name']}[/bold]\n"
                content += f"Description: [dim]{selected.get('description', 'N/A')}[/dim]"
                print_panel("Template Selected", content)
            return 0
        else:
            # User cancelled selection
            if not args.json:
                from ...core.ui.rich_output import print_warning
                print_warning("No template selected.")
            return 1

    except CLIError as e:
        from ...core.ui.rich_output import print_error
        print_error(str(e))
        return e.exit_code
    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)

# format_templates_list removed in favor of rich_output.print_table
