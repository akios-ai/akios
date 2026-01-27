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
CLI audit command - akios audit export

Export audit reports in PDF or JSON format.
"""

import argparse
from pathlib import Path

from ...core.audit import export_audit_json
from ..helpers import CLIError, output_result, validate_file_path, check_project_context


def register_audit_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the audit command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "audit",
        help="Export audit reports"
    )

    subparsers_audit = parser.add_subparsers(
        dest="audit_subcommand",
        help="Audit subcommands",
        required=True
    )

    # audit export subcommand
    export_parser = subparsers_audit.add_parser(
        "export",
        help="Export audit report"
    )

    export_parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
        help="Export format (default: json)"
    )

    export_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: auto-generated)"
    )

    export_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format (for status/info)"
    )

    export_parser.set_defaults(func=run_audit_export_command)


def run_audit_export_command(args: argparse.Namespace) -> int:
    """
    Execute the audit export command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()

        if args.audit_subcommand == "export":
            result = export_audit_report(
                format_type=args.format,
                output_path=args.output
            )

            output_result(
                result,
                json_mode=args.json,
                success_message=f"Audit exported to {result.get('output_file', 'unknown')}"
            )
            return 0

        else:
            raise CLIError("Unknown audit subcommand", exit_code=2)

    except CLIError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return e.exit_code
    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def export_audit_report(format_type: str, output_path: str = None) -> dict:
    """
    Export audit report.

    Args:
        format_type: Export format ('json' only)
        output_path: Optional output file path

    Returns:
        Dict with export results

    Raises:
        CLIError: If export fails or unsupported format
    """
    try:
        if format_type == "json":
            # Export as JSON
            if output_path is None:
                # Generate default filename
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"audit_export_{timestamp}.json"

            result = export_audit_json(output_file=output_path)

        else:
            raise CLIError(f"Unsupported format: {format_type}. Only 'json' format is supported.", exit_code=2)

        return result

    except Exception as e:
        raise CLIError(f"Audit export failed: {e}", exit_code=1) from e
