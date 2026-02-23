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
CLI helpers - Shared utilities for output formatting, error handling, and JSON mode support.

Keep this tiny and focused.
"""

import json
import os
import sys
from typing import Any, Dict, Optional, List

from akios._version import __version__
from ..config import get_settings
from ..core.ui.rich_output import get_theme_color


class CLIError(Exception):
    """CLI-specific error with exit code"""
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def get_command_prefix() -> str:
    """
    Get the correct command prefix based on environment.
    Delegates to the canonical implementation in core.ui.commands.
    """
    from ..core.ui.commands import get_command_prefix as _get_prefix
    return _get_prefix()


def output_result(result: Any, json_mode: bool = False, success_message: Optional[str] = None) -> None:
    """
    Output result in appropriate format.

    Args:
        result: Result to output
        json_mode: If True, output as JSON
        success_message: Optional success message for non-JSON mode
    """
    if json_mode:
        if isinstance(result, dict):
            json.dump(result, sys.stdout, indent=2)
        else:
            json.dump({"result": result}, sys.stdout, indent=2)
        print()  # Add newline
    else:
        try:
            from rich.console import Console
            from rich.syntax import Syntax
            import json as json_module
            from ..core.ui.rich_output import get_theme_color
            _console = Console()
        except ImportError:
            _console = None
        
        if isinstance(result, dict):
            if _console:
                # Format dict with proper colors for readability
                for key, value in result.items():
                    # Format key
                    key_str = f"[bold {get_theme_color('warning')}]{key}:[/bold {get_theme_color('warning')}]"
                    
                    # Format value based on type
                    if isinstance(value, (dict, list)):
                        # For complex types, show as formatted JSON
                        value_str = json_module.dumps(value, indent=2)
                        # Limit length for very large outputs
                        if len(value_str) > 1000:
                            value_str = value_str[:1000] + "...\\n(truncated)"
                        _console.print(f"{key_str}")
                        syntax = Syntax(value_str, "json", theme="monokai", word_wrap=True)
                        _console.print(syntax)
                    elif isinstance(value, bool):
                        color = get_theme_color('success') if value else get_theme_color('error')
                        value_str = f"[bold {color}]{value}[/]"
                        _console.print(f"{key_str} {value_str}")
                    elif isinstance(value, (int, float)):
                        value_str = f"[bold {get_theme_color('info')}]{value}[/]"
                        _console.print(f"{key_str} {value_str}")
                    else:
                        value_str = f"[{get_theme_color('info')}]{value}[/]"
                        _console.print(f"{key_str} {value_str}")
            else:
                for key, value in result.items():
                    print(f"{key}: {value}")
        elif isinstance(result, str):
            if _console:
                _console.print(f"[{get_theme_color('info')}]{result}[/{get_theme_color('info')}]")
            else:
                print(result)
        else:
            if _console:
                _console.print(f"[{get_theme_color('info')}]{str(result)}[/{get_theme_color('info')}]")
            else:
                print(str(result))
        
        if success_message:
            if _console:
                _console.print(f"[bold {get_theme_color('success')}]✓[/bold {get_theme_color('success')}] [{get_theme_color('success')}]{success_message}[/{get_theme_color('success')}]")
            else:
                print(success_message)


def handle_cli_error(error: Exception, json_mode: bool = False) -> int:
    """
    Handle CLI error and return appropriate exit code.

    Uses intelligent error classification for better user guidance.

    Args:
        error: The exception that occurred
        json_mode: If True, output error as JSON

    Returns:
        Exit code
    """
    if isinstance(error, CLIError):
        exit_code = error.exit_code
        message = str(error)
    else:
        exit_code = 1
        message = str(error)

    # Classify error for intelligent handling
    try:
        from ..core.error.classifier import classify_error
        fingerprint = classify_error(message, type(error).__name__)

        # Use classified error message in non-JSON mode
        if not json_mode:
            user_message = fingerprint.get_user_friendly_message()
            print(user_message, file=sys.stderr)
        else:
            # Include classification in JSON output
            error_data = {
                "error": True,
                "message": message,
                "exit_code": exit_code,
                "category": fingerprint.category.value,
                "severity": fingerprint.severity.value,
                "suggestions": fingerprint.recovery_suggestions
            }
            json.dump(error_data, sys.stderr, indent=2)
            print(file=sys.stderr)
    except ImportError:
        # Fallback if error classifier not available
        if json_mode:
            error_data = {
                "error": True,
                "message": message,
                "exit_code": exit_code
            }
            json.dump(error_data, sys.stderr, indent=2)
            print(file=sys.stderr)
        else:
            from ..core.ui.semantic_colors import print_error
            print_error(message)

    return exit_code


def validate_file_path(file_path: str, should_exist: bool = True) -> None:
    """
    Validate file path exists or doesn't exist as required.

    Args:
        file_path: Path to validate
        should_exist: If True, file must exist; if False, file must not exist

    Raises:
        CLIError: If validation fails
    """
    from pathlib import Path

    path = Path(file_path)

    if should_exist and not path.exists():
        raise CLIError(f"File not found: {file_path}", exit_code=2)

    if not should_exist and path.exists():
        raise CLIError(f"File already exists: {file_path}", exit_code=2)


def get_version_info() -> Dict[str, str]:
    """Get version information for --version command"""
    return {
        "version": __version__,
        "name": "AKIOS",
        "description": "Security-first AI agent runtime"
    }


def _determine_ai_mode(status_data: Dict[str, Any]) -> str:
    """Determine the AI mode string for status display."""
    from ..core.ui.rich_output import get_theme_color
    api_keys_status = status_data.get('api_keys_setup', {})
    mock_mode = api_keys_status.get('mock_mode_enabled', True)

    if mock_mode:
        return f"[{get_theme_color('warning')}]🎭 MOCK MODE[/{get_theme_color('warning')}] - [dim]Safe Testing (No Costs)[/dim]"

    settings = get_settings()
    provider = getattr(settings, 'llm_provider', None)
    model = getattr(settings, 'llm_model', None)

    if provider and model:
        provider_label = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "grok": "Grok",
            "mistral": "Mistral",
            "gemini": "Gemini"
        }.get(provider, provider.title())
        return f"[{get_theme_color('success')}]Real API[/{get_theme_color('success')}] ([{get_theme_color('primary')}]{provider_label} {model}[/{get_theme_color('primary')}])"

    detected_providers = status_data.get('api_keys_detected', [])
    if detected_providers:
        provider_names = [p.title() for p in detected_providers[:2]]
        return f"[{get_theme_color('success')}]Real API[/{get_theme_color('success')}] ([{get_theme_color('primary')}]{', '.join(provider_names)} ready[/{get_theme_color('primary')}])"

    return f"[{get_theme_color('success')}]Real API[/{get_theme_color('success')}] [dim](needs setup)[/dim]"


def _format_budget_status(cost_summary: Dict[str, Any]) -> str:
    """Format budget status string."""
    from ..core.ui.rich_output import get_theme_color
    settings = get_settings()
    total_cost = cost_summary.get('total_cost', 0.0)

    if settings.cost_kill_enabled:
        # Use actual remaining budget from workflow metadata if available
        # Otherwise calculate from total cost
        budget_remaining = cost_summary.get('remaining_budget')
        if budget_remaining is None:
            # For per-run budget, available budget is always the full limit when starting
            budget_remaining = settings.budget_limit_per_run
        
        # Color code based on remaining budget percentage
        budget_limit = settings.budget_limit_per_run
        pct_remaining = (budget_remaining / budget_limit * 100) if budget_limit > 0 else 100
        
        if pct_remaining > 50:
            color = get_theme_color('success')
        elif pct_remaining > 20:
            color = get_theme_color('warning')
        else:
            color = get_theme_color('error')
        return f"[bold {color}]${budget_remaining:.4f}[/bold {color}] [dim]remaining (${budget_limit:.2f} budget)[/dim]"

    return "[dim]Cost controls disabled[/dim]"


def _format_last_run_info(status_data: Dict[str, Any]) -> str:
    """Format last run information string."""
    if 'last_run_timestamp' not in status_data:
        return "📊 Last Run: No workflows run yet"

    timestamp = status_data.get('last_run_timestamp', 'unknown')
    if timestamp == 'unknown':
        return "📊 Last Run: No workflows run yet"

    try:
        from datetime import datetime
        run_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(run_time.tzinfo)
        diff = now - run_time

        if diff.days > 0:
            time_ago = f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            time_ago = "Just now"
    except (ValueError, AttributeError):
        time_ago = "Recently"

    last_result = status_data.get('last_run_result', 'success')
    status_icon = "✅" if last_result == 'success' else "❌" if last_result == 'error' else "⚠️"
    return f"📊 Last Run: {time_ago} ({status_icon} {last_result.title()})"


def _format_verbose_details(status_data: Dict[str, Any], workflow_info: Dict[str, Any],
                          cost_summary: Dict[str, Any], mock_mode: bool,
                          api_keys_status: Dict[str, Any]) -> List[str]:
    """Format verbose technical details section."""
    lines = []
    lines.append("📋 Technical Details:")
    lines.append("-" * 25)

    total_workflows = workflow_info.get('total_workflows', 0)
    total_tokens = cost_summary.get('total_tokens', 0)
    total_cost = cost_summary.get('total_cost', 0.0)

    lines.append(f"• Workflows run: {total_workflows}")
    lines.append(f"• Total tokens: {total_tokens}")
    lines.append(f"• Total cost: ${total_cost:.4f}")

    lines.append("• Security components:")
    security_comp = get_security_status_summary()
    lines.append(f"  - Level: {security_comp['level']}")
    lines.append(f"  - PII: {security_comp['pii_status']}")
    lines.append(f"  - Network: {security_comp['network_status']}")
    lines.append(f"  - Audit: {security_comp['audit_status']}")

    if not mock_mode:
        api_keys_found = api_keys_status.get('api_keys_found', [])
        if api_keys_found:
            lines.append(f"• Configured providers: {', '.join(api_keys_found)}")

    return lines


def format_status_info(status_data: Dict[str, Any], workflow_filter: str = None, verbose: bool = False) -> str:
    """
    Format status information for display with user-friendly interface.

    Args:
        status_data: Status data dictionary
        workflow_filter: Optional workflow filter
        verbose: Show technical details

    Returns:
        Formatted status string
    """
    lines = []

    workflow_info = status_data.get('workflow_info', {})
    cost_summary = workflow_info.get('cost_summary', {})
    api_keys_status = status_data.get('api_keys_setup', {})
    mock_mode = api_keys_status.get('mock_mode_enabled', True)

    # AI mode
    ai_mode = _determine_ai_mode(status_data)
    lines.append(f"🧪 AI Mode: {ai_mode}")

    # Budget information
    budget_status = _format_budget_status(cost_summary)
    lines.append(f"💰 Budget: {budget_status}")

    # Last run information
    last_run_info = _format_last_run_info(status_data)
    lines.append(last_run_info)

    # Security status
    from ..config import get_settings
    settings = get_settings()
    
    # Determine posture based on key variables
    # Strict means: No network, PII enabled, Low budget (< $5)
    is_strict = (
        not settings.network_access_allowed and 
        settings.pii_redaction_enabled and 
        settings.budget_limit_per_run <= 5.0
    )
    
    posture = "ELEVATED (STRICT)" if is_strict else "RELAXED (DEV)"
    posture_color = "success" if is_strict else "warning"
    
    lines.append(f"🔒 Security: [{get_theme_color(posture_color)}]{posture}[/{get_theme_color(posture_color)}]")
    
    # Add concise details line
    net_status = "BLOCKED" if not settings.network_access_allowed else "ALLOWED"
    pii_status = "ENABLED" if settings.pii_redaction_enabled else "DISABLED"
    
    lines.append(f"   [dim]• Network: {net_status} | PII: {pii_status} | Budget: ${settings.budget_limit_per_run:.2f}[/dim]")

    # Output location hint
    has_run_timestamp = ('last_run_timestamp' in status_data and
                        status_data['last_run_timestamp'])
    output_hint = f"📁 Output: [{get_theme_color('success')}]Ready[/{get_theme_color('success')}] [dim](check data/output/)[/dim]" if has_run_timestamp else "📁 Output: [dim]No results yet[/dim]"
    lines.append(output_hint)

    # Verbose mode details
    if verbose:
        lines.append("")
        verbose_lines = _format_verbose_details(status_data, workflow_info, cost_summary,
                                              mock_mode, api_keys_status)
        lines.extend(verbose_lines)

    # Next steps hint
    lines.append("")
    from ..core.ui.commands import suggest_command
    if mock_mode:
        lines.append(f"💡 [dim]Next:[/dim] Run [{get_theme_color('info')}]'{suggest_command('setup')}'[/{get_theme_color('info')}] to configure real AI providers")
    else:
        lines.append(f"💡 [dim]Next:[/dim] Run [{get_theme_color('info')}]'{suggest_command('run templates/hello-workflow.yml')}'[/{get_theme_color('info')}] to test AI")

    return "\n".join(lines)


def get_security_status_summary() -> Dict[str, str]:
    """
    Get a concise security status summary for status display.

    Returns:
        Dict with security status information
    """
    try:
        from ..config import get_settings
        settings = get_settings()

        # Determine security level
        from ..security.validation import _syscall_filtering_available, _sandbox_available
        syscall_available = _syscall_filtering_available()
        sandbox_available = _sandbox_available()

        if syscall_available and sandbox_available:
            level = "Full (Kernel-hard)"
        else:
            level = "Strong (Policy-based)"

        # PII status
        pii_status = "Active"
        if settings.pii_redaction_enabled and settings.pii_redaction_outputs:
            pii_status += " (Input+Output)"
        elif settings.pii_redaction_enabled:
            pii_status += " (Input only)"
        else:
            pii_status = "Disabled"

        # Network status
        network_status = "Blocked" if not settings.network_access_allowed else "Allowed"

        # Audit status
        audit_status = "Active" if settings.audit_enabled else "Disabled"

        return {
            "level": level,
            "pii_status": pii_status,
            "network_status": network_status,
            "audit_status": audit_status
        }

    except Exception:
        # Fallback if security check fails
        return {
            "level": "Unknown",
            "pii_status": "Unknown",
            "network_status": "Unknown",
            "audit_status": "Unknown"
        }


def check_project_context() -> None:
    """
    Verify we're in a valid AKIOS project directory.

    Checks for required project files and directories.

    Raises:
        CLIError: If not in valid project directory
    """
    import os
    from pathlib import Path

    # Check for required project files/directories
    config_exists = Path("config.yaml").exists()
    templates_dir_exists = Path("templates").is_dir()

    if not (config_exists and templates_dir_exists):
        raise CLIError(
            "This command should be run from inside an AKIOS project directory.\n\n"
            "To get started:\n"
            "  1. Create a project: akios init my-project\n"
            "  2. Enter the project: cd my-project\n"
            "  3. Run commands from there (e.g. akios run workflow.yml)",
            exit_code=1
        )


def format_logs_info(logs_data: Dict[str, Any]) -> str:
    """
    Format logs information for display.

    Args:
        logs_data: Logs data dictionary

    Returns:
        Formatted logs string
    """
    lines = []
    lines.append(f"[{get_theme_color('header')}]Recent Logs[/{get_theme_color('header')}]")
    lines.append("[dim]" + "=" * 11 + "[/dim]")

    events = logs_data.get("events", [])
    if not events:
        lines.append(f"[{get_theme_color('warning')}]No recent logs found[/{get_theme_color('warning')}]")
    else:
        for i, event in enumerate(events[-10:], 1):  # Show last 10 events
            timestamp = event.get("timestamp", "unknown")[:19]  # YYYY-MM-DDTHH:MM:SS
            agent = event.get("agent", "unknown")
            action = event.get("action", "unknown")
            result = event.get("result", "unknown")

            # Color code the result
            if result == "success":
                status = f"[bold {get_theme_color('success')}]✓[/bold {get_theme_color('success')}]"
                result_colored = f"[{get_theme_color('success')}]" + result + f"[/{get_theme_color('success')}]"
            else:
                status = f"[bold {get_theme_color('error')}]✗[/bold {get_theme_color('error')}]"
                result_colored = f"[{get_theme_color('error')}]" + result + f"[/{get_theme_color('error')}]"
            
            lines.append(f"{i:2d}: [dim]{timestamp}[/dim] [{get_theme_color('info')}]{agent}[/{get_theme_color('info')}].[{get_theme_color('info')}]{action}[/{get_theme_color('info')}] -> {status} {result_colored}")

    return "\n".join(lines)
