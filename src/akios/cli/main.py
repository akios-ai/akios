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
CLI main entry point - uses argparse to dispatch commands.

Simple, script-friendly interface with zero external dependencies.
"""

import argparse
import logging
import os
import sys

# Handle PyInstaller frozen application
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    import akios._version as _version_module
    import akios.cli.commands as commands_module
    import akios.cli.helpers as helpers_module

    __version__ = _version_module.__version__
    register_all_commands = commands_module.register_all_commands
    get_command_descriptions = commands_module.get_command_descriptions
    get_version_info = helpers_module.get_version_info
    handle_cli_error = helpers_module.handle_cli_error
else:
    # Running as normal Python module
    from .._version import __version__
    from .commands import register_all_commands, get_command_descriptions
    from .helpers import get_version_info, handle_cli_error


def show_version() -> None:
    """Show enhanced version information with build details."""
    from ..core.ui.rich_output import _should_use_rich
    
    if _should_use_rich():
        from ..core.ui.rich_output import get_theme_color
        version_info = f"[bold {get_theme_color('header')}]AKIOS[/bold {get_theme_color('header')}] [bold]{__version__}[/bold]"
        try:
            # Try to get git commit hash
            import subprocess
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                version_info += f" [dim](commit: {commit_hash})[/dim]"
        except (Exception, KeyboardInterrupt):
            pass  # Gracefully ignore if git not available

        try:
            # Try to get build date from git
            import subprocess
            result = subprocess.run(['git', 'log', '-1', '--format=%ci'],
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                build_date = result.stdout.strip().split()[0]  # Just the date part
                version_info += f" [dim](built: {build_date})[/dim]"
        except (Exception, KeyboardInterrupt):
            pass  # Gracefully ignore if git not available
        
        # Use Rich console for colored output
        from ..core.ui.rich_output import _get_console
        console = _get_console()
        console.print(version_info)
    else:
        # Plain text fallback
        version_info = f"AKIOS {__version__}"
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                version_info += f" (commit: {commit_hash})"
        except (Exception, KeyboardInterrupt):
            pass

        try:
            import subprocess
            result = subprocess.run(['git', 'log', '-1', '--format=%ci'],
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                build_date = result.stdout.strip().split()[0]
                version_info += f" (built: {build_date})"
        except (Exception, KeyboardInterrupt):
            pass
        
        print(version_info)


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Custom help formatter with color support.

    Adds ANSI color codes to help output for better readability.
    Colors automatically disabled in non-TTY environments.
    """

    def _format_usage(self, usage, actions, groups, prefix):
        """Override usage formatting to customize help output."""
        result = super()._format_usage(usage, actions, groups, prefix)
        return result.replace('positional arguments', 'commands')

    def format_help(self):
        """Override main help formatting to add colors."""
        help_text = super().format_help()
        help_text = help_text.replace('positional arguments:', 'commands:')
        
        # Add colors if terminal supports it
        if sys.stdout.isatty() and os.environ.get('NO_COLOR') != '1':
            from ..core.ui.rich_output import get_theme_ansi, ANSI_RESET
            
            # Semantic Theme Colors
            HEADER_COLOR = get_theme_ansi('header')
            SUCCESS_COLOR = get_theme_ansi('success')
            WARNING_COLOR = get_theme_ansi('warning')
            INFO_COLOR = get_theme_ansi('info')
            DIM = "\033[2m"  # Standard ANSI dim style
            RESET = ANSI_RESET
            
            # Color the main sections
            help_text = help_text.replace('usage:', f'{INFO_COLOR}usage:{RESET}')
            help_text = help_text.replace('AKIOS - Security-first AI agent runtime', 
                                         f'{HEADER_COLOR}AKIOS{RESET} - {DIM}Security-first AI agent runtime{RESET}')
            help_text = help_text.replace('commands:', f'{SUCCESS_COLOR}commands:{RESET}')
            help_text = help_text.replace('options:', f'{SUCCESS_COLOR}options:{RESET}')
            help_text = help_text.replace('Examples:', f'{WARNING_COLOR}Examples:{RESET}')
            
            # Color command names in examples (lines starting with akios)
            lines = help_text.split('\n')
            colored_lines = []
            for line in lines:
                # Color 'akios' command in examples
                if '  akios ' in line and not line.strip().startswith('#'):
                    line = line.replace('akios ', f'{INFO_COLOR}akios{RESET} ')
                    # Color comments
                    if '#' in line:
                        parts = line.split('#', 1)
                        line = parts[0] + f'{DIM}#{parts[1]}{RESET}'
                colored_lines.append(line)
            help_text = '\n'.join(colored_lines)
        
        return help_text

    def _format_action(self, action):
        """Override action formatting to customize help output."""
        result = super()._format_action(action)
        return result.replace('positional arguments', 'commands')


def create_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="akios",
        description="AKIOS - Security-first AI agent runtime",
        formatter_class=CustomHelpFormatter,
        epilog="""
Examples:
  akios init                    # Initialize project
  akios run workflow.yml        # Execute workflow
  akios status --security       # Show security dashboard
  akios audit export              # Export audit report
  akios logs --limit 5          # Show recent logs

Use 'akios <command> --help' for command-specific options.
        """
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # Add subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )

    # Register all commands
    register_all_commands(subparsers)

    return parser


def _configure_debug_logging(args: argparse.Namespace) -> None:
    """Configure debug logging if requested."""
    debug_enabled = getattr(args, 'debug', False) or os.environ.get('AKIOS_DEBUG') == '1'

    if debug_enabled:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s DEBUG %(name)s: %(message)s',
            stream=sys.stderr
        )

    # Make debug state available to commands
    os.environ['AKIOS_DEBUG_ENABLED'] = '1' if debug_enabled else '0'


def _configure_json_mode() -> bool:
    """Configure JSON mode for automation-friendly output."""
    json_mode = os.environ.get('AKIOS_JSON_MODE', '').lower() in ('1', 'true', 'yes')
    os.environ['AKIOS_JSON_MODE'] = '1' if json_mode else '0'
    return json_mode


def _validate_startup_security() -> None:
    """Validate security requirements at startup."""
    try:
        if getattr(sys, 'frozen', False):
            import akios.security.validation as validation_module
            validation_module.validate_startup_security()
        else:
            from ..security.validation import validate_startup_security
            validate_startup_security()
    except Exception as e:
        print(f"SECURITY VALIDATION FAILED: {e}", file=sys.stderr)
        raise


def _validate_configuration(args: argparse.Namespace) -> None:
    """Validate environment configuration early."""
    if args.command not in ['init', 'setup', 'serve']:
        try:
            if getattr(sys, 'frozen', False):
                import akios.config as config_module
                config_module.get_settings()
            else:
                from ..config import get_settings
                get_settings()
        except Exception as e:
            print(f"CONFIGURATION VALIDATION FAILED: {e}", file=sys.stderr)
            raise


def _run_first_run_wizard(args: argparse.Namespace) -> None:
    """Run first-run detection and setup wizard."""
    # Only run setup wizard if explicitly requested with --wizard flag
    if args.command == 'init' and getattr(args, 'wizard', False) is True:
        try:
            from pathlib import Path
            if getattr(sys, 'frozen', False):
                import akios.core.config.first_run as first_run_module
                first_run_module.run_setup_wizard(Path.cwd())
            else:
                from ..core.config.first_run import run_setup_wizard
                project_root = Path.cwd()
                run_setup_wizard(project_root)
        except Exception:
            # Silently fail if wizard fails - don't block command execution
            pass


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0=success, 1=error, 2=usage error, 137=killed)
    """
    # Initialize json_mode to avoid UnboundLocalError in exception handlers
    json_mode = False

    try:
        parser = create_parser()
        args = parser.parse_args()

        # Configure debug logging
        _configure_debug_logging(args)

        # Configure JSON mode
        json_mode = _configure_json_mode()

        # Handle --version
        if getattr(args, 'version', False):
            show_version()
            return 0

        # Handle no command provided
        if not args.command:
            parser.print_help()
            return 2

        # Validate security requirements at startup
        # Skip for commands that don't need kernel-level security
        if args.command not in ('serve',):
            _validate_startup_security()

        # Validate environment configuration
        _validate_configuration(args)

        # Run first-run wizard if needed
        _run_first_run_wizard(args)

        # Dispatch to command handler
        if hasattr(args, 'func'):
            return args.func(args)
        else:
            from .helpers import handle_cli_error, CLIError
            return handle_cli_error(CLIError(f"Unknown command '{args.command}'", exit_code=2), json_mode=json_mode)

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except SystemExit as e:
        return e.code
    except Exception as e:
        from .helpers import handle_cli_error
        return handle_cli_error(e, json_mode=json_mode)


if __name__ == "__main__":
    sys.exit(main())
