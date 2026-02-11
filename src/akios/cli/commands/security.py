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
CLI security command - akios security <up|down|status>
Alias: akios cage <up|down|status>

Manage the Security Cage activation state.
- cage up:     Activate full protection (PII, network lock, sandbox, audit)
- cage down:   Relax for development (PII off, network open)
- cage status: Show current cage posture

The cage controls security activation, not budget configuration.
Budget is managed in config.yaml (budget_limit_per_run).
LLM API calls always pass through — the cage protects data, not blocks AI.
"""

import argparse
import os
import re
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from ...core.ui.rich_output import (
    print_panel, print_table, print_success, print_warning, 
    print_error, print_info, get_theme_color
)
from ..helpers import CLIError, check_project_context

def register_security_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the security command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    _register_common(subparsers, "security")


def register_cage_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the cage command (alias for security).

    Args:
        subparsers: Subparsers action from main parser
    """
    _register_common(subparsers, "cage")


def _register_common(subparsers: argparse._SubParsersAction, command_name: str) -> None:
    """Shared registration logic for security and cage commands."""
    parser = subparsers.add_parser(
        command_name,
        help="Manage security cage activation",
        description="Activate or deactivate the AKIOS Security Cage"
    )

    subparsers_security = parser.add_subparsers(
        dest="security_subcommand",
        help="Security action",
        required=True
    )

    # security/cage up
    up_parser = subparsers_security.add_parser(
        "up",
        help="Activate security cage (PII ON, HTTP locked, sandbox ON)"
    )
    up_parser.set_defaults(func=run_security_up)

    # security/cage down
    down_parser = subparsers_security.add_parser(
        "down",
        help="Deactivate cage and destroy all session data"
    )
    down_parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Relax protections without wiping data (dev mode)"
    )
    down_parser.set_defaults(func=run_security_down)

    # security/cage status
    status_parser = subparsers_security.add_parser(
        "status",
        help="Show current cage posture"
    )
    status_parser.set_defaults(func=run_security_status)


def _update_env_file(updates: Dict[str, str]) -> None:
    """
    Update .env file with new values, preserving comments and structure.
    
    Args:
        updates: Dictionary of key-value pairs to update
    """
    env_path = Path(".env")
    if not env_path.exists():
        # Create if not exists
        with open(env_path, "w") as f:
            for key, value in updates.items():
                f.write(f"{key}={value}\n")
        return

    # Read existing content
    with open(env_path, "r") as f:
        lines = f.readlines()

    # Process updates
    new_lines = []
    processed_keys = set()

    for line in lines:
        line_stripped = line.strip()
        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith("#"):
            new_lines.append(line)
            continue

        # Check for key match
        match = False
        for key, value in updates.items():
            if line_stripped.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                processed_keys.add(key)
                match = True
                break
        
        if not match:
            new_lines.append(line)

    # Append new keys that weren't in the file
    if processed_keys != set(updates.keys()):
        new_lines.append("\n# Added by akios security command\n")
        for key, value in updates.items():
            if key not in processed_keys:
                new_lines.append(f"{key}={value}\n")

    # Write back
    with open(env_path, "w") as f:
        f.writelines(new_lines)


def run_security_up(args: argparse.Namespace) -> int:
    """
    Activate the Security Cage.
    
    Enables:
    - PII redaction on all inputs/outputs
    - HTTP agent network lock (LLM calls still pass through)
    - Sandbox enforcement
    - Audit logging
    
    Does NOT modify budget — budget is configured in config.yaml.
    """
    check_project_context()
    
    updates = {
        "AKIOS_PII_REDACTION_ENABLED": "true",
        "AKIOS_NETWORK_ACCESS_ALLOWED": "false",
        "AKIOS_SANDBOX_ENABLED": "true",
        "AKIOS_AUDIT_ENABLED": "true",
    }

    try:
        _update_env_file(updates)
        
        # Read budget from config.yaml for display
        budget = _read_budget_from_config()
        
        success_color = get_theme_color('success')
        error_color = get_theme_color('error')
        warning_color = get_theme_color('warning')
        
        status_text = (
            f"[bold {success_color}]Security Cage: ACTIVE[/]\n\n"
            f"• PII Redaction:    [{success_color}]ENABLED[/]  — all inputs/outputs protected\n"
            f"• HTTPS Network:    [{success_color}]LOCKED[/]   — LLM APIs + allowed_domains pass through\n"
            f"• LLM API Access:   [{success_color}]ALLOWED[/]  — AI orchestration always passes through\n"
            f"• Sandbox:          [{success_color}]ENFORCED[/] — process isolation active\n"
            f"• Audit Logging:    [{success_color}]ENABLED[/]  — Merkle-chained audit trail\n"
            f"• Budget Limit:     [{warning_color}]${budget:.2f}[/]    — (from config.yaml)"
        )
        
        print_panel("🔒 Cage Up", status_text, style=success_color)
        
        if os.environ.get("AKIOS_DOCKER_WRAPPER"):
             print_warning("Running in Docker wrapper. Restart container for changes to take effect.")
        
        return 0
    except Exception as e:
        raise CLIError(f"Failed to activate security cage: {str(e)}")


def run_security_down(args: argparse.Namespace) -> int:
    """
    Deactivate the Security Cage.
    
    Default: Full data wipe — audit logs, outputs, inputs all destroyed.
    --keep-data: Relax protections without wiping (dev convenience).
    """
    check_project_context()
    
    keep_data = getattr(args, 'keep_data', False)
    
    updates = {
        "AKIOS_PII_REDACTION_ENABLED": "false",
        "AKIOS_NETWORK_ACCESS_ALLOWED": "true",
        "AKIOS_SANDBOX_ENABLED": "true",  # Always on for safety
        "AKIOS_AUDIT_ENABLED": "true",    # Always on for traceability
    }

    try:
        _update_env_file(updates)
        
        success_color = get_theme_color('success')
        warning_color = get_theme_color('warning')
        error_color = get_theme_color('error')
        
        # Perform data wipe unless --keep-data
        wipe_summary = None
        if not keep_data:
            wipe_summary = _wipe_cage_data()
        
        budget = _read_budget_from_config()
        
        if keep_data:
            status_text = (
                f"[bold {warning_color}]Security Cage: RELAXED (DEV)[/]\n\n"
                f"• PII Redaction:    [{warning_color}]DISABLED[/] — data flows unmasked\n"
                f"• HTTPS Network:    [{success_color}]OPEN[/]     — all HTTPS requests allowed\n"
                f"• LLM API Access:   [{success_color}]ALLOWED[/]  — AI orchestration passes through\n"
                f"• Sandbox:          [{success_color}]ENFORCED[/] — process isolation still active\n"
                f"• Audit Logging:    [{success_color}]ENABLED[/]  — still logging for traceability\n"
                f"• Budget Limit:     [{warning_color}]${budget:.2f}[/]    — (from config.yaml)\n\n"
                f"[{warning_color}]⚠ Data preserved (--keep-data). Use 'cage down' without flag to wipe.[/]"
            )
            print_panel("🔓 Cage Down (Dev)", status_text, style=warning_color)
        else:
            wipe_lines = _format_wipe_summary(wipe_summary, error_color)
            status_text = (
                f"[bold {error_color}]Security Cage: DOWN — DATA DESTROYED[/]\n\n"
                f"• PII Redaction:    [{warning_color}]DISABLED[/]\n"
                f"• HTTPS Network:    [{success_color}]OPEN[/]\n"
                f"• Sandbox:          [{success_color}]ENFORCED[/]\n"
                f"• Audit Logging:    [{success_color}]ENABLED[/]\n\n"
                f"[bold {error_color}]🗑️  Data Wipe Summary:[/]\n"
                f"{wipe_lines}\n\n"
                f"[{success_color}]Nothing left. Cage promise fulfilled.[/]"
            )
            print_panel("🔓 Cage Down", status_text, style=error_color)
        
        if os.environ.get("AKIOS_DOCKER_WRAPPER"):
             print_warning("Running in Docker wrapper. Restart container for changes to take effect.")

        return 0
    except Exception as e:
        raise CLIError(f"Failed to deactivate security cage: {str(e)}")


def _wipe_cage_data() -> dict:
    """
    Destroy all cage session data.
    
    Removes:
    - audit/          Merkle-chained audit logs
    - data/output/    All workflow execution outputs
    - data/input/     All user-provided input files
    
    Returns:
        Summary dict with counts and sizes
    """
    summary = {
        'audit_files': 0, 'audit_bytes': 0,
        'output_files': 0, 'output_bytes': 0,
        'input_files': 0, 'input_bytes': 0,
    }
    
    dirs_to_wipe = [
        ('audit', 'audit_files', 'audit_bytes'),
        ('data/output', 'output_files', 'output_bytes'),
        ('data/input', 'input_files', 'input_bytes'),
    ]
    
    for dir_path, files_key, bytes_key in dirs_to_wipe:
        p = Path(dir_path)
        if p.exists() and p.is_dir():
            # Count files and bytes before deleting
            for f in p.rglob('*'):
                if f.is_file():
                    try:
                        summary[bytes_key] += f.stat().st_size
                        summary[files_key] += 1
                    except OSError:
                        pass
            # Remove all contents, recreate empty dir
            shutil.rmtree(p)
            p.mkdir(parents=True, exist_ok=True)
    
    return summary


def _format_wipe_summary(summary: dict, color: str) -> str:
    """Format wipe summary into display lines."""
    def _size(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        elif b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        return f"{b / (1024 * 1024):.2f} MB"
    
    total_files = summary['audit_files'] + summary['output_files'] + summary['input_files']
    total_bytes = summary['audit_bytes'] + summary['output_bytes'] + summary['input_bytes']
    
    lines = []
    lines.append(f"  [{color}]Audit logs:[/]  {summary['audit_files']} files ({_size(summary['audit_bytes'])})")
    lines.append(f"  [{color}]Outputs:[/]     {summary['output_files']} files ({_size(summary['output_bytes'])})")
    lines.append(f"  [{color}]Inputs:[/]      {summary['input_files']} files ({_size(summary['input_bytes'])})")
    lines.append(f"  [bold {color}]Total:[/]       {total_files} files ({_size(total_bytes)}) destroyed")
    return '\n'.join(lines)


def run_security_status(args: argparse.Namespace) -> int:
    """Show current cage posture by reading .env and config.yaml."""
    check_project_context()
    
    try:
        # Read current state from .env
        env_state = _read_env_state()
        budget = _read_budget_from_config()
        
        pii_on = env_state.get("AKIOS_PII_REDACTION_ENABLED", "true").lower() == "true"
        network_open = env_state.get("AKIOS_NETWORK_ACCESS_ALLOWED", "false").lower() == "true"
        sandbox_on = env_state.get("AKIOS_SANDBOX_ENABLED", "true").lower() == "true"
        audit_on = env_state.get("AKIOS_AUDIT_ENABLED", "true").lower() == "true"
        
        # Determine posture
        if pii_on and not network_open and sandbox_on:
            posture = "ACTIVE"
            posture_icon = "🔒"
            posture_color = get_theme_color('success')
        elif not pii_on and network_open:
            posture = "RELAXED (DEV)"
            posture_icon = "🔓"
            posture_color = get_theme_color('warning')
        else:
            posture = "CUSTOM"
            posture_icon = "⚙️"
            posture_color = get_theme_color('info')
        
        success_color = get_theme_color('success')
        error_color = get_theme_color('error')
        warning_color = get_theme_color('warning')
        
        protections = [
            {
                "protection": "PII Redaction",
                "status": f"[{success_color}]ENABLED[/]" if pii_on else f"[{warning_color}]DISABLED[/]",
            },
            {
                "protection": "HTTPS Network",
                "status": f"[{success_color}]LOCKED[/]" if not network_open else f"[{warning_color}]OPEN[/]",
            },
            {
                "protection": "LLM API Access",
                "status": f"[{success_color}]ALLOWED[/]",
            },
            {
                "protection": "Sandbox",
                "status": f"[{success_color}]ENFORCED[/]" if sandbox_on else f"[{error_color}]DISABLED[/]",
            },
            {
                "protection": "Audit Logging",
                "status": f"[{success_color}]ENABLED[/]" if audit_on else f"[{error_color}]DISABLED[/]",
            },
            {
                "protection": "Budget Limit",
                "status": f"[{warning_color}]${budget:.2f}[/]",
            },
        ]
        
        print_panel(
            f"{posture_icon} Cage Status",
            f"[bold {posture_color}]Security Cage: {posture}[/]",
            style=posture_color
        )
        print_table(protections, title="Protections", columns=["protection", "status"])
        
        return 0
    except Exception as e:
        raise CLIError(f"Failed to read security status: {str(e)}")


def _read_budget_from_config() -> float:
    """Read budget_limit_per_run from config.yaml, default $1.00."""
    config_path = Path("config.yaml")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
            return float(config.get("budget_limit_per_run", 1.0))
        except Exception:
            pass
    return 1.0


def _read_env_state() -> Dict[str, str]:
    """Read current .env file state."""
    env_path = Path(".env")
    state = {}
    if env_path.exists():
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        state[key.strip()] = value.strip()
        except Exception:
            pass
    return state
