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
Environment command - View environment notes and testing context.

Provides helpful context about your testing environment, detected capabilities,
and environmental constraints during AKIOS usage.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from ...core.ui.rich_output import print_panel, print_table, print_success, print_error, print_warning


def show_notes(args):
    """Display environment notes and testing context."""
    try:
        from ..helpers import check_project_context
        check_project_context()
        from ...testing.tracker import get_testing_tracker
        tracker = get_testing_tracker()

        issues = tracker.issues

        # Apply filters
        if hasattr(args, 'category') and args.category:
            issues = [i for i in issues if i.get('category') == args.category]
        if hasattr(args, 'severity') and args.severity:
            issues = [i for i in issues if i.get('severity') == args.severity]
        if hasattr(args, 'auto_only') and args.auto_only:
            issues = [i for i in issues if i.get('auto_detected', False)]

        format_type = getattr(args, 'format', 'table')

        if format_type == 'json':
            print(json.dumps({
                'issues': issues,
                'summary': tracker.get_summary()
            }, indent=2, default=str))

        elif format_type == 'summary':
            summary = tracker.get_summary()
            
            content = f"Environment Notes: {summary['unique_issues']}\n"
            content += f"Total Observations: {summary['total_occurrences']}\n"
            content += f"Session Duration: {summary['session_duration']:.1f}s\n"
            content += f"Platform: {summary['platform_info']['system']} {summary['platform_info']['release']}\n\n"
            
            content += "[bold]By Type (Environment Notes):[/bold]\n"
            for sev, count in summary['by_severity'].items():
                content += f"  {sev.capitalize()}: {count}\n"
            
            content += "\n[bold]By Category:[/bold]\n"
            for cat, count in summary['by_category'].items():
                content += f"  {cat.capitalize()}: {count}\n"
                
            print_panel("Environment & Testing Notes Summary", content)

        else:  # table format
            if not issues:
                print_success("Environment fully compatible - no special notes.")
                return

            # Prepare table data
            issues_data = []
            for issue in issues:
                severity_icon = {
                    'minor': '🟡',
                    'important': '🟠',
                    'critical': '🔴'
                }.get(issue.get('severity'), '⚪')
                
                auto_marker = "[AUTO]" if issue.get('auto_detected') else "[MANUAL]"
                occurrence_count = issue.get('occurrence_count', 1)
                occurrence_info = f" (x{occurrence_count})" if occurrence_count > 1 else ""
                
                issues_data.append({
                    "severity": severity_icon,
                    "type": auto_marker,
                    "title": issue.get('title', 'Unknown') + occurrence_info,
                    "category": issue.get('category', 'unknown').capitalize(),
                    "description": issue.get('description', 'No description')[:50] + "..."
                })
            
            if issues_data:
                print_table(issues_data, title="📋 Environment & Testing Notes",
                           columns=["severity", "type", "title", "category", "description"])

    except ImportError:
        print_error("Testing tracker not available.")
        sys.exit(1)


def clear_notes(args):
    """Clear all logged environment notes."""
    try:
        from ..helpers import check_project_context
        check_project_context()
        from ...testing.tracker import get_testing_tracker
        tracker = get_testing_tracker()

        issue_count = len(tracker.issues)
        tracker.issues.clear()
        tracker._save_issues()

        print_success(f"Cleared {issue_count} environment notes.")

    except ImportError:
        print_error("Testing tracker not available.")
        sys.exit(1)


def log_issue(args):
    """Manually log a testing issue."""
    try:
        from ..helpers import check_project_context
        check_project_context()
        from ...testing.tracker import get_testing_tracker
        tracker = get_testing_tracker()

        tracker.log_issue(
            category=getattr(args, 'category', 'manual'),
            severity=getattr(args, 'severity', 'minor'),
            title=args.title,
            description=args.description,
            impact=getattr(args, 'impact', ''),
            recommendation=getattr(args, 'recommendation', ''),
            auto_detected=False
        )

        print_success("Testing issue logged manually.")

    except ImportError:
        print_error("Testing tracker not available.")
        sys.exit(1)


def register_testing_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the testing command with the CLI parser."""
    testing_parser = subparsers.add_parser(
        "testing",
        help="View environment notes and testing context",
        description="Environment notes and testing context management."
    )

    # Add subcommands for testing
    testing_subparsers = testing_parser.add_subparsers(
        dest="testing_command",
        help="Testing subcommands",
        metavar="SUBCOMMAND",
        required=False
    )

    # Notes subcommand
    notes_parser = testing_subparsers.add_parser(
        "show-notes",
        aliases=["notes"],
        help="Display environment notes and testing context"
    )
    notes_parser.add_argument(
        "--format",
        type=str,
        choices=["table", "json", "summary"],
        default="table",
        help="Output format"
    )
    notes_parser.add_argument(
        "--category",
        help="Filter by category"
    )
    notes_parser.add_argument(
        "--severity",
        type=str,
        choices=["minor", "important", "critical"],
        help="Filter by severity level"
    )
    notes_parser.add_argument(
        "--auto-only",
        action="store_true",
        help="Show only auto-detected notes"
    )
    notes_parser.set_defaults(func=show_notes)

    # Set default to notes when no subcommand provided
    testing_parser.set_defaults(func=show_notes)

    # Clear subcommand
    clear_parser = testing_subparsers.add_parser(
        "clear-notes",
        aliases=["clear"],
        help="Clear all logged environment notes"
    )
    clear_parser.set_defaults(func=clear_notes)

    # Log subcommand
    log_parser = testing_subparsers.add_parser(
        "log-issue",
        aliases=["log"],
        help="Manually log a testing issue"
    )
    log_parser.add_argument(
        "title",
        help="Issue title"
    )
    log_parser.add_argument(
        "--category",
        default="manual",
        help="Issue category"
    )
    log_parser.add_argument(
        "--severity",
        type=str,
        choices=["minor", "important", "critical"],
        default="minor",
        help="Issue severity"
    )
    log_parser.add_argument(
        "--description",
        required=True,
        help="Issue description"
    )
    log_parser.add_argument(
        "--impact",
        help="Impact description"
    )
    log_parser.add_argument(
        "--recommendation",
        help="Recommendation"
    )
    log_parser.set_defaults(func=log_issue)

    testing_parser.set_defaults(func=show_notes)
