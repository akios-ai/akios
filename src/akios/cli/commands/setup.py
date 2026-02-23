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
Setup Command - Guided first-run configuration

Provides interactive setup wizard for new AKIOS projects.
Works identically in both Native and Docker deployments.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ...core.config.first_run import SetupWizard
from ..helpers import handle_cli_error, CLIError
from ..rich_helpers import output_with_mode


def register_setup_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Add setup command to argument parser.

    Args:
        subparsers: Subparser action from main parser
    """
    parser = subparsers.add_parser(
        'setup',
        help='Interactive or automated setup wizard for first-time configuration',
        description='Configure AKIOS for your first workflow. Supports both interactive and automated setup modes.'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force setup wizard to run even if already configured'
    )

    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Skip interactive prompts (useful for automated setup)'
    )

    parser.add_argument(
        '--defaults',
        action='store_true',
        help='Use recommended defaults for all setup questions (non-interactive)'
    )

    parser.add_argument(
        '--provider',
        choices=['openai', 'anthropic', 'grok', 'mistral', 'google'],
        help='Pre-select AI provider (enables non-interactive setup)'
    )

    parser.add_argument(
        '--mock-mode',
        action='store_true',
        help='Use mock mode instead of real API (enables non-interactive setup)'
    )

    parser.set_defaults(func=run_setup_command)


def run_setup_command(args: argparse.Namespace) -> int:
    """
    Execute the setup command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Determine project root
        project_root = _find_project_root()
        if not project_root:
            return handle_cli_error(CLIError("Not in an AKIOS project directory. Run 'akios init <project-name>' to create a new project first.", exit_code=1), json_mode=False)

        # Create wizard instance
        wizard = SetupWizard(project_root)

        # Handle force flag
        if args.force:
            wizard.detector.setup_marker.unlink(missing_ok=True)

        # Handle non-interactive flag
        if args.non_interactive:
            output_with_mode(
                message="Non-interactive mode: Skipping setup wizard",
                output_type="info"
            )
            # Mark setup as complete to skip future prompts
            wizard.detector._mark_setup_complete()
            return 0

        # Handle defaults flag (auto-answer with recommended defaults)
        if args.defaults:
            output_with_mode(
                message="Using recommended defaults for automated setup...",
                output_type="info"
            )
            success = wizard.run_wizard(force=args.force, defaults=True)
            if success:
                output_with_mode(
                    message="Setup completed with defaults!",
                    output_type="success"
                )
                return 0
            else:
                output_with_mode(
                    message="Setup failed.",
                    output_type="error"
                )
                return 1

        # Handle provider selection (enables non-interactive setup)
        if args.provider or args.mock_mode:
            output_with_mode(
                message="Non-interactive setup with pre-selected options...",
                output_type="info"
            )
            success = wizard.run_wizard(force=args.force, mock_mode=args.mock_mode, provider=args.provider)
            if success:
                output_with_mode(
                    message="Setup completed successfully!",
                    output_type="success"
                )
                return 0
            else:
                output_with_mode(
                    message="Setup failed.",
                    output_type="error"
                )
                return 1

        # Require interactive input for setup
        if not wizard.detector._is_interactive():
            output_with_mode(
                message="Non-interactive environment detected. Setup wizard requires a TTY.",
                output_type="warning"
            )
            output_with_mode(
                message="Configure .env manually or run on a native Linux host with an interactive terminal.",
                output_type="info"
            )
            return 1

        # Check if we should show wizard
        if not wizard.detector.should_show_wizard():
            if args.force:
                output_with_mode(
                    message="Force mode: Running setup wizard anyway...",
                    output_type="info"
                )
            else:
                output_with_mode(
                    message="AKIOS is already configured!",
                    output_type="success"
                )
                output_with_mode(
                    message="Use '--force' to run setup again.",
                    output_type="info"
                )
                output_with_mode(
                    message="Or edit .env and config.yaml manually.",
                    output_type="info"
                )
                return 0

        # Run the wizard
        success = wizard.run_wizard(force=args.force)

        if success:
            output_with_mode(
                message="Setup completed successfully!",
                output_type="success"
            )
            return 0
        else:
            output_with_mode(
                message="Setup was cancelled or failed.",
                output_type="error"
            )
            return 1

    except KeyboardInterrupt:
        output_with_mode(
            message="Setup interrupted by user.",
            output_type="warning"
        )
        return 1
    except Exception as e:
        import sys
        sys.stderr.write(f"Setup failed: {e}\n")
        return 1


def _find_project_root() -> Optional[Path]:
    """
    Find the AKIOS project root directory.

    Returns:
        Project root path or None if not found
    """
    current = Path.cwd()

    # Walk up directory tree looking for AKIOS project markers
    for path in [current] + list(current.parents):
        # Check for ALL required AKIOS project markers (strict validation)
        # A properly initialized project must have ALL of these:
        has_config = (path / "config.yaml").exists()
        has_templates = (path / "templates").exists() and (path / "templates" / "hello-workflow.yml").exists()
        has_data = (path / "data").exists()
        has_audit = (path / "audit").exists()

        # Only accept if ALL markers are present (prevents setup in wrong directories)
        if has_config and has_templates and has_data and has_audit:
            return path

    return None


def _validate_project_structure(project_root: Path) -> bool:
    """
    Validate that this is a valid AKIOS project.

    Args:
        project_root: Directory to validate

    Returns:
        True if valid AKIOS project
    """
    required_files = [
        "templates/hello-workflow.yml",
        "templates/batch_processing.yml",
        "templates/document_ingestion.yml",
        "templates/file_analysis.yml"
    ]

    for file_path in required_files:
        if not (project_root / file_path).exists():
            return False

    return True
