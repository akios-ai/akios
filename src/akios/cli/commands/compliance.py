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
CLI compliance command - akios compliance <subcommand>

Compliance reporting and status dashboard for v1.0.0 workflow isolation.
"""

import argparse

from ...core.compliance.report import get_compliance_generator
from ..helpers import CLIError, output_result, handle_cli_error


def register_compliance_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the compliance command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "compliance",
        help="Generate compliance reports",
        description="Generate compliance reports and view compliance status"
    )

    subparsers_compliance = parser.add_subparsers(
        dest="compliance_subcommand",
        help="Compliance subcommands",
        required=False
    )

    # compliance report
    report_parser = subparsers_compliance.add_parser(
        "report",
        help="Generate compliance report for a workflow"
    )
    report_parser.add_argument(
        "workflow",
        help="Workflow name to generate report for"
    )
    report_parser.add_argument(
        "--type",
        choices=["basic", "detailed", "executive"],
        default="basic",
        help="Type of compliance report (default: basic)"
    )
    report_parser.add_argument(
        "--format",
        choices=["json", "txt"],
        default="json",
        help="Export format (default: json)"
    )
    report_parser.add_argument(
        "--output",
        help="Output filename (optional - auto-generated if not specified)"
    )
    report_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    report_parser.set_defaults(func=run_compliance_report)

    # Default handler for no subcommand
    parser.set_defaults(func=run_compliance_help)


def run_compliance_report(args: argparse.Namespace) -> int:
    """
    Execute the compliance report command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        from ..helpers import check_project_context
        check_project_context()
        generator = get_compliance_generator()

        # Generate the report
        report = generator.generate_report(
            workflow_name=args.workflow,
            report_type=args.type
        )

        # Export if requested
        if args.format != "json" or args.output:
            export_path = generator.export_report(
                report=report,
                format=args.format,
                output_file=args.output
            )

            if args.json:
                output_result({
                    "workflow": args.workflow,
                    "report_type": args.type,
                    "export_format": args.format,
                    "export_path": export_path,
                    "status": "exported"
                }, json_mode=True)
            else:
                print(f"✅ Generated compliance report for workflow '{args.workflow}'")
                print(f"   Report Type: {args.type}")
                print(f"   Export Format: {args.format}")
                print(f"   File: {export_path}")

                # Show key metrics
                score = report.get('compliance_score', {})
                print(f"   Compliance Score: {score.get('overall_score', 'N/A')}/5.0 ({score.get('overall_level', 'unknown')})")
        else:
            # Just display the report
            if args.json:
                output_result(report, json_mode=True)
            else:
                # Show summary
                metadata = report.get('report_metadata', {})
                score = report.get('compliance_score', {})

                print(f"Compliance Report for '{args.workflow}'")
                print(f"Generated: {metadata.get('generated_at', 'unknown')}")
                print(f"Report Type: {args.type}")
                print()
                print(f"Overall Score: {score.get('overall_score', 'N/A')}/5.0 ({score.get('overall_level', 'unknown')})")
                print()

                # Show component scores
                components = score.get('component_scores', {})
                print("Component Scores:")
                print(f"  Security: {components.get('security', 'N/A')}/5.0")
                print(f"  Audit: {components.get('audit', 'N/A')}/5.0")
                print(f"  Cost: {components.get('cost', 'N/A')}/5.0")

        return 0

    except CLIError as e:
        return handle_cli_error(e, json_mode=args.json)
    except Exception as e:
        return handle_cli_error(e, json_mode=args.json)


def run_compliance_help(args: argparse.Namespace) -> int:
    """
    Show compliance command help.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    print("AKIOS Compliance Reporting")
    print("==========================")
    print()
    print("Generate compliance reports and view compliance status for workflows.")
    print()
    print("Commands:")
    print("  report <workflow>        Generate compliance report")
    print()
    print("Report Types:")
    print("  basic      - Cost, audit, and security compliance summary")
    print("  detailed   - Includes execution breakdown and model usage")
    print("  executive  - High-level compliance overview")
    print()
    print("Export Formats:")
    print("  json       - Structured JSON format")
    print("  txt        - Human-readable text format")
    print()
    print("Examples:")
    print("  akios compliance report fraud-detection                    # Basic JSON report")
    print("  akios compliance report fraud-detection --type detailed   # Detailed analysis")
    print("  akios compliance report fraud-detection --format txt      # Text export")

    return 0
