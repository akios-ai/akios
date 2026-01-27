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


class Colors:
    """ANSI color codes for CLI output formatting."""

    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    WHITE_ON_RED = '\033[97;41m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'

    # Reset
    RESET = '\033[0m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


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

        Colors are enabled when:
        - Output is a TTY (interactive terminal)
        - NO_COLOR environment variable is not set
        - TERM is not 'dumb'
        - Running in supported environments
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

        Args:
            text: Text to colorize
            color: ANSI color code
            style: Optional ANSI style code

        Returns:
            Colorized text or plain text
        """
        if not self._colors_enabled:
            return text

        if style:
            return f"{style}{color}{text}{Colors.RESET}"
        else:
            return f"{color}{text}{Colors.RESET}"

    def success(self, text: str) -> str:
        """Format text as success (green)."""
        return self.colorize(text, Colors.BRIGHT_GREEN)

    def error(self, text: str) -> str:
        """Format text as error (red)."""
        return self.colorize(text, Colors.BRIGHT_RED)

    def warning(self, text: str) -> str:
        """Format text as warning (yellow)."""
        return self.colorize(text, Colors.BRIGHT_YELLOW)

    def info(self, text: str) -> str:
        """Format text as info (blue)."""
        return self.colorize(text, Colors.BRIGHT_BLUE)

    def bold(self, text: str) -> str:
        """Format text as bold."""
        return self.colorize(text, Colors.BOLD)

    def dim(self, text: str) -> str:
        """Format text as dimmed."""
        return self.colorize(text, Colors.DIM)

    def header(self, text: str) -> str:
        """Format text as header (bold cyan)."""
        return self.colorize(text, Colors.BRIGHT_CYAN, Colors.BOLD)

    def highlight(self, text: str) -> str:
        """Format text as highlight (bold white)."""
        return self.colorize(text, Colors.WHITE, Colors.BOLD)


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
