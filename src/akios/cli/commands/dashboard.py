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
AKIOS Dashboard — launch the local compliance dashboard.

If the extended dashboard package is installed, starts the dashboard server
on localhost:8080. If not installed, prints guidance.
"""

import importlib.util
import sys


def register_dashboard_command(subparsers):
    """Register the 'dashboard' CLI command."""
    parser = subparsers.add_parser(
        'dashboard',
        help='Launch the local compliance dashboard'
    )
    parser.add_argument(
        '--port', type=int, default=8080,
        help='Port for the dashboard server (default: 8080)'
    )
    parser.add_argument(
        '--no-browser', action='store_true',
        help='Do not open browser automatically'
    )
    parser.set_defaults(func=run_dashboard_command)


def run_dashboard_command(args):
    """Execute the dashboard command."""
    # Check if extended dashboard package is installed
    spec = importlib.util.find_spec('akios_dashboard')

    if spec is None:
        _print_upgrade_message()
        sys.exit(0)

    # Dashboard package found — launch
    try:
        from akios_dashboard import start_dashboard
        start_dashboard(
            port=getattr(args, 'port', 8080),
            open_browser=not getattr(args, 'no_browser', False)
        )
    except ImportError as e:
        _print_upgrade_message(error=str(e))
        sys.exit(1)


def _print_upgrade_message(error=None):
    """Print dashboard package installation guidance."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    lines = [
        "[bold]Dashboard package not installed[/bold]",
        "",
        "The compliance dashboard provides:",
        "  • Real-time governance scoring (EU AI Act Art. 9)",
        "  • Extended PII detection patterns",
        "  • Kill switch / human oversight (Art. 14)",
        "  • Compliance report generation (PDF)",
        "",
        "[bold green]Install:[/bold green] pip install akios-dashboard",
        "[bold blue]Info:[/bold blue]    https://akioud.ai/dashboard",
    ]

    if error:
        lines.append(f"\n[dim]Error: {error}[/dim]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold]AKIOS Dashboard[/bold]",
        border_style="blue"
    ))
