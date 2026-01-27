"""
CLI clean command - akios clean --old-runs

Clean up old workflow runs and temporary data.
"""

import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta

from ..helpers import CLIError, output_result, check_project_context


def register_clean_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the clean command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "clean",
        help="Clean up project data"
    )

    parser.add_argument(
        "--old-runs",
        type=int,
        default=7,
        help="Remove runs older than N days (default: 7)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without actually deleting"
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run without confirmation prompts"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    parser.set_defaults(func=run_clean_command)


def run_clean_command(args: argparse.Namespace) -> int:
    """
    Execute the clean command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()

        clean_data = clean_old_runs(args.old_runs, dry_run=args.dry_run)

        if args.json:
            output_result(clean_data, json_mode=True)
        else:
            formatted = format_clean_results(clean_data, args.dry_run)
            print(formatted)

        return 0

    except CLIError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return e.exit_code
    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def clean_old_runs(days_old: int, dry_run: bool = False) -> dict:
    """
    Clean workflow runs older than specified days.

    Args:
        days_old: Remove runs older than this many days
        dry_run: If True, only show what would be cleaned

    Returns:
        Dict with cleaning results
    """
    if days_old <= 0:
        raise CLIError(f"Days must be positive, got {days_old}", exit_code=2)

    cutoff_date = datetime.now() - timedelta(days=days_old)

    # Find data/output/run_* directories
    output_dir = Path("data/output")
    if not output_dir.exists():
        return {
            "cleaned_runs": 0,
            "total_size_cleaned": 0,
            "runs_found": 0,
            "message": "No output directory found"
        }

    runs_cleaned = []
    total_size_cleaned = 0
    runs_found = 0

    # Look for run_YYYY-MM-DD_HH-MM-SS directories
    for item in output_dir.iterdir():
        if item.is_dir() and item.name.startswith("run_"):
            runs_found += 1

            try:
                # Extract timestamp from directory name (run_YYYY-MM-DD_HH-MM-SS)
                timestamp_str = item.name[4:]  # Remove "run_" prefix
                try:
                    run_date = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                except ValueError:
                    run_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if run_date < cutoff_date:
                    # Calculate directory size
                    dir_size = get_directory_size(item)

                    if not dry_run:
                        # Remove the directory
                        import shutil
                        shutil.rmtree(item)
                        runs_cleaned.append(item.name)
                        total_size_cleaned += dir_size
                    else:
                        # Dry run - just collect info
                        runs_cleaned.append(item.name)
                        total_size_cleaned += dir_size

            except (ValueError, OSError) as e:
                # Skip directories that don't match expected format
                continue

    return {
        "cleaned_runs": len(runs_cleaned),
        "total_size_cleaned": total_size_cleaned,
        "runs_found": runs_found,
        "cutoff_days": days_old,
        "run_names": runs_cleaned,
        "dry_run": dry_run
    }


def get_directory_size(directory: Path) -> int:
    """
    Calculate total size of a directory recursively.

    Args:
        directory: Directory path

    Returns:
        Total size in bytes
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    # Skip files we can't access
                    pass
    except OSError:
        # Skip directories we can't access
        pass

    return total_size


def format_clean_results(clean_data: dict, dry_run: bool) -> str:
    """
    Format clean results for display.

    Args:
        clean_data: Cleaning results dictionary
        dry_run: Whether this was a dry run

    Returns:
        Formatted string
    """
    lines = []

    if dry_run:
        lines.append("Clean Dry Run Results")
        lines.append("=" * 21)
        lines.append(f"Would clean runs older than {clean_data['cutoff_days']} days")
    else:
        lines.append("Clean Results")
        lines.append("=" * 13)
        lines.append(f"Cleaned runs older than {clean_data['cutoff_days']} days")

    lines.append(f"Runs found: {clean_data['runs_found']}")
    lines.append(f"Runs cleaned: {clean_data['cleaned_runs']}")

    if clean_data['cleaned_runs'] > 0:
        # Format size
        size_mb = clean_data['total_size_cleaned'] / (1024 * 1024)
        lines.append(f"Space freed: {size_mb:.2f} MB")

        lines.append("")
        lines.append("Cleaned runs:")
        for run_name in clean_data['run_names']:
            lines.append(f"  - {run_name}")
    else:
        lines.append("No old runs to clean")

    return "\n".join(lines)
