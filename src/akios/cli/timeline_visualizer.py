"""
Workflow Timeline Visualization.

Beautiful ASCII timeline visualization of workflow execution.
Shows per-step duration, bottlenecks, and performance analysis.
"""

import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..core.ui.rich_output import get_theme_color


@dataclass
class TimelineStep:
    """Represents a workflow step in timeline."""
    name: str
    duration: float
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str = "success"
    index: int = 0


def parse_audit_event(audit_data: Dict) -> Tuple[str, float, List[TimelineStep]]:
    """
    Parse audit event to extract timeline data.
    
    Args:
        audit_data: Audit event dictionary
    
    Returns:
        Tuple of (workflow_name, total_duration, steps_list)
    """
    workflow_name = audit_data.get("workflow", "Unknown")
    total_duration = audit_data.get("total_duration", 0.0)
    
    steps = []
    step_data = audit_data.get("steps", [])
    
    for idx, step in enumerate(step_data, 1):
        timeline_step = TimelineStep(
            name=step.get("name", f"Step {idx}"),
            duration=step.get("duration", 0.0),
            start_time=step.get("start_time"),
            end_time=step.get("end_time"),
            status=step.get("status", "success"),
            index=idx
        )
        steps.append(timeline_step)
    
    return workflow_name, total_duration, steps


def calculate_bottleneck(steps: List[TimelineStep]) -> Optional[TimelineStep]:
    """
    Find the step that took longest (bottleneck).
    
    Args:
        steps: List of timeline steps
    
    Returns:
        Step with longest duration or None
    """
    if not steps:
        return None
    return max(steps, key=lambda x: x.duration)


def format_percentage(duration: float, total: float) -> str:
    """
    Format percentage of total time.
    
    Args:
        duration: Step duration
        total: Total duration
    
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0%"
    return f"{(duration / total) * 100:.0f}%"


def create_duration_bar(
    duration: float,
    total: float,
    width: int = 30
) -> str:
    """
    Create ASCII bar for duration visualization.
    
    Args:
        duration: Step duration
        total: Total duration
        width: Width of bar in characters
    
    Returns:
        ASCII bar string
    """
    if total == 0:
        return "░" * width
    
    percentage = duration / total
    filled = int(percentage * width)
    filled = max(1, min(filled, width))
    empty = width - filled
    
    return "█" * filled + "░" * empty


def render_timeline(
    audit_data: Dict,
    json_mode: bool = False,
    width: Optional[int] = None
) -> None:
    """
    Render workflow timeline visualization.
    
    Args:
        audit_data: Audit event dictionary
        json_mode: Output as JSON
        width: Console width override
    """
    if json_mode:
        _render_timeline_json(audit_data)
        return
    
    if not RICH_AVAILABLE or not sys.stdout.isatty():
        _render_timeline_plain(audit_data)
        return
    
    _render_timeline_rich(audit_data, width)


def _render_timeline_rich(audit_data: Dict, width: Optional[int] = None) -> None:
    """Render timeline with Rich styling."""
    console = Console(width=width) if width else Console()
    
    workflow_name, total_duration, steps = parse_audit_event(audit_data)
    
    if not steps:
        console.print(f"[{get_theme_color('warning')}]No steps found in audit data[/{get_theme_color('warning')}]")
        return
    
    bottleneck = calculate_bottleneck(steps)
    
    # Header panel
    header_text = f"Workflow: {workflow_name}"
    if audit_data.get("end_time"):
        header_text += f" | Completed: {audit_data['end_time']}"
    header_text += f" | Total: [bold]{total_duration:.2f}s[/bold]"
    
    console.print(Panel(header_text, style=get_theme_color("header"), expand=False))
    
    # Timeline section
    console.print(f"\n[bold {get_theme_color('header')}]Timeline (Execution Order):[/bold {get_theme_color('header')}]\n")
    
    for i, step in enumerate(steps):
        # Status indicator
        status_icon = "✓" if step.status == "success" else "✗"
        status_color = get_theme_color("success") if step.status == "success" else get_theme_color("error")
        
        # Progress bar
        bar = create_duration_bar(step.duration, total_duration, width=25)
        
        # Percentage
        pct = format_percentage(step.duration, total_duration)
        
        # Highlight bottleneck
        is_bottleneck = step == bottleneck
        slowest_marker = f" [bold {get_theme_color('error')}]← SLOWEST[/bold {get_theme_color('error')}]" if is_bottleneck else ""
        
        # Step line
        step_line = (
            f"[{status_color}]{status_icon}[/{status_color}] "
            f"{i+1:2d}. [bold]{step.name:<25}[/bold] "
            f"[{bar}] {step.duration:.2f}s ({pct}){slowest_marker}"
        )
        console.print(step_line)
        
        # Arrow between steps
        if i < len(steps) - 1:
            console.print("     " + " " * 25 + "↓")
    
    # Bottleneck analysis
    if bottleneck:
        pct = format_percentage(bottleneck.duration, total_duration)
        console.print(f"\n[yellow]💡 Bottleneck:[/yellow] [bold]{bottleneck.name}[/bold] "
                     f"({pct} of total time)")
        
        # Optimization suggestion
        if bottleneck.name.lower().startswith("call"):
            suggestion = "Consider batch processing or parallel execution"
        elif bottleneck.name.lower().startswith("parse"):
            suggestion = "Optimize parsing logic or enable caching"
        elif bottleneck.name.lower().startswith("format"):
            suggestion = "Simplify output formatting"
        else:
            suggestion = "Profile this step to identify optimization opportunities"
        
        console.print(f"[cyan]→ Suggestion:[/cyan] {suggestion}")


def _render_timeline_plain(audit_data: Dict) -> None:
    """Render timeline as plain text (fallback)."""
    workflow_name, total_duration, steps = parse_audit_event(audit_data)
    
    if not steps:
        print("No steps found in audit data")
        return
    
    bottleneck = calculate_bottleneck(steps)
    
    print(f"\nWorkflow: {workflow_name}")
    print(f"Total: {total_duration:.2f}s")
    print("\nTimeline (Execution Order):\n")
    
    for i, step in enumerate(steps, 1):
        pct = format_percentage(step.duration, total_duration)
        status = "✓" if step.status == "success" else "✗"
        slowest = " (SLOWEST)" if step == bottleneck else ""
        print(f"{status} {i}. {step.name:<25} {step.duration:.2f}s ({pct}){slowest}")
    
    if bottleneck:
        pct = format_percentage(bottleneck.duration, total_duration)
        print(f"\nBottleneck: {bottleneck.name} ({pct} of total time)")


def _render_timeline_json(audit_data: Dict) -> None:
    """Render timeline as JSON."""
    workflow_name, total_duration, steps = parse_audit_event(audit_data)
    bottleneck = calculate_bottleneck(steps)
    
    output = {
        "workflow": workflow_name,
        "total_duration": total_duration,
        "steps": [
            {
                "index": step.index,
                "name": step.name,
                "duration": step.duration,
                "percentage": (step.duration / total_duration * 100) if total_duration > 0 else 0,
                "status": step.status,
                "is_bottleneck": step == bottleneck
            }
            for step in steps
        ],
        "bottleneck": {
            "name": bottleneck.name,
            "duration": bottleneck.duration,
            "percentage": (bottleneck.duration / total_duration * 100) if bottleneck and total_duration > 0 else 0
        } if bottleneck else None
    }
    
    print(json.dumps(output, indent=2))


def render_timeline_file(
    file_path: str,
    json_mode: bool = False,
    width: Optional[int] = None
) -> bool:
    """
    Load audit file and render timeline.
    
    Args:
        file_path: Path to audit JSON file
        json_mode: Output as JSON
        width: Console width override
    
    Returns:
        True on success, False on error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
        
        render_timeline(audit_data, json_mode=json_mode, width=width)
        return True
    except FileNotFoundError:
        print(f"Error: Audit file not found: {file_path}", file=sys.stderr)
        return False
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in audit file: {file_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def compare_timelines(
    audit_data_list: List[Dict],
    json_mode: bool = False
) -> None:
    """
    Compare multiple timeline runs.
    
    Args:
        audit_data_list: List of audit events
        json_mode: Output as JSON
    """
    if not audit_data_list:
        print("No audit data to compare")
        return
    
    if json_mode:
        comparisons = []
        for audit_data in audit_data_list:
            workflow, total_duration, steps = parse_audit_event(audit_data)
            comparisons.append({
                "workflow": workflow,
                "total_duration": total_duration,
                "step_count": len(steps),
                "timestamp": audit_data.get("end_time")
            })
        print(json.dumps(comparisons, indent=2))
        return
    
    if not RICH_AVAILABLE or not sys.stdout.isatty():
        _compare_timelines_plain(audit_data_list)
        return
    
    _compare_timelines_rich(audit_data_list)


def _compare_timelines_plain(audit_data_list: List[Dict]) -> None:
    """Compare timelines as plain text."""
    print("\nWorkflow Comparison:\n")
    for i, audit_data in enumerate(audit_data_list, 1):
        workflow, total_duration, steps = parse_audit_event(audit_data)
        print(f"Run {i}: {workflow} - {total_duration:.2f}s ({len(steps)} steps)")


def _compare_timelines_rich(audit_data_list: List[Dict]) -> None:
    """Compare timelines with Rich styling."""
    console = Console()
    
    # Create comparison table
    table = Table(title="Workflow Timeline Comparison")
    table.add_column("Run", style=get_theme_color("info"))
    table.add_column("Workflow", style=get_theme_color("security"))
    table.add_column("Total Time", style=get_theme_color("success"))
    table.add_column("Steps", style=get_theme_color("warning"))
    table.add_column("Timestamp", style=get_theme_color("info"))
    
    for i, audit_data in enumerate(audit_data_list, 1):
        workflow, total_duration, steps = parse_audit_event(audit_data)
        timestamp = audit_data.get("end_time", "Unknown")
        
        table.add_row(
            str(i),
            workflow,
            f"{total_duration:.2f}s",
            str(len(steps)),
            timestamp
        )
    
    console.print(table)


def get_timeline_summary(audit_data: Dict) -> Dict:
    """
    Get summary statistics from timeline.
    
    Args:
        audit_data: Audit event dictionary
    
    Returns:
        Summary dictionary with statistics
    """
    workflow_name, total_duration, steps = parse_audit_event(audit_data)
    bottleneck = calculate_bottleneck(steps)
    
    if not steps:
        return {
            "workflow": workflow_name,
            "total_duration": 0,
            "step_count": 0
        }
    
    durations = [s.duration for s in steps]
    return {
        "workflow": workflow_name,
        "total_duration": total_duration,
        "step_count": len(steps),
        "average_step_duration": sum(durations) / len(durations),
        "min_step_duration": min(durations),
        "max_step_duration": max(durations),
        "bottleneck_step": bottleneck.name if bottleneck else None,
        "bottleneck_duration": bottleneck.duration if bottleneck else None,
        "bottleneck_percentage": (bottleneck.duration / total_duration * 100) if bottleneck and total_duration > 0 else 0
    }
