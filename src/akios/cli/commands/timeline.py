"""
Timeline command for workflow execution visualization.

Displays beautiful ASCII timeline of workflow step execution with
bottleneck analysis and performance metrics.

Usage:
    akios timeline latest          # Show timeline of latest run
    akios timeline --list          # List available timelines
    akios timeline run-001         # Show specific run
    akios timeline latest --json   # JSON output
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from akios.cli.helpers import CLIError
from akios.cli.rich_helpers import output_with_mode
from akios.core.ui.rich_output import print_panel, print_error
from akios.cli.timeline_visualizer import (
    render_timeline,
    render_timeline_file,
    compare_timelines,
    get_timeline_summary,
)


def register_timeline_command(subparsers) -> None:
    """
    Register timeline command with argument parser.
    
    Args:
        subparsers: Argparse subparsers object
    """
    parser = subparsers.add_parser(
        'timeline',
        help='View workflow execution timeline with performance analysis',
        description='Display ASCII timeline visualization of workflow execution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  akios timeline latest              Show timeline of latest run
  akios timeline --list              List all available timelines
  akios timeline run-20260201-1      Show specific run
  akios timeline latest --json       JSON output for scripting
  akios timeline latest --width 100  Custom console width
        """
    )
    
    parser.add_argument(
        'run_name',
        nargs='?',
        default=None,
        help='Run name or "latest" for most recent (default: latest)'
    )
    
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List all available timeline records'
    )
    
    parser.add_argument(
        '-c', '--compare',
        nargs='+',
        help='Compare multiple runs (e.g., run-001 run-002)'
    )
    
    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='Output as JSON for scripting'
    )
    
    parser.add_argument(
        '-w', '--width',
        type=int,
        default=None,
        help='Console width override'
    )
    
    parser.add_argument(
        '-s', '--summary',
        action='store_true',
        help='Show summary statistics only'
    )
    
    parser.set_defaults(func=run_timeline_command)


def run_timeline_command(args: argparse.Namespace) -> int:
    """
    Main timeline command handler.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Exit code (0=success, 1=error)
    """
    try:
        # Handle --list flag
        if args.list:
            return _list_timelines(args.json)
        
        # Handle --compare flag
        if args.compare:
            return _compare_timeline_runs(args.compare, args.json)
        
        # Handle no arguments - show latest
        run_name = args.run_name or 'latest'
        
        # Display timeline
        return _display_timeline(run_name, args.json, args.width, args.summary)
        
    except CLIError as e:
        if args.json:
            print(json.dumps({"error": True, "message": str(e)}))
        else:
            output_with_mode(
                message=str(e),
                output_type="error",
                json_mode=False
            )
        return 1
    except KeyboardInterrupt:
        output_with_mode(
            message="Interrupted by user",
            output_type="warning",
            json_mode=False
        )
        return 130
    except Exception as e:
        if args.json:
            print(json.dumps({"error": True, "message": str(e)}))
        else:
            output_with_mode(
                message=f"Unexpected error: {e}",
                output_type="error",
                json_mode=False
            )
        return 1


def _get_audit_dir() -> Path:
    """Get the audit directory path."""
    from akios.config import get_settings
    settings = get_settings()
    return Path(settings.audit_storage_path)


def _find_timeline_file(run_name: str) -> Optional[Path]:
    """
    Find timeline/audit file for a run.
    
    Args:
        run_name: Run name (latest, run-001, etc.)
    
    Returns:
        Path to audit file or None
    """
    audit_dir = _get_audit_dir()
    
    if not audit_dir.exists():
        return None
    
    # Handle 'latest'
    if run_name.lower() == 'latest':
        # Find most recent audit file
        audit_files = sorted(audit_dir.glob('*.json'))
        if audit_files:
            return audit_files[-1]
        return None
    
    # Handle specific run name
    # Try exact match first
    candidate = audit_dir / f"{run_name}.json"
    if candidate.exists():
        return candidate
    
    # Try partial match
    for f in audit_dir.glob(f"*{run_name}*.json"):
        return f
    
    return None


def _list_timelines(json_mode: bool = False) -> int:
    """
    List available timeline records.
    
    Args:
        json_mode: Output as JSON
    
    Returns:
        Exit code
    """
    audit_dir = _get_audit_dir()
    
    if not audit_dir.exists():
        if json_mode:
            print(json.dumps({"timelines": []}))
        else:
            output_with_mode(
                message="No audit history available yet",
                details=["Run a workflow first: akios run <template>"],
                output_type="info",
                json_mode=False
            )
        return 0
    
    audit_files = sorted(audit_dir.glob('*.json'))
    
    if json_mode:
        timelines = []
        for f in audit_files:
            try:
                with open(f, 'r') as fd:
                    data = json.load(fd)
                    timelines.append({
                        "name": f.stem,
                        "workflow": data.get("workflow", "Unknown"),
                        "total_duration": data.get("total_duration", 0),
                        "timestamp": data.get("end_time", "Unknown"),
                        "steps": len(data.get("steps", []))
                    })
            except Exception:
                continue
        print(json.dumps({"timelines": timelines}, indent=2))
        return 0
    
    # Human-readable format
    if not audit_files:
        output_with_mode(
            message="No timeline records found",
            output_type="info",
            json_mode=False
        )
        return 0
    
    output_with_mode(
        message="Available Timeline Records",
        details=[
            f"{f.stem:<20} ({len([d for d in json.loads(open(f).read()).get('steps', [])])} steps)"
            for f in audit_files[:10]  # Show last 10
        ],
        output_type="info",
        json_mode=False
    )
    
    return 0


def _display_timeline(
    run_name: str,
    json_mode: bool = False,
    width: Optional[int] = None,
    summary_only: bool = False
) -> int:
    """
    Display timeline for a specific run.
    
    Args:
        run_name: Run name or 'latest'
        json_mode: Output as JSON
        width: Console width
        summary_only: Show summary only
    
    Returns:
        Exit code
    """
    # Find audit file
    file_path = _find_timeline_file(run_name)
    
    if not file_path:
        if json_mode:
            print(json.dumps({
                "error": True,
                "message": f"Timeline not found: {run_name}"
            }))
        else:
            output_with_mode(
                message=f"Timeline not found for run '{run_name}'",
                details=["Run 'akios timeline --list' to see available timelines"],
                output_type="error",
                json_mode=False
            )
        return 1
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
        
        # Handle summary mode
        if summary_only:
            summary = get_timeline_summary(audit_data)
            if json_mode:
                print(json.dumps(summary, indent=2))
            else:
                content = f"Workflow: {summary['workflow']}\n"
                content += f"Total Duration: {summary['total_duration']:.2f}s\n"
                content += f"Steps: {summary['step_count']}\n"
                if summary.get('bottleneck_step'):
                    content += f"Bottleneck: {summary['bottleneck_step']} ({summary['bottleneck_percentage']:.0f}%)"
                
                print_panel("Timeline Summary", content)
            return 0
        
        # Display full timeline
        render_timeline(audit_data, json_mode=json_mode, width=width)
        return 0
        
    except json.JSONDecodeError:
        if json_mode:
            print(json.dumps({
                "error": True,
                "message": f"Invalid timeline file: {file_path}"
            }))
        else:
            print_error(f"Invalid timeline file: {file_path}")
        return 1
    except Exception as e:
        if json_mode:
            print(json.dumps({
                "error": True,
                "message": str(e)
            }))
        else:
            print_error(str(e))
        return 1


def _compare_timeline_runs(run_names: list, json_mode: bool = False) -> int:
    """
    Compare multiple timeline runs.
    
    Args:
        run_names: List of run names
        json_mode: Output as JSON
    
    Returns:
        Exit code
    """
    if not run_names:
        print_error("Specify at least 2 runs to compare")
        return 1
    
    audit_data_list = []
    
    for run_name in run_names:
        file_path = _find_timeline_file(run_name)
        
        if not file_path:
            print(f"Warning: Timeline not found for '{run_name}'", file=sys.stderr)
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                audit_data_list.append(json.load(f))
        except Exception as e:
            print(f"Warning: Error loading '{run_name}': {e}", file=sys.stderr)
            continue
    
    if not audit_data_list:
        print_error("No timelines found to compare")
        return 1
    
    compare_timelines(audit_data_list, json_mode=json_mode)
    return 0
