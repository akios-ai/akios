"""
Rich terminal output utilities for AKIOS CLI.
"""
import os
import re
import sys
import time
import contextlib
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Global console instance
_console = None

def _get_console():
    global _console
    if _console is None and RICH_AVAILABLE:
        # Check for forced color
        force_terminal = os.environ.get("FORCE_COLOR") == "1" or os.environ.get("CLICOLOR_FORCE") == "1"
        # Use stderr for UI elements to keep stdout clean for data piping
        _console = Console(stderr=True, force_terminal=force_terminal if force_terminal else None)
    return _console

def is_rich_available() -> bool:
    return RICH_AVAILABLE

def _strip_rich_markup(text: str) -> str:
    """Remove Rich markup tags like [bold], [dim], [/#04B1DC], [/], etc."""
    return re.sub(r'\[/?[^\]]*\]', '', text)

def _should_use_rich() -> bool:
    """
    Determine if Rich UI should be used based on environment.
    """
    if not RICH_AVAILABLE:
        return False
    if os.environ.get('NO_COLOR'):
        return False
    
    # Respect forced color
    if os.environ.get('FORCE_COLOR') == '1' or os.environ.get('CLICOLOR_FORCE') == '1':
        return True
        
    if not sys.stderr.isatty():
        return False
    return True

def get_theme_color(name: str) -> str:
    """
    Get color for semantic theme element.
    """
    # Minimal theme mapping - strictly adhering to design system
    # Using specific hex codes from COLOR_ARCHITECTURE_V1.0.md
    theme = {
        "header": "bold #04B1DC",    # Cyan
        "success": "#2ECC71",        # Green
        "warning": "#F39C12",        # Orange
        "error": "#E74C3C",          # Red
        "info": "#04B1DC",           # Cyan (Info is Cyan in AKIOS)
        "primary": "#04B1DC",        # Cyan (alias for info)
        "security": "#E91E63",       # Magenta
        "highlight": "#9B59B6",      # Purple
        "panel": "#04B1DC",          # Cyan
        "border": "dim #04B1DC",     # Dim Cyan
        "banner": "#04B1DC",         # Cyan
        "dim": "dim",                # Dim text
    }
    return theme.get(name, "white")

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_theme_ansi(name: str) -> str:
    """
    Get ANSI escape code for semantic theme element.
    Returns the complete ANSI sequence (including bold/dim attributes + color).
    """
    style = get_theme_color(name)
    ansi_codes = []
    
    # Handle attributes
    if "bold" in style:
        ansi_codes.append("1")
    if "dim" in style:
        ansi_codes.append("2")
        
    # Handle color
    import re
    hex_match = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}', style)
    if hex_match:
        hex_color = hex_match.group(0)
        r, g, b = hex_to_rgb(hex_color)
        ansi_codes.append(f"38;2;{r};{g};{b}")
        
    if not ansi_codes:
        return ""
        
    return f"\033[{';'.join(ansi_codes)}m"

ANSI_RESET = "\033[0m"

# ============================================================================
# STANDARD OUTPUT FUNCTIONS
# ============================================================================

def print_panel(title: str, content: str, style: Optional[str] = None):
    """Print a styled panel."""
    if not _should_use_rich():
        clean = _strip_rich_markup(content)
        print(f"\n{'=' * 60}")
        print(title)
        print('=' * 60)
        print(clean)
        return
    
    style = style or get_theme_color("panel")
    # Extract just the color part for the border if it has attributes like 'bold'
    # rich.panel.Panel border_style expects a style string
    
    # Use theme header color for the title
    header_style = get_theme_color("header")
    
    panel = Panel(
        content, 
        title=f"[{header_style}]{title}[/]", 
        border_style=style, 
        box=box.ROUNDED,
        padding=(1, 2)
    )
    _get_console().print(panel)

def print_table(data: List[Dict[str, Any]], title: Optional[str] = None, columns: Optional[List[str]] = None):
    """Print a styled table."""
    if not _should_use_rich() or not data:
        if title: print(f"\n--- {_strip_rich_markup(title)} ---")
        if data:
            # Determine columns
            headers = columns if columns else list(data[0].keys())
            display_headers = []
            for h in headers:
                display = str(h).replace('_', ' ')
                if display == display.lower():
                    display = display.title()
                display_headers.append(display)
            
            # Print header row
            print("  ".join(f"{dh:<20}" for dh in display_headers))
            print("-" * (22 * len(display_headers)))
            
            for row in data:
                values = [_strip_rich_markup(str(row.get(h, ""))) for h in headers]
                print("  ".join(f"{v:<20}" for v in values))
        print("")
        return

    table = Table(
        title=title, 
        box=box.ROUNDED, 
        header_style=get_theme_color("header"),
        border_style=get_theme_color("border"),
        expand=True
    )
    
    # Add columns
    if columns:
        headers = columns
    else:
        # Add columns based on first row
        headers = list(data[0].keys())
        
    for h in headers:
        # Preserve original casing for headers like 'PII Type'
        display = str(h).replace('_', ' ')
        # Only title-case if fully lowercase
        if display == display.lower():
            display = display.title()
        table.add_column(display)
    
    for row in data:
        table.add_row(*[str(row.get(h, "")) for h in headers])
        
    _get_console().print(table)

def print_success(message: str, details: Optional[List[str]] = None):
    """Print a success message."""
    if not _should_use_rich():
        print(f"SUCCESS: {_strip_rich_markup(message)}")
        if details:
            for d in details: print(f"  {_strip_rich_markup(d)}")
        return
    
    _get_console().print(f"[bold {get_theme_color('success')}]✅ SUCCESS:[/] [{get_theme_color('success')}]{message}[/]")
    if details:
        for d in details:
            _get_console().print(f"  [dim]{d}[/]")

def print_warning(message: str, details: Optional[List[str]] = None):
    """Print a warning message."""
    if not _should_use_rich():
        print(f"WARNING: {_strip_rich_markup(message)}")
        if details:
            for d in details: print(f"  {_strip_rich_markup(d)}")
        return
    
    _get_console().print(f"[{get_theme_color('warning')}]{message}[/]")
    if details:
        for d in details:
            _get_console().print(f"  [dim]{d}[/]")

def print_error(message: str, details: Optional[List[str]] = None):
    """Print an error message."""
    if not _should_use_rich():
        print(f"ERROR: {_strip_rich_markup(message)}")
        if details:
            for d in details: print(f"  {_strip_rich_markup(d)}")
        return
    
    _get_console().print(f"[{get_theme_color('error')}]{message}[/]")
    if details:
        for d in details:
            _get_console().print(f"  [dim]{d}[/]")

def print_info(message: str, details: Optional[List[str]] = None):
    """Print an info message."""
    if not _should_use_rich():
        print(f"INFO: {_strip_rich_markup(message)}")
        if details:
            for d in details: print(f"  {_strip_rich_markup(d)}")
        return
    
    _get_console().print(f"[{get_theme_color('info')}]{message}[/]")
    if details:
        for d in details:
            _get_console().print(f"  [dim]{d}[/]")

def print_banner(title: str, content: str, style: Optional[str] = None, box_style: Any = None):
    """Print a prominent banner for critical notifications."""
    if not _should_use_rich():
        print(f"\n*** {title} ***\n{_strip_rich_markup(content)}\n")
        return
    
    style = style or get_theme_color("banner")
    
    if box_style is None:
        box_style = box.ROUNDED
        
    panel = Panel(
        content,
        title=f"[bold {style}]{title}[/bold {style}]",
        style="white",
        expand=True,
        border_style=f"bold {style}",
        box=box_style,
        padding=(1, 2)
    )
    _get_console().print(panel)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_code(code: str, language: str = "python", title: Optional[str] = None):
    """Print syntax highlighted code."""
    if not _should_use_rich():
        if title: print(f"--- {title} ---")
        print(code)
        return
    
    from rich.syntax import Syntax
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    if title:
        _get_console().print(Panel(syntax, title=title, border_style=get_theme_color("panel"), box=box.ROUNDED))
    else:
        _get_console().print(syntax)

def print_pii_findings(findings: List[Dict[str, Any]]):
    """Print PII findings table."""
    if not findings:
        print_success("No PII detected.")
        return
        
    print_table(findings, title="PII DETECTED")

def print_audit_log(events: List[Dict[str, Any]]):
    """Print audit log table."""
    if not events:
        print_info("No audit events recorded.")
        return
        
    print_table(events, title="AUDIT LOG")

def progress_bar(iterable, description: str = "Processing..."):
    """
    Simple progress bar wrapper for backward compatibility.
    Prefer create_workflow_progress for workflows.
    """
    if not _should_use_rich():
        for item in iterable:
            yield item
        return

    from rich.progress import track
    for item in track(iterable, description=description, console=_get_console()):
        yield item

def clear_screen():
    """Clear the terminal screen."""
    if _should_use_rich():
        _get_console().clear()
    else:
        # Fallback for standard terminals
        os.system('cls' if os.name == 'nt' else 'clear')

def get_status_badge(status: str) -> str:
    """Get a colored status badge string."""
    status = status.lower()
    if status == "success":
        return f"[{get_theme_color('success')}]SUCCESS[/]"
    elif status == "error":
        return f"[{get_theme_color('error')}]ERROR[/]"
    elif status == "warning":
        return f"[{get_theme_color('warning')}]WARNING[/]"
    elif status == "info":
        return f"[{get_theme_color('info')}]INFO[/]"
    return f"[{get_theme_color('info')}]{status.upper()}[/]"

# ============================================================================
# BUDGET VISUALIZATION
# ============================================================================

def print_budget_progress(current_spending: float, budget_limit: float, title: str = "Budget Usage", show_warning: bool = True):
    """Print a budget usage progress bar."""
    if not _should_use_rich():
        percentage = (current_spending / budget_limit) * 100 if budget_limit > 0 else 0
        print(f"{title}: ${current_spending:.2f} / ${budget_limit:.2f} ({percentage:.1f}%)")
        return

    percentage = (current_spending / budget_limit) * 100 if budget_limit > 0 else 0
    
    # Determine color based on usage
    if percentage < 50:
        color = get_theme_color("success")
    elif percentage < 80:
        color = get_theme_color("warning")
    else:
        color = get_theme_color("error")
        
    # Create a custom progress bar for budget
    progress = Progress(
        TextColumn(f"[bold]{title}[/]"),
        BarColumn(bar_width=None, style="dim white", complete_style=color),
        TextColumn(f"[{color}]${current_spending:.2f}[/] / [dim]${budget_limit:.2f}[/]"),
        TextColumn(f"([{color}]{percentage:.1f}%[/])"),
        console=_get_console(),
        expand=True
    )
    
    progress.add_task("budget", total=budget_limit, completed=current_spending)
    _get_console().print(progress)

def print_cost_breakdown_table(breakdown_data: List[Dict[str, Any]], title: str = "COST BREAKDOWN"):
    """Print cost breakdown table."""
    if not breakdown_data:
        print_info("No cost data available.")
        return
        
    print_table(breakdown_data, title=title)

def print_spending_trend(trend_data, title: str = "7-DAY SPENDING TREND"):
    """Print spending trend as a summary panel."""
    if not trend_data:
        return
    
    # Handle dict from calculate_7day_trend
    if isinstance(trend_data, dict):
        daily_costs = trend_data.get('daily_costs', [])
        total = trend_data.get('total_7day', 0.0)
        avg = trend_data.get('avg_daily', 0.0)
        direction = trend_data.get('trend_direction', 'stable')
        
        arrow = {"up": "\u2191", "down": "\u2193", "stable": "\u2192"}.get(direction, "\u2192")
        color = {"up": get_theme_color('warning'), "down": get_theme_color('success'), "stable": get_theme_color('info')}.get(direction, get_theme_color('info'))
        
        content = (
            f"[{color}]{arrow} Trend: {direction.upper()}[/{color}]  \u2022  "
            f"Total: ${total:.4f}  \u2022  Avg/day: ${avg:.4f}"
        )
        print_panel(title, content, style=color)
    else:
        # List of dicts fallback
        print_table(trend_data, title=title)

# ============================================================================
# PROGRESS BARS
# ============================================================================

def create_workflow_progress(total_steps: int, description: str, disable: bool = False):
    """Create a progress bar for workflow execution."""
    if not _should_use_rich():
        # Return a dummy context manager compatible with rich.progress.Progress interface
        class DummyProgress:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def add_task(self, *args, **kwargs): return 0
            def update(self, *args, **kwargs): pass
        return DummyProgress()
        
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=_get_console(),
        disable=disable,
        transient=True
    )

def create_step_progress(description: str):
    """Create a progress bar for a single step."""
    if not _should_use_rich():
        class DummyProgress:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def add_task(self, *args, **kwargs): return 0
            def update(self, *args, **kwargs): pass
        return DummyProgress()

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=_get_console(),
        transient=True
    )

# ============================================================================
# LIVE DASHBOARD
# ============================================================================

class WorkflowDashboard:
    """
    Live dashboard for workflow execution visualization.
    Displays a persistent table of steps and their status.
    """
    def __init__(self, workflow_name: str, total_steps: int, steps_info: List[Dict[str, str]]):
        self.workflow_name = workflow_name
        self.total_steps = total_steps
        self.steps_info = steps_info
        self.current_step_idx = 0
        self.step_statuses = ["pending"] * total_steps
        self.step_durations = [0.0] * total_steps
        self.start_time = time.time()
        self.console = _get_console()
        
    def __rich__(self):
        """Generate the current dashboard view."""
        header_color = get_theme_color("header").replace("bold ", "")
        
        # Header
        header = Panel(
            f"[{get_theme_color('header')}]Workflow Execution: {self.workflow_name}[/]",
            style=get_theme_color("header"),
            box=box.ROUNDED,
            padding=(0, 1)
        )
        
        # Steps Table
        table = Table(
            show_header=True, 
            header_style=get_theme_color("header"),
            box=box.SIMPLE,
            expand=True,
            show_edge=False
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Agent", width=12)
        table.add_column("Action", width=15)
        table.add_column("Status", width=10)
        table.add_column("Duration", justify="right", width=10)
        
        for i, info in enumerate(self.steps_info):
            status = self.step_statuses[i]
            duration = self.step_durations[i]
            
            # Status styling
            if status == "pending":
                status_str = "[dim]Pending[/]"
                style = "dim"
                icon = "○"
            elif status == "running":
                status_str = f"[{header_color}]Running...[/]"
                style = header_color
                icon = "⟳"
            elif status == "success":
                status_str = f"[{get_theme_color('success')}]Success[/]"
                style = get_theme_color('success')
                icon = "✓"
            elif status == "error":
                status_str = f"[{get_theme_color('error')}]Failed[/]"
                style = get_theme_color('error')
                icon = "✗"
            else:
                status_str = status
                style = "white"
                icon = "?"
                
            # Current step highlight
            if i == self.current_step_idx and status == "running":
                row_style = "bold white"
            else:
                row_style = style if status != "pending" else "dim"
                
            duration_str = f"{duration:.2f}s" if duration > 0 else ""
            
            table.add_row(
                f"{i+1}",
                info['agent'],
                info['action'],
                f"{icon} {status_str}",
                duration_str,
                style=row_style
            )
            
        return Group(header, table)
    
    def set_running(self, step_idx: int):
        self.current_step_idx = step_idx
        self.step_statuses[step_idx] = "running"
        
    def set_success(self, step_idx: int, duration: float):
        self.step_statuses[step_idx] = "success"
        self.step_durations[step_idx] = duration
        
    def set_error(self, step_idx: int, duration: float):
        self.step_statuses[step_idx] = "error"
        self.step_durations[step_idx] = duration


@contextlib.contextmanager
def create_workflow_dashboard(workflow) -> Any:
    """
    Create a live dashboard context manager for workflow execution.
    Yields the dashboard controller.
    """
    if not _should_use_rich():
        # Fallback dummy
        class DummyDashboard:
            def set_running(self, *args): pass
            def set_success(self, *args): pass
            def set_error(self, *args): pass
        yield DummyDashboard()
        return

    # Extract step info
    steps_info = []
    for step in workflow.steps:
        steps_info.append({
            'agent': step.agent,
            'action': step.action
        })
        
    dashboard = WorkflowDashboard(
        workflow.name,
        len(workflow.steps),
        steps_info
    )
    
    # Use Live context manager
    with Live(
        dashboard,
        console=_get_console(),
        refresh_per_second=4,
        transient=False
    ) as live:
        yield dashboard
