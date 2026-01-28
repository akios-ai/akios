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
from pathlib import Path

from ...core.runtime.output.manager import get_output_manager
from ..helpers import CLIError, output_result, handle_cli_error, check_project_context


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
                    output_result({"workflow": args.workflow, "outputs": []}, format_json=True)
                else:
                    print(f"No outputs found for workflow '{args.workflow}'")
                return 0

            if args.json:
                output_result({
                    "workflow": args.workflow,
                    "outputs": outputs
                }, format_json=True)
            else:
                print(f"Outputs for workflow '{args.workflow}':")
                for output in outputs:
                    size_mb = output['total_size'] / (1024 * 1024)
                    print(f"  • {output['execution_id']} - {output['file_count']} files, {size_mb:.1f} MB")

        else:
            # List all workflow outputs
            all_outputs = manager.get_all_outputs()

            if args.json:
                output_result({"workflows": all_outputs}, json_mode=True)
            else:
                if not all_outputs:
                    print("No workflow outputs found")
                else:
                    print("Workflow Outputs:")
                    for workflow, outputs in all_outputs.items():
                        print(f"  {workflow}/ ({len(outputs)} executions)")
                        for output in outputs[:3]:  # Show latest 3
                            size_mb = output['total_size'] / (1024 * 1024)
                            print(f"    • {output['execution_id']} - {output['file_count']} files, {size_mb:.1f} MB")
                        if len(outputs) > 3:
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
            output_result(result, format_json=True)
        else:
            action = "Would clean" if args.dry_run else "Cleaned"
            size_mb = result['size_freed'] / (1024 * 1024)
            print(f"{action} {result['cleaned']} execution(s) from '{args.workflow}'")
            print(f"  • Scanned: {result['scanned']} total executions")
            print(f"  • Space freed: {size_mb:.1f} MB")

            if args.dry_run:
                print("\nUse --dry-run=false to actually perform cleanup")

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
            }, format_json=True)
        else:
            print(f"✅ Archived outputs for workflow '{args.workflow}'")
            print(f"   Archive: {archive_path}")

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
    print("AKIOS Output Management")
    print("=======================")
    print()
    print("Manage workflow outputs with organization and cleanup capabilities.")
    print()
    print("Commands:")
    print("  list [workflow]              List workflow outputs")
    print("  clean <workflow>             Clean old workflow outputs")
    print("  archive <workflow>           Archive workflow outputs")
    print()
    print("Examples:")
    print("  akios output list                           # List all workflow outputs")
    print("  akios output list fraud-detection          # List specific workflow")
    print("  akios output clean fraud-detection --dry-run # Preview cleanup")
    print("  akios output archive fraud-detection       # Create archive")

    return 0