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
            print("📋 Environment & Testing Notes Summary")
            print("=" * 50)
            print(f"Environment Notes: {summary['unique_issues']}")
            print(f"Total Observations: {summary['total_occurrences']}")
            print(f"Session Duration: {summary['session_duration']:.1f}s")
            print(f"Platform: {summary['platform_info']['system']} {summary['platform_info']['release']}")

            print(f"\nBy Type (Environment Notes):")
            for sev, count in summary['by_severity'].items():
                print(f"  {sev.capitalize()}: {count}")

            print(f"\nBy Category:")
            for cat, count in summary['by_category'].items():
                print(f"  {cat.capitalize()}: {count}")

        else:  # table format
            if not issues:
                print("✅ Environment fully compatible - no special notes.")
                return

            print("📋 Environment & Testing Notes")
            print("=" * 80)
            print("💡 These notes help you understand your current setup:")
            print()

            for i, issue in enumerate(issues, 1):
                auto_marker = "[AUTO]" if issue.get('auto_detected') else "[MANUAL]"
                severity_marker = {
                    'minor': '🟡',
                    'important': '🟠',
                    'critical': '🔴'
                }.get(issue.get('severity'), '⚪')

                # Show occurrence count for duplicate issues
                occurrence_count = issue.get('occurrence_count', 1)
                occurrence_info = f" (x{occurrence_count})" if occurrence_count > 1 else ""

                print(f"{i}. {severity_marker} {auto_marker} {issue.get('title', 'Unknown')}{occurrence_info}")
                print(f"   Category: {issue.get('category', 'unknown').capitalize()}")
                print(f"   Severity: {issue.get('severity', 'unknown').capitalize()}")
                print(f"   Description: {issue.get('description', 'No description')}")
                if issue.get('impact'):
                    print(f"   Impact: {issue.get('impact')}")
                if issue.get('recommendation'):
                    print(f"   Recommendation: {issue.get('recommendation')}")
                print()

    except ImportError:
        print("❌ Testing tracker not available.", file=sys.stderr)
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

        print(f"✅ Cleared {issue_count} environment notes.")

    except ImportError:
        print("❌ Testing tracker not available.", file=sys.stderr)
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

        print("✅ Testing issue logged manually.")

    except ImportError:
        print("❌ Testing tracker not available.", file=sys.stderr)
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
        required=True
    )

    # Notes subcommand
    notes_parser = testing_subparsers.add_parser(
        "notes",
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

    # Clear subcommand
    clear_parser = testing_subparsers.add_parser(
        "clear",
        help="Clear all logged environment notes"
    )
    clear_parser.set_defaults(func=clear_notes)

    # Log subcommand
    log_parser = testing_subparsers.add_parser(
        "log",
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
