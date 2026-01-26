"""
CLI helpers - Shared utilities for output formatting, error handling, and JSON mode support.

Keep this tiny and focused.
"""

import json
import sys
from typing import Any, Dict, Optional, List

from akios._version import __version__
from ..config import get_settings


class CLIError(Exception):
    """CLI-specific error with exit code"""
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


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
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"{key}: {value}")
        elif isinstance(result, str):
            print(result)
        else:
            print(str(result))
        
        if success_message:
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
            print(f"Error: {message}", file=sys.stderr)

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
    api_keys_status = status_data.get('api_keys_setup', {})
    mock_mode = api_keys_status.get('mock_mode_enabled', True)

    if mock_mode:
        return "🎭 MOCK MODE - Safe Testing (No Costs)"

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
        return f"Real API ({provider_label} {model})"

    detected_providers = status_data.get('api_keys_detected', [])
    if detected_providers:
        provider_names = [p.title() for p in detected_providers[:2]]
        return f"Real API ({', '.join(provider_names)} ready)"

    return "Real API (needs setup)"


def _format_budget_status(cost_summary: Dict[str, Any]) -> str:
    """Format budget status string."""
    settings = get_settings()
    total_cost = cost_summary.get('total_cost', 0.0)

    if settings.cost_kill_enabled:
        budget_remaining = max(0, settings.budget_limit_per_run - total_cost)
        return f"${budget_remaining:.2f} remaining"

    return "Cost controls disabled"


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
    lines.append("AKIOS Status")
    lines.append("=============")

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
    import os
    if os.path.exists('/.dockerenv'):
        lines.append("🔒 Security: Docker (Policy-Based) — PII/Audit/Command Limits Active")
    else:
        lines.append("🔒 Security: Linux (Kernel-Hardened) — PII/Audit/Command Limits Active")

    # Output location hint
    has_run_timestamp = ('last_run_timestamp' in status_data and
                        status_data['last_run_timestamp'])
    output_hint = "📁 Output: Ready (check data/output/)" if has_run_timestamp else "📁 Output: No results yet"
    lines.append(output_hint)

    # Verbose mode details
    if verbose:
        lines.append("")
        verbose_lines = _format_verbose_details(status_data, workflow_info, cost_summary,
                                              mock_mode, api_keys_status)
        lines.extend(verbose_lines)

    # Next steps hint
    lines.append("")
    if mock_mode:
        lines.append("💡 Next: Run 'akios setup' to configure real AI providers")
    else:
        lines.append("💡 Next: Run 'akios run templates/hello-workflow.yml' to test AI")

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
    Exits with error message if not in valid project context.

    Raises:
        SystemExit: If not in valid project directory
    """
    import os
    from pathlib import Path

    # Check for required project files/directories
    config_exists = Path("config.yaml").exists()
    templates_dir_exists = Path("templates").is_dir()

    if not (config_exists and templates_dir_exists):
        print("⚠️  WARNING: This command should be run from inside an AKIOS project directory.")
        print("")
        print("To get started:")
        print("  1. Create a project: akios init my-project")
        print("  2. Enter the project: cd my-project")
        print("  3. Run commands from there (e.g. akios run workflow.yml)")
        print("")
        print("Running from current directory may give unexpected results.")
        import sys
        sys.exit(1)


def format_logs_info(logs_data: Dict[str, Any]) -> str:
    """
    Format logs information for display.

    Args:
        logs_data: Logs data dictionary

    Returns:
        Formatted logs string
    """
    lines = []
    lines.append("Recent Logs")
    lines.append("=" * 11)

    events = logs_data.get("events", [])
    if not events:
        lines.append("No recent logs found")
    else:
        for i, event in enumerate(events[-10:], 1):  # Show last 10 events
            timestamp = event.get("timestamp", "unknown")[:19]  # YYYY-MM-DDTHH:MM:SS
            agent = event.get("agent", "unknown")
            action = event.get("action", "unknown")
            result = event.get("result", "unknown")

            status = "✓" if result == "success" else "✗"
            lines.append(f"{i:2d}: {timestamp} {agent}.{action} -> {status} {result}")

    return "\n".join(lines)
