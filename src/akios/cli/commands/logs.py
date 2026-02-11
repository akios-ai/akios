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
CLI logs command - akios logs

Show recent logs for a task.
"""

import argparse
from typing import Optional

from ...core.audit.ledger import get_ledger
from ...core.ui.rich_output import _get_console
from ..helpers import CLIError, output_result, format_logs_info, check_project_context
from ..rich_helpers import output_with_mode


def register_logs_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the logs command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "logs",
        help="Show recent logs"
    )

    parser.add_argument(
        "--task",
        "-t",
        help="Task/workflow ID to show logs for (default: show all recent)"
    )

    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=10,
        help="Number of log entries to show (default: 10)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    parser.set_defaults(func=run_logs_command)


def run_logs_command(args: argparse.Namespace) -> int:
    """
    Execute the logs command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()
        logs_data = get_logs_data(task_id=args.task, limit=args.limit)

        if args.json:
            output_result(logs_data, json_mode=True)
        else:
            # Display logs via output_with_mode
            if logs_data.get('events'):
                details = [f"Total events: {len(logs_data['events'])}"]
                if args.task:
                    details.insert(0, f"Filtering for task: {args.task}")
                output_with_mode(
                    message="Recent logs retrieved",
                    details=details,
                    output_type="info",
                    json_mode=False
                )
                # Print the actual formatted logs
                formatted = format_logs_info(logs_data)
                console = _get_console()
                if console:
                    console.print(formatted)
                else:
                    print(formatted)
            else:
                output_with_mode(
                    message="No logs found",
                    output_type="info",
                    json_mode=False
                )

        return 0

    except CLIError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return e.exit_code
    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def get_logs_data(task_id: str = None, limit: int = 10) -> dict:
    """
    Get logs data for display.

    Args:
        task_id: Optional task/workflow ID filter
        limit: Maximum number of entries to return

    Returns:
        Dict with logs data
    """
    if limit <= 0:
        raise CLIError(f"Limit must be positive, got {limit}", exit_code=2)
    if limit > 1000:
        raise CLIError(f"Limit too large (max 1000), got {limit}", exit_code=2)

    try:
        ledger = get_ledger()
        all_events = ledger.get_all_events()

        # Filter by task if specified
        if task_id:
            filtered_events = [
                event for event in all_events
                if event.workflow_id == task_id
            ]
        else:
            filtered_events = all_events

        # Get most recent events up to limit
        recent_events = filtered_events[-limit:]

        # Convert events to dict format
        events_data = []
        for event in recent_events:
            events_data.append({
                "workflow_id": event.workflow_id,
                "step": event.step,
                "agent": event.agent,
                "action": event.action,
                "result": event.result,
                "timestamp": event.timestamp,
                "hash": event.hash[:8] + "..."  # Short hash for display
            })

        return {
            "events": events_data,
            "total_events": len(filtered_events),
            "shown_events": len(events_data),
            "task_filter": task_id
        }

    except Exception as e:
        raise CLIError(f"Failed to retrieve logs: {e}", exit_code=1) from e
