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
CLI Progress Indicators

Provides visual feedback for long-running operations with spinners,
progress bars, and status updates. Works seamlessly in both native Unix
and Docker environments with automatic fallback for non-interactive terminals.
"""

import sys
import time
import threading
from typing import Optional, Callable
from contextlib import contextmanager

from .colors import get_color_formatter, success, warning, info, dim


class Spinner:
    """
    Terminal spinner for indicating ongoing operations.

    Provides visual feedback during long-running tasks with automatic
    cleanup and cross-platform compatibility.
    """

    def __init__(self, message: str = "Processing...", spinner_chars: str = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
        """
        Initialize spinner.

        Args:
            message: Text to display next to spinner
            spinner_chars: Characters to cycle through for animation
        """
        self.message = message
        self.spinner_chars = spinner_chars
        self.is_spinning = False
        self.thread: Optional[threading.Thread] = None
        self.formatter = get_color_formatter()

    def _spin(self) -> None:
        """Internal spinner animation loop."""
        i = 0
        while self.is_spinning:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            colored_char = self.formatter.info(char)
            sys.stdout.write(f'\r{colored_char} {self.message}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

        # Clear the spinner line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 3) + '\r')
        sys.stdout.flush()

    def start(self) -> None:
        """Start the spinner animation."""
        if not sys.stdout.isatty():
            # Non-interactive terminal - just print message
            print(f"{info('ℹ')} {self.message}")
            return

        self.is_spinning = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self, success_msg: Optional[str] = None, error_msg: Optional[str] = None) -> None:
        """
        Stop the spinner and display final message.

        Args:
            success_msg: Success message to display
            error_msg: Error message to display
        """
        self.is_spinning = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            # Ensure thread is properly cleaned up
            if self.thread.is_alive():
                # Thread didn't stop gracefully, but continue anyway
                pass

        # Clear thread reference to prevent memory leaks
        self.thread = None

        if not sys.stdout.isatty():
            # Non-interactive terminal
            if success_msg:
                print(success_msg)
            elif error_msg:
                print(error_msg, file=sys.stderr)
            return

        # Clear spinner line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 3) + '\r')

        if success_msg:
            print(f"{success('✓')} {success_msg}")
        elif error_msg:
            print(f"{warning('✗')} {error_msg}", file=sys.stderr)
        else:
            print()  # Just add newline


class ProgressBar:
    """
    Visual progress bar for operations with known completion percentage.

    Provides clear visual feedback for multi-step operations.
    """

    def __init__(self, total: int, width: int = 40, message: str = "Progress"):
        """
        Initialize progress bar.

        Args:
            total: Total number of steps
            width: Width of progress bar in characters
            message: Progress message
        """
        self.total = total
        self.width = width
        self.message = message
        self.current = 0
        self.formatter = get_color_formatter()

    def update(self, current: int, message: Optional[str] = None) -> None:
        """
        Update progress bar.

        Args:
            current: Current progress (0 to total)
            message: Optional updated message
        """
        self.current = min(current, self.total)

        if message:
            self.message = message

        if not sys.stdout.isatty():
            # Non-interactive - just show percentage
            percentage = int((self.current / self.total) * 100)
            print(f"{self.message}: {percentage}%")
            return

        # Calculate progress
        percentage = self.current / self.total
        filled_width = int(self.width * percentage)
        bar = '█' * filled_width + '░' * (self.width - filled_width)

        # Color based on progress
        if percentage < 0.3:
            bar_color = self.formatter.warning(bar)
        elif percentage < 0.7:
            bar_color = self.formatter.info(bar)
        else:
            bar_color = self.formatter.success(bar)

        percentage_str = f"{int(percentage * 100):3d}%"

        sys.stdout.write(f'\r{self.message}: [{bar_color}] {percentage_str}')
        sys.stdout.flush()

        if self.current >= self.total:
            sys.stdout.write('\n')
            sys.stdout.flush()

    def finish(self, message: Optional[str] = None) -> None:
        """Mark progress as complete."""
        self.update(self.total, message or f"{self.message} complete")


class StepTracker:
    """
    Track and display multi-step operation progress.

    Provides clear feedback for operations with multiple distinct phases.
    """

    def __init__(self, total_steps: int, operation_name: str = "Operation"):
        """
        Initialize step tracker.

        Args:
            total_steps: Total number of steps
            operation_name: Name of the operation
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.formatter = get_color_formatter()

    def start_step(self, step_name: str) -> None:
        """
        Mark the start of a new step.

        Args:
            step_name: Name of the step being started
        """
        self.current_step += 1
        step_info = f"[{self.current_step}/{self.total_steps}]"

        if sys.stdout.isatty():
            message = f"{dim(step_info)} {self.operation_name}: {info(step_name)}"
        else:
            message = f"{step_info} {self.operation_name}: {step_name}"

        print(message)

    def complete_step(self, result: Optional[str] = None) -> None:
        """
        Mark the current step as completed.

        Args:
            result: Optional result message
        """
        if result and sys.stdout.isatty():
            print(f"  {success('✓')} {result}")
        elif result:
            print(f"  ✓ {result}")


# Convenience functions for common use cases

@contextmanager
def spinner(message: str = "Processing..."):
    """
    Context manager for spinner display.

    Usage:
        with spinner("Loading data..."):
            do_work()
    """
    s = Spinner(message)
    s.start()
    try:
        yield s
    except Exception as e:
        s.stop(error_msg=str(e))
        raise
    else:
        s.stop()


def with_spinner(func: Callable, message: str = "Processing..."):
    """
    Decorator to wrap function with spinner.

    Args:
        func: Function to wrap
        message: Spinner message

    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        with spinner(message):
            return func(*args, **kwargs)
    return wrapper


def show_progress(message: str, success_msg: Optional[str] = None, error_msg: Optional[str] = None):
    """
    Show a temporary progress message with success/error outcome.

    Args:
        message: Progress message
        success_msg: Success completion message
        error_msg: Error completion message
    """
    if sys.stdout.isatty():
        # Interactive terminal
        print(f"{info('ℹ')} {message}", end='', flush=True)
        time.sleep(0.5)  # Brief pause for visual effect

        if success_msg:
            print(f"\r{success('✓')} {success_msg}")
        elif error_msg:
            print(f"\r{warning('✗')} {error_msg}", file=sys.stderr)
        else:
            print(f"\r{success('✓')} Complete")
    else:
        # Non-interactive
        print(message)
        if success_msg:
            print(success_msg)
        elif error_msg:
            print(error_msg, file=sys.stderr)
