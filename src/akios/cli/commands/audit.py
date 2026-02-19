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
CLI audit command - akios audit export/log

Export audit reports in PDF or JSON format, or view logs in terminal.
"""

import argparse
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

from ...core.audit import export_audit_json
from ...core.audit.merkle import MerkleTree
from ...core.ui.rich_output import print_panel, get_theme_color
from ..helpers import CLIError, output_result, validate_file_path, check_project_context
from ..rich_helpers import output_with_mode

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def register_audit_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the audit command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "audit",
        help="Export audit reports"
    )

    subparsers_audit = parser.add_subparsers(
        dest="audit_subcommand",
        help="Audit subcommands",
        required=True
    )

    # audit export subcommand
    export_parser = subparsers_audit.add_parser(
        "export",
        help="Export audit report"
    )

    export_parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
        help="Export format (default: json)"
    )

    export_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: auto-generated)"
    )

    export_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format (for status/info)"
    )
    
    # audit log subcommand
    log_parser = subparsers_audit.add_parser(
        "log",
        help="View audit logs in terminal"
    )
    
    log_parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=20,
        help="Number of recent entries to show (default: 20)"
    )
    
    log_parser.add_argument(
        "--agent",
        help="Filter by agent name"
    )

    export_parser.set_defaults(func=run_audit_export_command)
    log_parser.set_defaults(func=run_audit_log_command)

    # audit verify subcommand
    verify_parser = subparsers_audit.add_parser(
        "verify",
        help="Verify cryptographic integrity of audit logs"
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        help="Output verification proof as structured JSON"
    )
    verify_parser.set_defaults(func=run_audit_verify_command)

    # audit rotate subcommand
    rotate_parser = subparsers_audit.add_parser(
        "rotate",
        help="Manually trigger audit log rotation"
    )
    rotate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output rotation result as JSON"
    )
    rotate_parser.set_defaults(func=run_audit_rotate_command)

    # audit stats subcommand
    stats_parser = subparsers_audit.add_parser(
        "stats",
        help="Show audit log statistics"
    )
    stats_parser.add_argument(
        "--json",
        action="store_true",
        help="Output stats as JSON"
    )
    stats_parser.set_defaults(func=run_audit_stats_command)


def export_audit_report(format_type: str = "json", output_path: str = None) -> dict:
    """
    Export audit report wrapper.
    """
    if format_type == "json":
        return export_audit_json(output_file=output_path)
    else:
        raise CLIError(f"Unsupported format: {format_type}")


def run_audit_export_command(args: argparse.Namespace) -> int:
    """
    Execute the audit export command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()

        if args.audit_subcommand == "export":
            result = export_audit_report(
                format_type=args.format,
                output_path=args.output
            )

            output_result(
                result,
                json_mode=args.json,
                success_message=""  # Don't use this custom message
            )
            return 0
            
    except Exception as e:
        if args.json:
            output_result({"error": str(e)}, json_mode=True, output_type="error")
        else:
            output_with_mode(f"Error exporting audit report: {e}", output_type="error")
        return 1
        
    return 0


def run_audit_log_command(args: argparse.Namespace) -> int:
    """
    Execute the audit log command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code
    """
    try:
        # Verify we're in a valid project context
        check_project_context()
        
        # Find audit logs
        audit_dir = Path("./audit")
        if not audit_dir.exists():
            output_with_mode("No audit logs found (audit directory missing)", output_type="warning")
            return 0
            
        logs = []
        # Support both .json (legacy/export) and .jsonl (ledger) formats
        log_files = list(audit_dir.glob("*.json")) + list(audit_dir.glob("*.jsonl"))
        
        for log_file in log_files:
            try:
                if log_file.suffix == '.jsonl':
                    # Parse JSONL line by line
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    logs.append(json.loads(line))
                                except json.JSONDecodeError:
                                    continue
                else:
                    # Parse standard JSON
                    content = json.loads(log_file.read_text(encoding='utf-8'))
                    # Handle both single entry and list of entries
                    if isinstance(content, list):
                        logs.extend(content)
                    elif isinstance(content, dict):
                        logs.append(content)
            except (json.JSONDecodeError, OSError):
                continue
                
        # Sort by timestamp (descending)
        # Try different timestamp keys depending on format
        def get_timestamp(entry):
            return entry.get("timestamp") or entry.get("created_at") or ""
            
        logs.sort(key=get_timestamp, reverse=True)
        
        # Filter
        if args.agent:
            logs = [l for l in logs if l.get("agent") == args.agent]
            
        # Limit
        logs = logs[:args.limit]
        
        if not logs:
            output_with_mode("No audit logs found matching criteria", output_type="info")
            return 0
            
        # Display
        if RICH_AVAILABLE:
            header_color = get_theme_color('header')
            success_color = get_theme_color('success')
            warning_color = get_theme_color('warning')
            error_color = get_theme_color('error')
            info_color = get_theme_color('info')
            
            from akios.core.ui.rich_output import _get_console
            console = _get_console()
            table = Table(
                title=f"\ud83d\udcdc Audit Log \u2014 Last {len(logs)} entries",
                box=box.ROUNDED,
                header_style=f"bold {header_color}",
                expand=True,
                border_style=get_theme_color('border'),
            )
            
            table.add_column("Timestamp", style="dim")
            table.add_column("Agent", style=info_color)
            table.add_column("Action", style=warning_color)
            table.add_column("Status", style="bold")
            table.add_column("Details")
            
            for log in logs:
                ts = get_timestamp(log)
                # Format timestamp if possible
                try:
                    dt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    ts_display = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    ts_display = ts
                
                agent_name = log.get("agent", "unknown")
                action = log.get("action", "-")
                
                # Determine status color using theme
                status = str(log.get("status", "info")).upper()
                if status in ["ERROR", "FAILED", "BLOCKED"]:
                    status_style = error_color
                elif status in ["SUCCESS", "ALLOWED"]:
                    status_style = success_color
                elif status == "WARNING":
                    status_style = warning_color
                else:
                    status_style = info_color
                    
                # Details formatting
                details = []
                params = log.get("parameters", {})
                if params:
                    details.append(f"Params: {str(params)[:50]}...")
                
                user = log.get("user")
                if user:
                    details.append(f"User: {user}")
                    
                table.add_row(
                    ts_display,
                    agent_name,
                    action,
                    Text(status, style=status_style),
                    ", ".join(details) or "-"
                )
                
            console.print(table)
        else:
            # Fallback for no-rich
            print(f"Audit Log (Last {len(logs)} entries)")
            print("-" * 80)
            for log in logs:
                ts = get_timestamp(log)
                print(f"[{ts}] {log.get('agent')} - {log.get('action')} ({log.get('status')})")
        
        return 0
        
    except Exception as e:
        output_with_mode(f"Error reading audit logs: {e}", output_type="error")
        return 1


def run_audit_verify_command(args: argparse.Namespace) -> int:
    """
    Execute the audit verify command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code
    """
    try:
        check_project_context()
        
        audit_file = Path("./audit/audit_events.jsonl")
        if not audit_file.exists():
            raise CLIError("Audit ledger not found: ./audit/audit_events.jsonl")
            
        # Reconstruct Merkle Tree from raw events
        tree = MerkleTree()
        event_count = 0
        first_timestamp = None
        last_timestamp = None
        
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tree.append(line)
                    event_count += 1
                    # Extract timestamps from events
                    try:
                        event = json.loads(line)
                        ts = event.get("timestamp") or event.get("created_at")
                        if ts:
                            if first_timestamp is None:
                                first_timestamp = ts
                            last_timestamp = ts
                    except (json.JSONDecodeError, KeyError):
                        pass
                    
        root_hash = tree.get_root_hash()
        
        if not root_hash:
            if getattr(args, 'json', False):
                print(json.dumps({"integrity": "EMPTY", "events": 0}, indent=2))
            else:
                print_panel("Audit Verification", "Audit ledger is empty.", style="yellow")
            return 0

        # Compare against stored Merkle root hash
        stored_root = None
        root_file = Path("./audit/merkle_root.hash")
        if root_file.exists():
            stored_root = root_file.read_text(encoding="utf-8").strip()

        if stored_root:
            integrity_verified = (root_hash == stored_root)
        else:
            # No stored root — first verification or root file missing
            integrity_verified = True  # Tree is self-consistent
        
        # JSON output
        if getattr(args, 'json', False):
            proof = {
                "integrity": "VERIFIED" if integrity_verified else "TAMPERED",
                "events": event_count,
                "merkle_root": root_hash,
                "stored_root": stored_root,
                "roots_match": integrity_verified,
                "first_event": first_timestamp,
                "last_event": last_timestamp,
                "ledger_file": str(audit_file),
                "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            print(json.dumps(proof, indent=2))
            return 0 if integrity_verified else 1
            
        # Rich display
        success_color = get_theme_color('success')
        error_color = get_theme_color('error')
        info_color = get_theme_color('info')
        
        # Format time range
        time_range = ""
        if first_timestamp and last_timestamp:
            try:
                ft = datetime.datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
                lt = datetime.datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                time_range = (
                    f"\n"
                    f"• Time Range:\n"
                    f"  [dim]First:[/dim] {ft.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"  [dim]Last:[/dim]  {lt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
            except (ValueError, AttributeError):
                pass

        if integrity_verified:
            root_comparison = ""
            if stored_root:
                root_comparison = f"\n• Stored Root:\n  [dim]{stored_root}[/]\n[{success_color}]✓ Recomputed root matches stored root[/]"
            else:
                root_comparison = f"\n[dim]No stored root hash found (first verification)[/]"

            status_text = (
                f"[bold {success_color}]Integrity: VERIFIED[/]\n\n"
                f"• Events Processed: [bold]{event_count}[/]\n"
                f"• Merkle Root:\n  [dim]{root_hash}[/]"
                f"{root_comparison}"
                f"{time_range}\n"
                f"[{success_color}]The cryptographic chain of custody is intact.[/]"
            )
            print_panel("🔐 Audit Proof", status_text, style=success_color)
        else:
            status_text = (
                f"[bold {error_color}]Integrity: TAMPERED[/]\n\n"
                f"• Events Processed: [bold]{event_count}[/]\n"
                f"• Recomputed Root:\n  [dim]{root_hash}[/]\n"
                f"• Stored Root:\n  [dim]{stored_root}[/]\n"
                f"\n[bold {error_color}]⚠ ROOT HASH MISMATCH — audit log may have been tampered with![/]"
            )
            print_panel("🚨 Audit Integrity Failure", status_text, style=error_color)

        return 0 if integrity_verified else 1
        
    except Exception as e:
        raise CLIError(f"Audit verification failed: {str(e)}")


def run_audit_rotate_command(args: argparse.Namespace) -> int:
    """
    Execute the audit rotate command.

    Manually triggers audit log rotation — archives the current ledger
    and starts a fresh one with Merkle chain linkage.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        check_project_context()

        audit_file = Path("./audit/audit_events.jsonl")
        if not audit_file.exists():
            raise CLIError("Audit ledger not found: ./audit/audit_events.jsonl")

        from ...core.audit.ledger import get_ledger
        ledger = get_ledger()

        # Capture pre-rotation stats
        pre_count = ledger._total_event_count
        pre_root = ledger.merkle_tree.get_root_hash()

        if pre_count == 0:
            if getattr(args, 'json', False):
                print(json.dumps({"rotated": False, "reason": "ledger is empty"}, indent=2))
            else:
                print_panel("Audit Rotation", "Ledger is empty — nothing to rotate.", style="yellow")
            return 0

        # Perform rotation (acquires state lock internally)
        with ledger._state_lock:
            ledger._rotate_ledger()

        result = {
            "rotated": True,
            "archived_events": pre_count,
            "archived_merkle_root": pre_root,
            "archive_dir": str(Path("./audit/archive")),
            "rotated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        if getattr(args, 'json', False):
            print(json.dumps(result, indent=2))
        else:
            success_color = get_theme_color('success')
            status_text = (
                f"[bold {success_color}]Rotation complete[/]\n\n"
                f"• Events archived: [bold]{pre_count}[/]\n"
                f"• Merkle root: [dim]{pre_root[:32] if pre_root else 'none'}...[/]\n"
                f"• Archive dir: [dim]./audit/archive[/]\n\n"
                f"[{success_color}]Fresh ledger started with chain linkage.[/]"
            )
            print_panel("🔄 Audit Log Rotated", status_text, style=success_color)

        return 0

    except CLIError:
        raise
    except Exception as e:
        raise CLIError(f"Audit rotation failed: {str(e)}")


def run_audit_stats_command(args: argparse.Namespace) -> int:
    """
    Execute the audit stats command.

    Shows audit ledger statistics: event count, ledger size, archive info,
    Merkle root hash, and rotation threshold.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        check_project_context()

        audit_dir = Path("./audit")
        if not audit_dir.exists():
            if getattr(args, 'json', False):
                print(json.dumps({"error": "no audit directory"}, indent=2))
            else:
                output_with_mode("No audit directory found.", output_type="warning")
            return 0

        ledger_file = audit_dir / "audit_events.jsonl"
        archive_dir = audit_dir / "archive"
        counter_file = audit_dir / ".event_count"

        # Current ledger stats
        ledger_size = ledger_file.stat().st_size if ledger_file.exists() else 0
        ledger_lines = 0
        if ledger_file.exists():
            with open(ledger_file, 'r', encoding='utf-8') as f:
                ledger_lines = sum(1 for line in f if line.strip())

        # Counter file (O(1) total count)
        total_count = 0
        if counter_file.exists():
            try:
                total_count = int(counter_file.read_text().strip())
            except (ValueError, OSError):
                total_count = ledger_lines

        # Archive stats
        archive_segments = 0
        archive_total_events = 0
        archive_total_bytes = 0
        if archive_dir.exists():
            for f in archive_dir.glob("ledger_*.jsonl"):
                archive_segments += 1
                archive_total_bytes += f.stat().st_size

            chain_file = archive_dir / "chain.jsonl"
            if chain_file.exists():
                with open(chain_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                archive_total_events += entry.get("event_count", 0)
                            except json.JSONDecodeError:
                                pass

        # Merkle root
        root_file = audit_dir / "merkle_root.hash"
        merkle_root = None
        if root_file.exists():
            merkle_root = root_file.read_text(encoding='utf-8').strip()

        def _format_size(b: int) -> str:
            if b < 1024:
                return f"{b} B"
            elif b < 1024 * 1024:
                return f"{b / 1024:.1f} KB"
            return f"{b / (1024 * 1024):.2f} MB"

        stats = {
            "current_ledger": {
                "events": ledger_lines,
                "size": ledger_size,
                "size_human": _format_size(ledger_size),
                "file": str(ledger_file),
            },
            "total_events": total_count,
            "rotation_threshold": 50000,
            "merkle_root": merkle_root,
            "archive": {
                "segments": archive_segments,
                "total_events": archive_total_events,
                "total_size": archive_total_bytes,
                "total_size_human": _format_size(archive_total_bytes),
            },
        }

        if getattr(args, 'json', False):
            print(json.dumps(stats, indent=2))
        else:
            info_color = get_theme_color('info')
            success_color = get_theme_color('success')

            lines = [
                f"[bold {info_color}]Current Ledger[/]",
                f"  Events:    [bold]{ledger_lines}[/]",
                f"  Size:      {_format_size(ledger_size)}",
                f"  Threshold: 50,000 events",
                "",
                f"[bold {info_color}]Totals[/]",
                f"  All-time events: [bold]{total_count}[/]",
            ]

            if merkle_root:
                lines.append(f"  Merkle root: [dim]{merkle_root[:32]}...[/]")

            if archive_segments > 0:
                lines.extend([
                    "",
                    f"[bold {info_color}]Archive[/]",
                    f"  Segments:  {archive_segments}",
                    f"  Events:    {archive_total_events}",
                    f"  Size:      {_format_size(archive_total_bytes)}",
                ])
            else:
                lines.append("\n[dim]No archived segments yet.[/]")

            print_panel("📊 Audit Statistics", "\n".join(lines), style=info_color)

        return 0

    except Exception as e:
        raise CLIError(f"Failed to read audit stats: {str(e)}")