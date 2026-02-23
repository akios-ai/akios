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
CLI files command - akios files

Show available input and output files for easy workflow management.
"""

import argparse
import os
from pathlib import Path
from typing import List, Tuple

from ..helpers import CLIError, check_project_context
from ...core.ui.rich_output import print_panel, print_table, print_info, get_theme_color


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
    """Print formatted files display with Rich UI and colors."""
    if not input_files and not output_files:
        print_panel("📁 Data Files", f"[{get_theme_color('warning')}]No files found[/{get_theme_color('warning')}] [dim]in data directories.\nAdd files to[/dim] [{get_theme_color('info')}]data/input/[/{get_theme_color('info')}] [dim]and run workflows to create outputs[/dim]", style=get_theme_color("warning"))
        return

    # Display input files with colored metadata
    if category in ["input", "all"] and input_files:
        input_data = [
            {"file": name, "size": f"[{get_theme_color('info')}]{size}[/{get_theme_color('info')}]", "modified": f"[dim]{modified}[/dim]"}
            for name, size, modified in input_files
        ]
        print_table(input_data, title="📁 Input Files", columns=["file", "size", "modified"])

    # Display output files with colored metadata
    if category in ["output", "all"] and output_files:
        output_data = [
            {"run": f"[bold]{run_name}[/bold]", "files": f"[{get_theme_color('success')}]{file_count}[/{get_theme_color('success')}]", "modified": f"[dim]{modified}[/dim]"}
            for run_name, file_count, modified in output_files
        ]
        print_table(output_data, title="📤 Recent Output Runs", columns=["run", "files", "modified"])

    # Show usage tips with colors
    tips_text = ""
    if input_files:
        tips_text += f"[{get_theme_color('success')}]✓[/{get_theme_color('success')}] [dim]Reference input files in templates:[/dim] [{get_theme_color('info')}]path: \"./data/input/your-file.txt\"[/{get_theme_color('info')}]\n"
    if output_files:
        tips_text += f"[{get_theme_color('success')}]✓[/{get_theme_color('success')}] [dim]View outputs:[/dim] [{get_theme_color('info')}]ls data/output/run_*/[/{get_theme_color('info')}]"
    
    if tips_text:
        print_info(tips_text.strip())
