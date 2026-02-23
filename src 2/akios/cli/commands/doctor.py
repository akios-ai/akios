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
CLI doctor command - akios doctor

Show a focused diagnostics report using existing status checks.
"""

import argparse

from .status import run_status_command


def register_doctor_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the doctor command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "doctor",
        help="Run diagnostics and security checks"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format for automation"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed technical information"
    )

    parser.set_defaults(func=run_doctor_command)


def run_doctor_command(args: argparse.Namespace) -> int:
    """
    Execute the doctor command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    args.security = True
    return run_status_command(args)
