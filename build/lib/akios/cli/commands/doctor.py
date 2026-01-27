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
