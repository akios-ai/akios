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
CLI Color and Formatting Utilities

Provides cross-platform color support and formatting for enhanced CLI user experience.
Works seamlessly in both native Unix and Docker environments.
"""

import os
import sys
from typing import Optional

try:
    from .rich_output import get_theme_ansi, ANSI_RESET
except ImportError:
    # Fallback
    def get_theme_ansi(name): return ""
    ANSI_RESET = ""

class Colors:
    """
    ANSI color codes for CLI output formatting.
    DEPRECATED: Use semantic functions or rich_output instead.
    Kept for backward compatibility.
    """
    RESET = ANSI_RESET
    # We map these to theme colors where possible, or keep defaults if no mapping
    # Note: These are not strictly theme-compliant if used directly.
    # Users should use semantic methods.
    pass


class ColorFormatter:
    """
    Cross-platform color formatter for CLI output.
    
    Automatically detects terminal capabilities and gracefully degrades
    when colors are not supported (Docker, CI/CD, redirected output).
    """

    def __init__(self):
        self._colors_enabled = self._should_enable_colors()

    def _should_enable_colors(self) -> bool:
        """
        Determine if colors should be enabled based on environment.
        """
        # Respect NO_COLOR standard
        if os.environ.get('NO_COLOR'):
            return False

        # Only enable colors for TTY output
        if not sys.stdout.isatty():
            return False

        # Check TERM variable
        term = os.environ.get('TERM', '').lower()
        if term in ('dumb', 'unknown'):
            return False

        # Enable colors for known good terminals
        if term in ('xterm', 'xterm-256color', 'screen', 'screen-256color', 'linux'):
            return True

        # Enable for common development environments
        if any(env in os.environ for env in ['COLORTERM', 'CLICOLOR']):
            return True

        # Default: enable colors for most modern terminals
        return True

    def colorize(self, text: str, color: str, style: Optional[str] = None) -> str:
        """
        Apply color and style to text if colors are enabled.
        """
        if not self._colors_enabled:
            return text

        if style:
            return f"{style}{color}{text}{ANSI_RESET}"
        else:
            return f"{color}{text}{ANSI_RESET}"

    def success(self, text: str) -> str:
        """Format text as success (green)."""
        if not self._colors_enabled: return text
        return f"{get_theme_ansi('success')}{text}{ANSI_RESET}"

    def error(self, text: str) -> str:
        """Format text as error (red)."""
        if not self._colors_enabled: return text
        return f"{get_theme_ansi('error')}{text}{ANSI_RESET}"

    def warning(self, text: str) -> str:
        """Format text as warning (yellow)."""
        if not self._colors_enabled: return text
        return f"{get_theme_ansi('warning')}{text}{ANSI_RESET}"

    def info(self, text: str) -> str:
        """Format text as info (cyan)."""
        if not self._colors_enabled: return text
        return f"{get_theme_ansi('info')}{text}{ANSI_RESET}"

    def bold(self, text: str) -> str:
        """Format text as bold."""
        if not self._colors_enabled: return text
        # 'header' is bold cyan, but if we just want bold...
        # The theme doesn't expose a generic 'bold'.
        # We can use standard ANSI bold here as it's a style.
        return f"\033[1m{text}{ANSI_RESET}"

    def dim(self, text: str) -> str:
        """Format text as dimmed."""
        if not self._colors_enabled: return text
        return f"\033[2m{text}{ANSI_RESET}"

    def header(self, text: str) -> str:
        """Format text as header (bold cyan)."""
        if not self._colors_enabled: return text
        return f"{get_theme_ansi('header')}{text}{ANSI_RESET}"

    def highlight(self, text: str) -> str:
        """Format text as highlight (bold white/purple)."""
        if not self._colors_enabled: return text
        return f"{get_theme_ansi('highlight')}{text}{ANSI_RESET}"



# Global color formatter instance
_color_formatter = None

def get_color_formatter() -> ColorFormatter:
    """Get the global color formatter instance."""
    global _color_formatter
    if _color_formatter is None:
        _color_formatter = ColorFormatter()
    return _color_formatter


def success(text: str) -> str:
    """Format text as success (green)."""
    return get_color_formatter().success(text)

def error(text: str) -> str:
    """Format text as error (red)."""
    return get_color_formatter().error(text)

def warning(text: str) -> str:
    """Format text as warning (yellow)."""
    return get_color_formatter().warning(text)

def info(text: str) -> str:
    """Format text as info (blue)."""
    return get_color_formatter().info(text)

def bold(text: str) -> str:
    """Format text as bold."""
    return get_color_formatter().bold(text)

def dim(text: str) -> str:
    """Format text as dimmed."""
    return get_color_formatter().dim(text)

def header(text: str) -> str:
    """Format text as header (bold cyan)."""
    return get_color_formatter().header(text)

def highlight(text: str) -> str:
    """Format text as highlight (bold white)."""
    return get_color_formatter().highlight(text)
