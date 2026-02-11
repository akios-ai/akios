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
CLI output command - akios output <subcommand>

Enhanced output management for workflow isolation.
List, clean, and archive workflow outputs.
"""

import argparse
import json
import os
from pathlib import Path

try:
    from rich.console import Console
    _console = Console()
except ImportError:
    _console = None

from ...core.runtime.output.manager import get_output_manager
from ...core.ui.rich_output import print_panel, get_theme_color
from ..helpers import CLIError, output_result, handle_cli_error, check_project_context
from ..rich_helpers import output_with_mode, is_json_mode


def register_output_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the output command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "output",
        help="Manage workflow outputs",
        description="List, clean, and archive workflow outputs"
    )

    subparsers_output = parser.add_subparsers(
        dest="output_subcommand",
        help="Output subcommands",
        required=False
    )

    # output list
    list_parser = subparsers_output.add_parser(
        "list",
        help="List workflow outputs"
    )
    list_parser.add_argument(
        "workflow",
        nargs="?",
        help="Workflow name (optional - shows all if not specified)"
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    list_parser.set_defaults(func=run_output_list)

    # output latest
    latest_parser = subparsers_output.add_parser(
        "latest",
        help="Get the most recent workflow output in JSON"
    )
    latest_parser.set_defaults(func=run_output_latest)

    # output clean
    clean_parser = subparsers_output.add_parser(
        "clean",
        help="Clean old workflow outputs"
    )
    clean_parser.add_argument(
        "workflow",
        help="Workflow name"
    )
    clean_parser.add_argument(
        "--max-age",
        type=int,
        default=30,
        help="Maximum age in days (default: 30)"
    )
    clean_parser.add_argument(
        "--max-count",
        type=int,
        default=50,
        help="Maximum executions to keep (default: 50)"
    )
    clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without actually cleaning"
    )
    clean_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    clean_parser.set_defaults(func=run_output_clean)

    # output archive
    archive_parser = subparsers_output.add_parser(
        "archive",
        help="Archive workflow outputs"
    )
    archive_parser.add_argument(
        "workflow",
        help="Workflow name"
    )
    archive_parser.add_argument(
        "--name",
        help="Archive filename (optional - auto-generated if not specified)"
    )
    archive_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    archive_parser.set_defaults(func=run_output_archive)

    # Default handler for no subcommand
    parser.set_defaults(func=run_output_help)


def run_output_list(args: argparse.Namespace) -> int:
    """
    Execute the output list command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()
        manager = get_output_manager()

        if args.workflow:
            # List specific workflow outputs
            outputs = manager.get_workflow_outputs(args.workflow)
            if not outputs:
                if args.json:
                    output_result({"workflow": args.workflow, "outputs": []}, json_mode=True)
                else:
                    output_with_mode(
                        message=f"No outputs found for workflow '{args.workflow}'",
                        json_mode=False,
                        quiet_mode=False,
                        output_type="info"
                    )
                return 0

            if args.json:
                output_result({
                    "workflow": args.workflow,
                    "outputs": outputs
                }, json_mode=True)
            else:
                output_with_mode(
                    message=f"Outputs for workflow '[{get_theme_color('info')}]{args.workflow}[/{get_theme_color('info')}]'",
                    json_mode=False,
                    quiet_mode=False,
                    output_type="info"
                )
                for output in outputs:
                    size_mb = output['total_size'] / (1024 * 1024)
                    if _console:
                        _console.print(f"  [{get_theme_color('info')}]•[/{get_theme_color('info')}] [bold]{output['execution_id']}[/bold] [dim]-[/dim] [{get_theme_color('info')}]{output['file_count']} files[/{get_theme_color('info')}], [{get_theme_color('warning')}]{size_mb:.1f} MB[/{get_theme_color('warning')}]")
                    else:
                        print(f"  • {output['execution_id']} - {output['file_count']} files, {size_mb:.1f} MB")
        else:
            # List all workflow outputs
            all_outputs = manager.get_all_outputs()

            if args.json:
                output_result({"workflows": all_outputs}, json_mode=True)
            else:
                if not all_outputs:
                    output_with_mode(
                        message="No workflow outputs found",
                        json_mode=False,
                        quiet_mode=False,
                        output_type="info"
                    )
                else:
                    output_with_mode(
                        message="Workflow Outputs",
                        json_mode=False,
                        quiet_mode=False,
                        output_type="info"
                    )
                    for workflow, outputs in all_outputs.items():
                        if _console:
                            _console.print(f"  [bold {get_theme_color('header')}]{workflow}/[/bold {get_theme_color('header')}] [dim]({len(outputs)} executions)[/dim]")
                        else:
                            print(f"  {workflow}/ ({len(outputs)} executions)")
                        for output in outputs[:3]:  # Show latest 3
                            size_mb = output['total_size'] / (1024 * 1024)
                            if _console:
                                _console.print(f"    [{get_theme_color('info')}]•[/{get_theme_color('info')}] [bold]{output['execution_id']}[/bold] [dim]-[/dim] [{get_theme_color('info')}]{output['file_count']} files[/{get_theme_color('info')}], [{get_theme_color('warning')}]{size_mb:.1f} MB[/{get_theme_color('warning')}]")
                            else:
                                print(f"    • {output['execution_id']} - {output['file_count']} files, {size_mb:.1f} MB")
                        if len(outputs) > 3:
                            if _console:
                                _console.print(f"    [dim]... and {len(outputs) - 3} more[/dim]")
                            else:
                                print(f"    ... and {len(outputs) - 3} more")

        return 0

    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def run_output_clean(args: argparse.Namespace) -> int:
    """
    Execute the output clean command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()
        manager = get_output_manager()

        result = manager.clean_workflow_outputs(
            workflow_name=args.workflow,
            max_age_days=args.max_age,
            max_count=args.max_count,
            dry_run=args.dry_run
        )

        if args.json:
            output_result(result, json_mode=True)
        else:
            action = "Would clean" if args.dry_run else "Cleaned"
            size_mb = result['size_freed'] / (1024 * 1024)
            details = [
                f"Scanned: {result['scanned']} total executions",
                f"Space freed: {size_mb:.1f} MB"
            ]
            if args.dry_run:
                details.append("Use --dry-run=false to actually perform cleanup")
            
            output_with_mode(
                message=f"{action} {result['cleaned']} execution(s) from '{args.workflow}'",
                details=details,
                json_mode=False,
                quiet_mode=False,
                output_type="success" if not args.dry_run else "info"
            )

        return 0

    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def run_output_archive(args: argparse.Namespace) -> int:
    """
    Execute the output archive command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()
        manager = get_output_manager()

        archive_path = manager.archive_workflow_outputs(
            workflow_name=args.workflow,
            archive_name=args.name
        )

        if args.json:
            output_result({
                "workflow": args.workflow,
                "archive_path": archive_path,
                "status": "created"
            }, json_mode=True)
        else:
            output_with_mode(
                message=f"Archived outputs for workflow '[{get_theme_color('info')}]{args.workflow}[/{get_theme_color('info')}]'",
                details=[f"Archive: [{get_theme_color('warning')}]{archive_path}[/{get_theme_color('warning')}]"],
                json_mode=False,
                quiet_mode=False,
                output_type="success"
            )

        return 0

    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def run_output_help(args: argparse.Namespace) -> int:
    """
    Show output command help.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    help_content = """Commands:
  list [workflow]              List workflow outputs
  clean <workflow>             Clean old workflow outputs
  archive <workflow>           Archive workflow outputs

Examples:
  akios output list                           # List all workflow outputs
  akios output list fraud-detection          # List specific workflow
  akios output clean fraud-detection --dry-run # Preview cleanup
  akios output archive fraud-detection       # Create archive"""

    print_panel(
        "AKIOS Output Management",
        "Manage workflow outputs with organization and cleanup capabilities.\n\n" + help_content,
        style=None
    )

    return 0


def run_output_latest(args: argparse.Namespace) -> int:
    """
    Execute the output latest command.
    """
    check_project_context()
    
    output_dir = Path("./data/output")
    if not output_dir.exists():
        raise CLIError("No output directory found")
        
    # Find all run directories
    runs = sorted([d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("run_")])
    
    if not runs:
        raise CLIError("No workflow runs found")
        
    latest_run = runs[-1]
    
    # Try to find a JSON output file
    # Usually outputs are in the run directory.
    # We look for the main output file.
    
    # Priority:
    # 1. output.json
    # 2. *.json (first one found)
    
    output_file = latest_run / "output.json"
    if not output_file.exists():
        json_files = list(latest_run.glob("*.json"))
        if json_files:
            output_file = json_files[0]
        else:
            raise CLIError(f"No JSON output found in {latest_run}")
            
    try:
        with open(output_file, "r") as f:
            data = json.load(f)
            
        # Print raw JSON for piping
        print(json.dumps(data, indent=2))
        return 0
        
    except Exception as e:
        raise CLIError(f"Failed to read output: {str(e)}")