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

Compliance reporting and status dashboard for workflow isolation.
"""

import argparse

try:
    from rich.console import Console
    _console = Console()
except ImportError:
    _console = None

from ...core.compliance.report import get_compliance_generator
from ...core.ui.rich_output import (
    print_panel, print_success, print_error, print_warning, print_info, get_theme_color
)
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

    # compliance eu-ai-act (v1.2.0-rc — requires EnforceCore)
    euaiact_parser = subparsers_compliance.add_parser(
        "eu-ai-act",
        help="Generate EU AI Act compliance report (requires EnforceCore)"
    )
    euaiact_parser.add_argument(
        "--organization",
        default="",
        help="Organization name for the report header"
    )
    euaiact_parser.add_argument(
        "--period",
        default="",
        help="Reporting period (e.g. 'Q1 2026')"
    )
    euaiact_parser.add_argument(
        "--format",
        choices=["html", "json"],
        default="json",
        help="Output format: html (rich report) or json (structured data)"
    )
    euaiact_parser.add_argument(
        "--output",
        help="Output file path (default: compliance_eu_ai_act.<format>)"
    )
    euaiact_parser.set_defaults(func=run_compliance_eu_ai_act)

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
                print_success(
                    message=f"Generated compliance report for workflow '{args.workflow}'",
                    details=[
                        f"Report Type: {args.type}",
                        f"Export Format: {args.format}",
                        f"File: {export_path}"
                    ]
                )
                
                # Show key metrics
                score = report.get('compliance_score', {})
                score_text = f"Compliance Score: {score.get('overall_score', 'N/A')}/5.0 ({score.get('overall_level', 'unknown')})"
                print_info(score_text)
        else:
            # Just display the report
            if args.json:
                output_result(report, json_mode=True)
            else:
                # Show summary
                metadata = report.get('report_metadata', {})
                score = report.get('compliance_score', {})
                
                # Prepare report content
                report_title = f"Compliance Report - {args.workflow}"
                report_content = f"""Generated: {metadata.get('generated_at', 'unknown')}
Report Type: {args.type}

Overall Score: {score.get('overall_score', 'N/A')}/5.0 ({score.get('overall_level', 'unknown')})

Component Scores:
  Security: {score.get('component_scores', {}).get('security', 'N/A')}/5.0
  Audit: {score.get('component_scores', {}).get('audit', 'N/A')}/5.0
  Cost: {score.get('component_scores', {}).get('cost', 'N/A')}/5.0"""
                
                print_panel(report_title, report_content, style=get_theme_color("info"))

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
    help_content = """Commands:
  report <workflow>        Generate compliance report

Report Types:
  basic      - Cost, audit, and security compliance summary
  detailed   - Includes execution breakdown and model usage
  executive  - High-level compliance overview

Export Formats:
  json       - Structured JSON format
  txt        - Human-readable text format

Examples:
  akios compliance report fraud-detection                    # Basic JSON report
  akios compliance report fraud-detection --type detailed    # Detailed analysis
  akios compliance report fraud-detection --format txt       # Text export"""

    print_panel(
        "AKIOS Compliance Reporting",
        "Generate compliance reports and view compliance status for workflows.\n\n" + help_content,
        style=get_theme_color("info")
    )

    return 0


def run_compliance_eu_ai_act(args: argparse.Namespace) -> int:
    """
    Generate EU AI Act compliance report using EnforceCore (v1.2.0-rc).

    Requires: pip install akios[enforcecore]
    """
    import json as _json
    try:
        from enforcecore.auditstore.reports.generator import ReportGenerator
        from enforcecore.auditstore.backends.jsonl import JSONLBackend
        from enforcecore.auditstore.core import AuditStore
    except ImportError:
        msg = "EU AI Act reports require EnforceCore: pip install 'akios[enforcecore]'"
        if getattr(args, "json", False):
            print(_json.dumps({"error": msg, "enforcecore_available": False}))
        else:
            print_warning(msg)
        return 1

    try:
        from ..helpers import check_project_context
        check_project_context()
    except Exception:
        pass  # Reports can run without project context

    try:
        # Load audit trail from AKIOS's JSONL backend
        from ....config import get_settings
        import os
        settings = get_settings()
        audit_path = os.path.join(settings.audit_storage_path, "audit_events.jsonl")

        backend = JSONLBackend(audit_path)
        store = AuditStore(backend=backend)
        generator = ReportGenerator(store)

        organization = args.organization or "AKIOS Deployment"
        period = args.period or "Current"
        fmt = getattr(args, "format", "json")

        report = generator.generate_eu_ai_act_report(
            organization=organization,
            period=period,
            format=fmt,
        )

        output_path = args.output or f"compliance_eu_ai_act.{fmt}"

        if fmt == "html":
            report.save(output_path)
            print_success(f"EU AI Act report saved: {output_path}")
        else:
            content = report.render()
            with open(output_path, "w") as f:
                f.write(content)
            print_success(f"EU AI Act report saved: {output_path}")

        return 0

    except Exception as e:
        print_error(f"Report generation failed: {e}")
        return 1
