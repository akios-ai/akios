"""
Setup Command - Guided first-run configuration

Provides interactive setup wizard for new AKIOS projects.
Works identically in both Native and Docker deployments.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def register_setup_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Add setup command to argument parser.

    Args:
        subparsers: Subparser action from main parser
    """
    parser = subparsers.add_parser(
        'setup',
        help='Interactive setup wizard for first-time configuration',
        description='Run the guided setup wizard to configure AKIOS for your first workflow'
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
            from ..helpers import handle_cli_error, CLIError
            return handle_cli_error(CLIError("Not in an AKIOS project directory. Run 'akios init <project-name>' to create a new project first.", exit_code=1), json_mode=False)

        # Import here to avoid circular imports
        from ...core.config.first_run import SetupWizard

        # Create wizard instance
        wizard = SetupWizard(project_root)

        # Handle force flag
        if args.force:
            wizard.detector.setup_marker.unlink(missing_ok=True)

        # Handle non-interactive flag
        if args.non_interactive:
            print("ℹ️  Non-interactive mode: Skipping setup wizard")
            # Mark setup as complete to skip future prompts
            wizard.detector._mark_setup_complete()
            return 0

        # Require interactive input for setup
        if not wizard.detector._is_interactive():
            print("ℹ️  Non-interactive environment detected. Setup wizard requires a TTY.")
            print("   Configure .env manually or run on a native Linux host with an interactive terminal.")
            return 1

        # Check if we should show wizard
        if not wizard.detector.should_show_wizard():
            if args.force:
                print("🔄 Force mode: Running setup wizard anyway...")
            else:
                print("✅ AKIOS is already configured!")
                print("   Use '--force' to run setup again.")
                print("   Or edit .env and config.yaml manually.")
                return 0

        # Run the wizard
        success = wizard.run_wizard(force=args.force)

        if success:
            print("\n🎯 Setup completed successfully!")
            return 0
        else:
            print("\n❌ Setup was cancelled or failed.")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        return 1
    except Exception as e:
        print(f"❌ Setup failed: {e}", file=sys.stderr)
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
