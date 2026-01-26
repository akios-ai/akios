"""
CLI files command - akios files

Show available input and output files for easy workflow management.
"""

import argparse
import os
from pathlib import Path
from typing import List, Tuple

from ..helpers import CLIError, check_project_context


def register_files_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the files command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "files",
        help="Show available input and output files"
    )

    parser.add_argument(
        "category",
        nargs="?",
        choices=["input", "output", "all"],
        default="all",
        help="File category to show (default: all)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    parser.set_defaults(func=run_files_command)


def run_files_command(args: argparse.Namespace) -> int:
    """
    Execute the files command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()

        if args.category == "input" or args.category == "all":
            input_files = get_input_files()
        else:
            input_files = []

        if args.category == "output" or args.category == "all":
            output_files = get_output_files()
        else:
            output_files = []

        if args.json:
            from ..helpers import output_result
            data = {
                "input_files": input_files,
                "output_files": output_files
            }
            output_result(data, json_mode=True)
        else:
            print_files_display(input_files, output_files, args.category)

        return 0

    except CLIError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return e.exit_code
    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def get_input_files() -> List[Tuple[str, str, str]]:
    """
    Get list of input files with metadata.

    Returns:
        List of (filename, size, modified) tuples
    """
    input_dir = Path("data/input")
    if not input_dir.exists():
        return []

    files = []
    for file_path in input_dir.iterdir():
        if file_path.is_file():
            try:
                stat = file_path.stat()
                size = format_file_size(stat.st_size)
                modified = format_timestamp(stat.st_mtime)
                files.append((file_path.name, size, modified))
            except OSError:
                # Skip files we can't stat
                continue

    return sorted(files, key=lambda x: x[0])


def get_output_files() -> List[Tuple[str, str, str]]:
    """
    Get list of recent output files with metadata.

    Returns:
        List of (run_dir, file_count, modified) tuples
    """
    output_dir = Path("data/output")
    if not output_dir.exists():
        return []

    runs = []
    for run_dir in output_dir.iterdir():
        if run_dir.is_dir() and run_dir.name.startswith("run_"):
            try:
                stat = run_dir.stat()
                file_count = sum(1 for _ in run_dir.iterdir() if _.is_file())
                modified = format_timestamp(stat.st_mtime)
                runs.append((run_dir.name, f"{file_count} files", modified))
            except OSError:
                continue

    # Return most recent 5 runs
    return sorted(runs, key=lambda x: x[0], reverse=True)[:5]


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024}KB"
    else:
        return f"{size_bytes // (1024 * 1024)}MB"


def format_timestamp(timestamp: float) -> str:
    """Format timestamp as relative time."""
    import time
    from datetime import datetime

    now = time.time()
    diff = now - timestamp

    if diff < 60:
        return "just now"
    elif diff < 3600:
        minutes = int(diff // 60)
        return f"{minutes}m ago"
    elif diff < 86400:
        hours = int(diff // 3600)
        return f"{hours}h ago"
    else:
        days = int(diff // 86400)
        return f"{days}d ago"


def print_files_display(input_files: List[Tuple[str, str, str]],
                       output_files: List[Tuple[str, str, str]],
                       category: str) -> None:
    """Print formatted files display."""
    if category in ["input", "all"] and input_files:
        print("📁 Input Files")
        print("=" * 13)
        for name, size, modified in input_files:
            print(f"  {name:<30} {size:>8}  {modified}")
        print()

    if category in ["output", "all"] and output_files:
        print("📤 Recent Output Runs")
        print("=" * 20)
        for run_name, file_count, modified in output_files:
            print(f"  {run_name:<25} {file_count:>10}  {modified}")
        print()

    if not input_files and not output_files:
        print("No files found in data directories.")
        print("💡 Tip: Add files to data/input/ and run workflows to create outputs")
        return

    # Show usage tips
    if input_files:
        print("💡 To use input files in workflows, reference them in your YAML templates:")
        print("   path: \"./data/input/your-file.txt\"")
    if output_files:
        print("💡 To view output files: ls data/output/run_*/")
