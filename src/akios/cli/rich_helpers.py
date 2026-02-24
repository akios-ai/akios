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
Rich terminal output helpers for CLI commands.

Provides intelligent output routing:
- Rich UI when appropriate (terminal, colors enabled)
- Plain text fallback for pipes/non-TTY
- JSON purity when in JSON mode
- NO_COLOR environment variable support

All commands should use these helpers for consistent output behavior.
"""

import os
import re
import sys
import json
from typing import Optional, Any, List, Dict

from ..core.ui.rich_output import (
    print_panel, print_table, print_success, print_warning,
    print_error, print_info, print_banner, is_rich_available
)


# ============================================================================
# OUTPUT MODE DETECTION
# ============================================================================

def should_use_rich() -> bool:
    """
    Determine if Rich UI should be used based on environment.

    Checks (in order):
    1. NO_COLOR environment variable (if set, disable Rich)
    2. TTY detection (if not a terminal, disable Rich)
    3. Rich library availability

    Returns:
        True if Rich UI should be used, False otherwise
    """
    # Check NO_COLOR environment variable (standard: https://no-color.org/)
    if os.environ.get('NO_COLOR'):
        return False

    # Check if stdout is a TTY (terminal)
    if not sys.stdout.isatty():
        return False

    # Check if Rich is available
    if not is_rich_available():
        return False

    return True


def is_json_mode(args_json: bool = False) -> bool:
    """
    Determine if JSON output mode should be used.

    Checks the --json flag from argparse AND the AKIOS_JSON_MODE
    environment variable (set in main.py for automation-friendly output).

    Args:
        args_json: The --json flag value from argparse

    Returns:
        True if JSON mode is active
    """
    if args_json is True:
        return True
    return os.environ.get('AKIOS_JSON_MODE', '').lower() in ('1', 'true', 'yes')


def is_quiet_mode(args_quiet: bool = False) -> bool:
    """
    Determine if quiet mode should be used.

    Args:
        args_quiet: The --quiet flag value from argparse

    Returns:
        True if quiet mode is active
    """
    return args_quiet is True


def is_verbose_mode(args_verbose: bool = False) -> bool:
    """
    Determine if verbose mode should be used.

    Args:
        args_verbose: The --verbose flag value from argparse

    Returns:
        True if verbose mode is active
    """
    return args_verbose is True


# ============================================================================
# OUTPUT ROUTING
# ============================================================================

def output_json_only(data: Any, file=None) -> None:
    """
    Output pure JSON with NO Rich formatting or headers.

    Critical for automation: ensures output is parseable by jq and automation tools.

    Args:
        data: Data to output as JSON
        file: File handle (defaults to sys.stdout)
    """
    if file is None:
        file = sys.stdout

    if isinstance(data, dict):
        json.dump(data, file, indent=2)
    else:
        json.dump({"result": data}, file, indent=2)
    
    file.write("\n")


def output_with_mode(
    message: str = "",
    details: Optional[List[str]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_mode: bool = False,
    quiet_mode: bool = False,
    output_type: str = "info",  # "success", "warning", "error", "info", "panel", "banner"
    title: Optional[str] = None,
    style: Optional[str] = None
) -> None:
    """
    Output content with intelligent mode routing.

    Routes output through appropriate channel based on mode:
    - JSON mode: Pure JSON structure (no Rich UI)
    - Quiet mode: Suppress non-critical output
    - Rich available: Use Rich UI formatting
    - Plain fallback: Use simple text output

    Args:
        message: Primary message
        details: Optional list of detail lines
        data: Optional data dict for JSON/table output
        json_mode: If True, output as JSON only
        quiet_mode: If True, suppress non-critical output
        output_type: Type of output ("success", "warning", "error", "info", "panel", "banner")
        title: Optional title for panel/table output
        style: Optional style/color override
    """
    if json_mode:
        # JSON mode: pure JSON output, nothing else
        json_data = {
            "message": message,
            "type": output_type,
        }
        if details:
            json_data["details"] = details
        if data:
            json_data.update(data)
        output_json_only(json_data)
        return

    if quiet_mode and output_type not in ["error", "warning"]:
        # Quiet mode: suppress info/success messages, keep errors/warnings
        return

    use_rich = should_use_rich()

    if not use_rich:
        # Plain text fallback — strip Rich markup tags
        def _strip_rich(text: str) -> str:
            """Remove Rich markup tags like [bold], [dim], [/#04B1DC], etc."""
            return re.sub(r'\[/?[^\]]*\]', '', text)

        if title:
            print(f"\n{'=' * 60}")
            print(title)
            print('=' * 60)
        if message:
            print(_strip_rich(message))
        if details:
            for detail in details:
                print(f"  {_strip_rich(detail)}")
        return

    # Rich UI mode
    if output_type == "success":
        print_success(message, details=details) if details else print_success(message)
    elif output_type == "warning":
        print_warning(message, details=details) if details else print_warning(message)
    elif output_type == "error":
        print_error(message, details=details) if details else print_error(message)
    elif output_type == "info":
        print_info(message, details=details) if details else print_info(message)
    elif output_type == "banner":
        print_banner(title or "Notice", message, style=style)
    elif output_type == "panel":
        # If both title and message provided, use title as panel title and message as content
        # If only message provided, use message as content with no title
        # Use None for style to let print_panel use the theme default (dimmed brand color)
        if title:
            print_panel(title, message, style=style)
        else:
            print_panel("", message, style=style)
    elif output_type == "table" and data:
        # For table output: data should be list of dicts
        if isinstance(data, list):
            print_table(data, title=title)
        else:
            # Convert single dict to table
            print_table([data], title=title)


# ============================================================================
# HELPER FUNCTIONS FOR COMMON OUTPUT PATTERNS
# ============================================================================

def print_step_counter(
    current: int,
    total: int,
    step_name: str = "",
    json_mode: bool = False,
    quiet_mode: bool = False
) -> None:
    """
    Print step counter for multi-step operations.

    Args:
        current: Current step number (1-indexed)
        total: Total steps
        step_name: Name of current step
        json_mode: If True, output as JSON
        quiet_mode: If True, suppress output
    """
    if quiet_mode:
        return

    message = f"[{current}/{total}]"
    if step_name:
        message += f" {step_name}"

    if json_mode:
        output_json_only({"step": current, "total": total, "name": step_name})
        return

    if should_use_rich():
        print_info(message)
    else:
        print(message)


def print_success_with_details(
    title: str,
    details: Optional[List[str]] = None,
    json_mode: bool = False,
    quiet_mode: bool = False
) -> None:
    """
    Print success message with optional detail lines.

    Args:
        title: Success message title
        details: Optional detail lines
        json_mode: If True, output as JSON
        quiet_mode: If True, suppress output
    """
    if quiet_mode:
        return

    output_with_mode(
        message=title,
        details=details,
        json_mode=json_mode,
        quiet_mode=False,  # Override quiet for success
        output_type="success"
    )


def print_warning_with_details(
    title: str,
    details: Optional[List[str]] = None,
    json_mode: bool = False,
    quiet_mode: bool = False
) -> None:
    """
    Print warning message with optional detail lines.

    Args:
        title: Warning message title
        details: Optional detail lines
        json_mode: If True, output as JSON
        quiet_mode: If True, suppress output
    """
    output_with_mode(
        message=title,
        details=details,
        json_mode=json_mode,
        quiet_mode=quiet_mode,
        output_type="warning"
    )


def print_error_with_details(
    title: str,
    details: Optional[List[str]] = None,
    json_mode: bool = False
) -> None:
    """
    Print error message with optional detail lines.

    Always printed, never suppressed by quiet mode.

    Args:
        title: Error message title
        details: Optional detail lines
        json_mode: If True, output as JSON
    """
    output_with_mode(
        message=title,
        details=details,
        json_mode=json_mode,
        quiet_mode=False,  # Never quiet for errors
        output_type="error"
    )


# ============================================================================
# COMPATIBILITY LAYER
# ============================================================================

def get_output_mode_summary() -> Dict[str, Any]:
    """
    Get current output mode configuration.

    Returns:
        Dict with mode information
    """
    return {
        "rich_available": is_rich_available(),
        "should_use_rich": should_use_rich(),
        "is_tty": sys.stdout.isatty(),
        "no_color": bool(os.environ.get('NO_COLOR')),
    }
