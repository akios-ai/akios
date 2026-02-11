"""
AKIOS Brand Header.
Modern, minimal, typographic. No ASCII art.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from akios.core.ui.colors import Colors

# First-run marker location
CONFIG_DIR = Path.home() / ".akios"
INITIALIZED_FILE = CONFIG_DIR / ".initialized"

TAGLINE = "Secure AI Runtime v1.0"

def should_show_logo() -> bool:
    """
    Check if logo should be displayed.
    
    Conditions:
    - First run (no ~/.akios/.initialized)
    - TTY available (not piped)
    - Not in CI/CD (CI, GITHUB_ACTIONS, etc.)
    - Not --quiet mode (check via sys.argv)
    
    Returns:
        True if logo should be shown
    """
    # Check first-run status
    try:
        if INITIALIZED_FILE.exists():
            return False
    except Exception:
        # If we can't check, assume not first run
        return False
    
    # Check TTY
    if not sys.stdout.isatty():
        return False
    
    # Check CI/CD environment
    ci_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", 
               "TRAVIS", "JENKINS_HOME", "BUILDKITE"]
    if any(os.getenv(var) for var in ci_vars):
        return False
    
    # Check --quiet flag
    if "--quiet" in sys.argv or "-q" in sys.argv:
        return False
    
    return True


def mark_initialized() -> None:
    """
    Create ~/.akios/.initialized file to mark first run complete.
    
    File contains timestamp of first run for audit purposes.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        INITIALIZED_FILE.write_text(
            f"AKIOS initialized: {datetime.now(timezone.utc).isoformat()}\n"
        )
    except Exception:
        # Silent fail - don't break CLI if can't write
        pass


def show_logo() -> None:
    """
    Display AKIOS Modern Header.
    Clean typography, no ASCII art.
    """
    try:
        from rich.console import Console
        from rich.text import Text
        from rich.align import Align
        from .rich_output import get_theme_color
        
        console = Console()
        
        # Modern Header: AKIOS / Runtime
        # Header Color + Dim
        
        header = Text()
        header.append("AKIOS", style=f"bold {get_theme_color('header')}")
        header.append(" / ", style="dim")
        header.append(TAGLINE, style="dim")
        
        print()
        console.print(header)
        print()

    except ImportError:
        # Fallback if rich is not available
        print(f"\nAKIOS / {TAGLINE}\n")
    except Exception:
        # Silent fail
        pass
