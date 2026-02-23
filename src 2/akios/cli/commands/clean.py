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
CLI clean command - akios clean --old-runs

Clean up old workflow runs and temporary data.
"""

import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta

from ..helpers import CLIError, output_result, check_project_context
from ..rich_helpers import output_with_mode, is_json_mode


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
        "--all",
        action="store_true",
        help="Clean all runs regardless of age"
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

        days = 0 if args.all else args.old_runs
        clean_data = clean_old_runs(days, dry_run=args.dry_run)

        if args.json:
            output_result(clean_data, json_mode=True)
        else:
            # Format and display results
            if clean_data['cleaned_runs'] > 0:
                size_mb = clean_data['total_size_cleaned'] / (1024 * 1024)
                details = [
                    f"Cleaned {clean_data['cleaned_runs']} runs older than {clean_data['cutoff_days']} days",
                    f"Space freed: {size_mb:.2f} MB",
                    f"Runs found: {clean_data['runs_found']}"
                ]
                output_with_mode(
                    message="Cleanup completed successfully",
                    details=details,
                    output_type="success",
                    json_mode=False
                )
            else:
                output_with_mode(
                    message="No old runs found to clean",
                    output_type="info",
                    json_mode=False
                )

        return 0

    except CLIError as e:
        output_with_mode(
            message=f"Error: {e}",
            output_type="error",
            json_mode=is_json_mode(getattr(args, 'json', False)),
            quiet_mode=False
        )
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
    if days_old < 0:
        raise CLIError(f"Days must be positive, got {days_old}", exit_code=2)

    if days_old == 0:
        # Clean everything - set cutoff to future
        cutoff_date = datetime.now() + timedelta(days=365)
    else:
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


def format_clean_results(clean_data: dict, dry_run: bool = False) -> str:
    """
    Format clean results into a human-readable string.

    Args:
        clean_data: Dictionary with clean operation results
        dry_run: Whether this was a dry run

    Returns:
        Formatted result string
    """
    lines = []

    if dry_run:
        lines.append("Clean Dry Run Results")
        lines.append("=" * 20)
        cutoff_days = clean_data.get("cutoff_days", 7)
        lines.append(f"Would clean runs older than {cutoff_days} days")
    else:
        lines.append("Clean Results")
        lines.append("=" * 13)

    runs_found = clean_data.get("runs_found", 0)
    cleaned_runs = clean_data.get("cleaned_runs", 0)
    total_size = clean_data.get("total_size_cleaned", 0)
    run_names = clean_data.get("run_names", [])

    lines.append(f"Runs found: {runs_found}")
    lines.append(f"Runs cleaned: {cleaned_runs}")

    # Format size in MB
    size_mb = total_size / (1024 * 1024)
    lines.append(f"Space freed: {size_mb:.2f} MB")

    if cleaned_runs == 0 and not dry_run:
        lines.append("No old runs to clean")
    elif run_names:
        lines.append("Cleaned runs:")
        for name in run_names:
            lines.append(f"  - {name}")

    return "\n".join(lines)
