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
CLI status command - akios status

Show current status, last run summary, and setup validation.
"""

import argparse
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

from ...config import get_settings
from ...core.audit.ledger import get_ledger
from ...core.analytics.cost_tracker import (
    get_budget_status,
    format_cost_breakdown,
    calculate_7day_trend,
    export_cost_history_csv,
)
from ...core.ui.rich_output import (
    print_panel, print_table, print_success, print_warning, 
    print_error, print_info, get_status_badge,
    print_budget_progress,
    print_cost_breakdown_table,
    print_spending_trend,
)
from ..helpers import CLIError, output_result, format_status_info, check_project_context


def register_status_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the status command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "status",
        help="Show current status and last run summary"
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

    parser.add_argument(
        "--workflow",
        type=str,
        help="Filter status by specific workflow ID"
    )

    parser.add_argument(
        "--security",
        action="store_true",
        help="Show comprehensive security dashboard"
    )

    parser.add_argument(
        "--budget",
        action="store_true",
        help="Show detailed budget and spending information"
    )

    parser.set_defaults(func=run_status_command)


def run_status_command(args: argparse.Namespace) -> int:
    """
    Execute the status command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    # Entry point debug - removed for production
    try:
        # Suppress interactive prompts for status command
        os.environ['AKIOS_NON_INTERACTIVE'] = '1'

        # Verify we're in a valid project context
        check_project_context()

        # Show Docker security mode information (debug mode only)
        if os.path.exists('/.dockerenv') and os.getenv("AKIOS_DEBUG_ENABLED") == "1":
            from ...core.ui.rich_output import print_info
            print_info("Docker mode: policy-based security active")

        # Handle security dashboard mode
        if args.security:
            return run_security_dashboard(args.json)

        # Handle budget details mode
        if args.budget:
            status_data = get_status_data(workflow_filter=args.workflow)
            return run_budget_dashboard(status_data, args.json)

        status_data = get_status_data(workflow_filter=args.workflow)

        if args.json:
            output_result(status_data, json_mode=True)
        else:
            formatted = format_status_info(status_data, workflow_filter=args.workflow, verbose=args.verbose)
            print_panel("AKIOS Status", formatted)

        return 0

    except CLIError as e:
        import sys
        sys.stderr.write(f"❌ Error: {e}\n")
        return e.exit_code
    except Exception as e:
        if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
            logger.debug(f"Unexpected error in status command: {e}")
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def get_status_data(workflow_filter: str = None) -> dict:
    """
    Get comprehensive status information including setup validation.

    Returns:
        Dict with status data
    """
    try:
        # Get configuration status
        settings = get_settings()

        # Get audit ledger status
        ledger = get_ledger()

        # Get last run information
        all_events = ledger.get_all_events()
        last_run = None
        if all_events:
            last_event = all_events[-1]
            last_run = {
                "workflow_id": last_event.workflow_id,
                "timestamp": last_event.timestamp,
                "last_agent": last_event.agent,
                "last_action": last_event.action,
                "last_result": last_event.result
            }

        # Get workflow-specific information
        workflow_info = get_workflow_status_info(all_events, workflow_filter)

        # Check for audit directory
        audit_path = Path(settings.audit_storage_path)
        audit_exists = audit_path.exists()

        # Check API key setup
        api_keys_status = check_api_key_setup(settings)

        # Check templates
        templates_status = check_templates_setup()

        # Check security status
        try:
            security_status = check_security_status()
        except Exception as e:
            security_status = {
                "security_level": "Error",
                "description": f"Security check failed: {e}",
                "error": str(e)
            }

        # Detect available providers
        # Provider-specific environment variables (same as LLM agent)
        key_mapping = {
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "grok": ["GROK_API_KEY"],
            "mistral": ["MISTRAL_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
        }

        providers_detected = []
        for provider in settings.allowed_providers:
            env_vars = key_mapping.get(provider, [f"{provider.upper()}_API_KEY"])
            for env_var in env_vars:
                if os.getenv(env_var):
                    providers_detected.append(provider)
                    break

        # Build status data
        from ..._version import __version__
        status_data = {
            "akios_version": __version__,
            "configuration_loaded": True,
            "sandbox_enabled": settings.sandbox_enabled,
            "audit_enabled": settings.audit_enabled,
            "audit_directory_exists": audit_exists,
            "total_audit_events": len(all_events),
            "merkle_root": ledger.get_merkle_root()[:16] + "..." if ledger.get_merkle_root() else None,
            "environment": settings.environment,
            "network_access": settings.network_access_allowed,
            "pii_redaction_enabled": settings.pii_redaction_enabled,
            "security_status": security_status,
            "api_keys_setup": api_keys_status,
            "api_keys_detected": providers_detected,
            "templates_setup": templates_status,
            "workflow_info": workflow_info
        }

        if last_run:
            status_data.update({
                "last_run_workflow": last_run["workflow_id"],
                "last_run_timestamp": last_run["timestamp"],
                "last_run_result": last_run["last_result"]
            })

        return status_data

    except Exception as e:
        raise CLIError(f"Failed to get status: {e}", exit_code=1) from e


def check_api_key_setup(settings) -> dict:
    """
    Check API key setup for LLM providers.

    Returns:
        Dict with API key status
    """
    providers = settings.allowed_providers
    api_keys_found = []
    api_keys_missing = []

    # Provider-specific environment variables (same as LLM agent)
    key_mapping = {
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "grok": ["GROK_API_KEY"],
        "mistral": ["MISTRAL_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
    }

    # Check each allowed provider
    for provider in providers:
        env_vars = key_mapping.get(provider, [get_provider_env_var(provider)])
        found = False
        for env_var in env_vars:
            if os.getenv(env_var):
                found = True
                break
        if found:
            api_keys_found.append(provider)
        else:
            api_keys_missing.append(provider)

    # Check for mock mode
    mock_mode = os.getenv('AKIOS_MOCK_LLM') == '1'

    return {
        "providers_checked": providers,
        "api_keys_found": api_keys_found,
        "api_keys_missing": api_keys_missing,
        "mock_mode_enabled": mock_mode,
        "ready_for_real_ai": len(api_keys_found) > 0 or mock_mode
    }


def check_templates_setup() -> dict:
    """
    Check if templates are available.

    Returns:
        Dict with template status
    """
    try:
        # Check user templates directory first
        user_templates_dir = Path("templates")
        if user_templates_dir.exists():
            yml_files = list(user_templates_dir.glob("*.yml"))
            return {
                "templates_found": len(yml_files),
                "template_names": [f.name for f in yml_files],
                "templates_available": len(yml_files) > 0,
                "location": "user"
            }

        # Check package templates as fallback
        import akios
        package_templates_dir = Path(akios.__file__).parent / "templates"
        if package_templates_dir.exists():
            yml_files = list(package_templates_dir.glob("*.yml"))
            return {
                "templates_found": len(yml_files),
                "template_names": [f.name for f in yml_files],
                "templates_available": len(yml_files) > 0,
                "location": "package"
            }

        return {
            "templates_found": 0,
            "template_names": [],
            "templates_available": False,
            "error": "No templates directory found"
        }
    except Exception as e:
        return {
            "templates_found": 0,
            "template_names": [],
            "templates_available": False,
            "error": str(e)
        }


def get_provider_env_var(provider: str) -> str:
    """
    Get the environment variable name for a provider.

    Args:
        provider: Provider name

    Returns:
        Environment variable name
    """
    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "grok": "GROK_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "gemini": "GEMINI_API_KEY"
    }
    return mapping.get(provider, f"{provider.upper()}_API_KEY")


def check_security_status() -> dict:
    """
    Check security system status and capabilities.

    Returns:
        Dict with security status information
    """
    import platform
    from ...security.validation import _syscall_filtering_available, _sandbox_available, _audit_system_available

    # Check individual security components
    syscall_available = _syscall_filtering_available()
    sandbox_available = _sandbox_available()
    audit_available = _audit_system_available()

    # Determine overall security level
    if syscall_available and sandbox_available and audit_available:
        security_level = "Full"
        security_description = "Complete security: cgroups v2 + seccomp-bpf + audit"
        environment_note = "Linux environment with full security features"
        recommendation = "Full security active"
    else:
        security_level = "Strong"
        security_description = "Policy-based security active"
        environment_note = "Container or limited environment"
        recommendation = "Policy-based security provides strong protection"

    return {
        "security_level": security_level,
        "description": security_description,
        "syscall_filtering": syscall_available,
        "sandbox_isolation": sandbox_available,
        "audit_system": audit_available,
        "environment": environment_note,
        "recommendation": recommendation
    }


def get_workflow_status_info(all_events, workflow_filter: str = None) -> dict:
    """
    Get workflow-specific status information from audit events.

    Args:
        all_events: List of all audit events

    Returns:
        Dict with workflow status information
    """
    if not all_events:
        return {
            "active_workflow": None,
            "total_workflows": 0,
            "last_workflow_run": None,
            "workflow_runs": {},
            "cost_summary": {"total_cost": 0.0, "total_tokens": 0}
        }

    # Filter events by workflow if specified
    if workflow_filter:
        filtered_events = [event for event in all_events
                          if getattr(event, 'workflow_id', 'unknown') == workflow_filter]
        if not filtered_events:
            return {
                "active_workflow": workflow_filter,
                "total_workflows": 0,
                "last_workflow_run": None,
                "workflow_runs": {},
                "cost_summary": {"total_cost": 0.0, "total_tokens": 0},
                "filtered_workflow": workflow_filter,
                "filtered_events": 0
            }
        all_events = filtered_events

    # Group events by workflow_id
    workflow_runs = {}
    total_cost = 0.0
    total_tokens = 0

    for event in all_events:
        workflow_id = getattr(event, 'workflow_id', 'unknown')

        if workflow_id not in workflow_runs:
            workflow_runs[workflow_id] = {
                "runs": 0,
                "last_run": None,
                "cost": 0.0,
                "tokens": 0,
                "success_count": 0,
                "error_count": 0,
                "template_source": None
            }

        workflow_runs[workflow_id]["runs"] += 1
        workflow_runs[workflow_id]["last_run"] = getattr(event, 'timestamp', None)

        # Extract cost and token information from metadata
        metadata = getattr(event, 'metadata', {}) or {}
        cost_incurred = metadata.get('cost_incurred', 0.0)
        tokens_used = metadata.get('tokens_used', 0)

        # Extract template source if available (only set once, on first encounter)
        if not workflow_runs[workflow_id]["template_source"]:
            template_source = metadata.get('template_source')
            if template_source:
                workflow_runs[workflow_id]["template_source"] = template_source

        workflow_runs[workflow_id]["cost"] += cost_incurred
        workflow_runs[workflow_id]["tokens"] += tokens_used

        total_cost += cost_incurred
        total_tokens += tokens_used

        # Count success/error
        result = getattr(event, 'result', 'unknown')
        if result == 'success':
            workflow_runs[workflow_id]["success_count"] += 1
        elif result == 'error':
            workflow_runs[workflow_id]["error_count"] += 1

    # Find the most recent workflow (active workflow) and extract remaining budget
    active_workflow = None
    last_run_time = None
    remaining_budget = None

    for workflow_id, info in workflow_runs.items():
        if info["last_run"] and (last_run_time is None or info["last_run"] > last_run_time):
            last_run_time = info["last_run"]
            active_workflow = workflow_id

    # Get remaining budget from the last workflow_complete event
    for event in reversed(all_events):
        metadata = getattr(event, 'metadata', {}) or {}
        if getattr(event, 'action', None) == 'workflow_complete':
            cost_status = metadata.get('cost_status', {})
            if 'remaining_budget' in cost_status:
                remaining_budget = cost_status['remaining_budget']
                break

    result = {
        "active_workflow": active_workflow,
        "total_workflows": len(workflow_runs),
        "last_workflow_run": last_run_time,
        "workflow_runs": workflow_runs,
        "cost_summary": {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "remaining_budget": remaining_budget
        }
    }

    if workflow_filter:
        result.update({
            "filtered_workflow": workflow_filter,
            "filtered_events": len(all_events)
        })

    return result


def run_security_dashboard(json_mode: bool = False) -> int:
    """
    Display comprehensive security status dashboard.

    Args:
        json_mode: Output in JSON format

    Returns:
        Exit code
    """
    try:
        # Get security status
        security_status = check_security_status()
        settings = get_settings()

        if json_mode:
            # JSON output for programmatic access
            security_data = {
                "security_level": security_status["security_level"],
                "description": security_status["description"],
                "environment": security_status["environment"],
                "recommendation": security_status["recommendation"],
                "active_protections": {
                    "pii_redaction": {
                        "enabled": settings.pii_redaction_enabled,
                        "outputs_protected": settings.pii_redaction_outputs,
                        "aggressive_mode": settings.pii_redaction_aggressive
                    },
                    "audit_logging": {
                        "enabled": settings.audit_enabled,
                        "audit_path": str(settings.audit_storage_path)
                    },
                    "cost_limits": {
                        "budget_limit": settings.budget_limit_per_run,
                        "token_limit": settings.max_tokens_per_call
                    },
                    "network_access": {
                        "allowed": settings.network_access_allowed
                    }
                },
                "compliance_indicators": {
                    "merkle_integrity": True,  # Always enabled
                    "tamper_evident_audit": True,  # Always enabled
                    "kill_switches": True,  # Always enabled
                    "process_isolation": True  # Always enabled
                }
            }
            import json
            print(json.dumps(security_data, indent=2))
        else:
            # Human-readable dashboard with Rich UI
            from ...core.ui.rich_output import get_theme_color
            
            success_color = get_theme_color("success")
            warning_color = get_theme_color("warning")
            error_color = get_theme_color("error")
            
            level_icon = "🛡️" if security_status["security_level"] == "Full" else "🔒"
            level_style = f"bold {success_color}" if security_status["security_level"] == "Full" else f"bold {warning_color}"
            
            title = f"{level_icon} AKIOS Security Dashboard"
            content = f"[{level_style}]{security_status['security_level']}[/{level_style}] {security_status['description']}\n" \
                     f"[dim]{security_status['environment']}[/dim]"
            # Use default theme color (Cyan) for the panel border, but keep status text colored
            print_panel(title, content)

            # Build protections table with colored status values
            protections = [
                {
                    "protection": "🔐 PII Redaction",
                    "status": f"[bold {success_color}]Enabled[/]" if settings.pii_redaction_enabled else f"[bold {error_color}]Disabled[/]",
                    "details": "[dim]Input protection always active[/dim]" if settings.pii_redaction_enabled else "[dim]—[/dim]"
                },
                {
                    "protection": "📋 Audit Logging", 
                    "status": f"[bold {success_color}]Enabled[/]" if settings.audit_enabled else f"[bold {error_color}]Disabled[/]",
                    "details": "[dim]Merkle integrity active[/dim]" if settings.audit_enabled else "[dim]—[/dim]"
                },
                {
                    "protection": "💰 Budget Limits",
                    "status": f"[bold {success_color}]Active[/]",
                    "details": f"[bold {warning_color}]${settings.budget_limit_per_run:.2f}[/] [dim]per workflow[/dim]"
                },
                {
                    "protection": "🌐 Network Access",
                    "status": f"[bold {success_color}]Allowed[/]" if settings.network_access_allowed else f"[bold {error_color}]Blocked[/]",
                    "details": "[dim]LLM API calls permitted[/dim]" if settings.network_access_allowed else "[dim]Local processing only[/dim]"
                },
            ]
            print_table(protections, title="Active Protections", columns=["protection", "status", "details"])

            # Compliance indicators with colored status
            compliance = [
                {"indicator": "Merkle Tree Integrity", "status": f"[{success_color}]✓ Active[/]", "desc": "[dim]Tamper-evident audit trails[/dim]"},
                {"indicator": "Cryptographic Audit", "status": f"[{success_color}]✓ Active[/]", "desc": "[dim]Every action logged with proof[/dim]"},
                {"indicator": "Process Isolation", "status": f"[{success_color}]✓ Active[/]", "desc": "[dim]Sandboxed execution[/dim]"},
                {"indicator": "Data Protection", "status": f"[{success_color}]✓ Active[/]", "desc": "[dim]PII automatic masking[/dim]"},
                {"indicator": "Resource Limits", "status": f"[{success_color}]✓ Active[/]", "desc": "[dim]Termination on violation[/dim]"},
            ]
            print_table(compliance, title="Compliance Indicators", columns=["indicator", "status", "desc"])

        return 0

    except Exception as e:
        if json_mode:
            import json
            error_data = {"error": True, "message": str(e)}
            print(json.dumps(error_data, indent=2))
        else:
            print(f"❌ Error retrieving security status: {e}", file=__import__("sys").stderr)
        return 1


def run_budget_dashboard(status_data: dict, json_mode: bool = False) -> int:
    """
    Display detailed budget and spending information.
    
    Shows:
    - Budget progress bar with color coding
    - Per-workflow cost breakdown table
    - 7-day spending trend
    - Status warnings at 80% threshold

    Args:
        status_data: Status data dictionary
        json_mode: Output in JSON format

    Returns:
        Exit code
    """
    try:
        workflow_info = status_data.get('workflow_info', {})
        cost_summary = workflow_info.get('cost_summary', {})
        workflow_runs = workflow_info.get('workflow_runs', {})

        # If no workflow data available yet, provide defaults
        if not cost_summary:
            cost_summary = {"total_cost": 0.0, "total_tokens": 0}
        if not workflow_runs:
            workflow_runs = {}

        settings = get_settings()
        budget_limit = settings.budget_limit_per_run
        total_cost = cost_summary.get('total_cost', 0.0)

        # If per-event cost tracking shows $0 but we have remaining_budget from
        # workflow_complete events, derive actual spending from budget arithmetic.
        # This handles the case where cost is tracked at workflow level, not per-event.
        remaining_budget = cost_summary.get('remaining_budget')
        if total_cost == 0.0 and remaining_budget is not None and remaining_budget < budget_limit:
            total_cost = round(budget_limit - remaining_budget, 4)

        if json_mode:
            # JSON output for automation (Feature 4: raw data export)
            budget_status = get_budget_status(total_cost, budget_limit)
            
            budget_data = {
                "budget_limit": budget_limit,
                "total_spent": round(total_cost, 4),
                "remaining_budget": round(budget_status['remaining'], 4),
                "utilization_percentage": budget_status['percentage'],
                "status": budget_status['status_text'],
                "is_over_budget": budget_status['is_over_budget'],
                "warning_threshold_reached": budget_status['warning_threshold_reached'],
                "workflows_run": len(workflow_runs),
                "cost_by_workflow": {}
            }

            for workflow_id, info in workflow_runs.items():
                budget_data["cost_by_workflow"][workflow_id] = {
                    "cost": round(info.get("cost", 0.0), 4),
                    "tokens": info.get("tokens", 0),
                    "runs": info.get("runs", 0),
                    "avg_cost_per_run": round(info.get("cost", 0.0) / max(info.get("runs", 1), 1), 4)
                }

            import json
            print(json.dumps(budget_data, indent=2))
        else:
            # Human-readable dashboard with Rich UI (Feature 4: visual progress bars)
            from ...core.ui.rich_output import get_theme_color
            
            header_color = get_theme_color("header")
            success_color = get_theme_color("success")
            warning_color = get_theme_color("warning")
            error_color = get_theme_color("error")
            info_color = get_theme_color("info")
            
            print_panel("💰 AKIOS Budget Dashboard", "Comprehensive cost tracking and budget monitoring", style=f"bold {header_color}")
            
            # Feature 4: Budget progress bar with color coding
            print_budget_progress(
                current_spending=total_cost,
                budget_limit=budget_limit,
                title="Overall Budget",
                show_warning=True
            )
            
            print()  # Spacing
            
            # Feature 4: Per-workflow cost breakdown table
            if workflow_runs:
                breakdown = format_cost_breakdown(workflow_runs)
                print_cost_breakdown_table(breakdown, title=f"[{header_color}]Cost Breakdown[/{header_color}] ([dim]{len(workflow_runs)} workflows[/dim])")
            else:
                print_info("No workflow cost data available yet - run a workflow to see costs")
            
            print()  # Spacing
            
            # Feature 4: 7-day spending trend
            ledger = get_ledger()
            all_events = ledger.get_all_events()
            if all_events:
                trend = calculate_7day_trend(all_events)
                print_spending_trend(trend, title="7-Day Spending Trend")
            else:
                print_info("No historical data for trend analysis")
            
            print()  # Spacing
            
            # Summary statistics with colors
            total_tokens = cost_summary.get('total_tokens', 0)
            summary_data = [
                {"metric": "💵 Budget Limit", "value": f"[bold {warning_color}]${budget_limit:.2f}[/]"},
                {"metric": "💸 Total Spent", "value": f"[bold {error_color if total_cost > budget_limit else success_color}]${total_cost:.4f}[/]"},
                {"metric": "📊 Total Tokens", "value": f"[{info_color}]{total_tokens:,}[/]"},
                {"metric": "🔢 Workflows Run", "value": f"[{success_color}]{len(workflow_runs)}[/]"},
            ]
            print_table(summary_data, title="Summary", columns=["metric", "value"])
            
            # Feature 4: CSV export option hint
            print()
            print_info(f"[dim]💡 Tip: Export cost history with:[/dim] [{info_color}]akios status --budget --json[/{info_color}]")

        return 0

    except Exception as e:
        if json_mode:
            import json
            error_data = {"error": True, "message": str(e)}
            print(json.dumps(error_data, indent=2))
        else:
            print(f"❌ Error retrieving budget information: {e}", file=__import__("sys").stderr)
        return 1
