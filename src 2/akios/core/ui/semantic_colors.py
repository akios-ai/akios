"""
Semantic color system for AKIOS CLI output.

Each message type has a FIXED color that never changes, regardless of theme or environment.
This ensures users understand what each color means.

Semantic Colors:
- MAGENTA (#E91E63) = Security messages (🔒)
- CYAN (#04B1DC) = Information/branding (ℹ️)
- GREEN (#2ECC71) = Success (✓)
- ORANGE (#F39C12) = Warnings (⚠️)
- RED (#E74C3C) = Errors (✗)
- PURPLE (#9B59B6) = Highlights (★)
"""

from typing import Optional, List
import os
import sys


# ============================================================================
# SEMANTIC COLOR DEFINITIONS (NEVER CHANGE)
# ============================================================================

SEMANTIC_COLORS = {
    # Message category → Fixed color code
    "security": "#E91E63",      # Magenta - 🔒 security notices, PII protection, audit
    "info": "#04B1DC",          # Cyan - ℹ️ status updates, information (AKIOS brand)
    "success": "#2ECC71",       # Green - ✓ operations completed successfully
    "warning": "#F39C12",       # Orange - ⚠️ cautions, things to be aware of
    "error": "#E74C3C",         # Red - ✗ failures, errors, blocking issues
    "highlight": "#9B59B6",     # Purple - ★ important notices, new features
}

SEMANTIC_SYMBOLS = {
    "security": "🔒",
    "info": "ℹ️",
    "success": "✓",
    "warning": "⚠️",
    "error": "✗",
    "highlight": "★",
}


# ============================================================================
# COLOR SUPPORT DETECTION
# ============================================================================

def _should_use_colors() -> bool:
    """Determine if colors should be used based on environment."""
    # Respect NO_COLOR standard
    if os.environ.get('NO_COLOR'):
        return False
    
    # Check if stdout is a TTY
    if not sys.stdout.isatty():
        return False
    
    return True


# ============================================================================
# SEMANTIC OUTPUT FUNCTIONS (PUBLIC API)
# ============================================================================

def print_security(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print a security message in magenta.
    
    Use for: Security status, PII protection, audit logging, permissions
    Color: ALWAYS magenta (#E91E63)
    Symbol: ALWAYS 🔒
    
    Args:
        message: Main message to print
        details: Optional list of detail lines to print indented
    """
    _print_semantic("security", message, details)


def print_info(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print an information message in cyan.
    
    Use for: Status updates, system info, workflow progress
    Color: ALWAYS cyan (#04B1DC) - AKIOS brand color
    Symbol: ALWAYS ℹ️
    
    Args:
        message: Main message to print
        details: Optional list of detail lines to print indented
    """
    _print_semantic("info", message, details)


def print_success(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print a success message in green.
    
    Use for: Operations completed, confirmations
    Color: ALWAYS green (#2ECC71)
    Symbol: ALWAYS ✓
    
    Args:
        message: Main message to print
        details: Optional list of detail lines to print indented
    """
    _print_semantic("success", message, details)


def print_warning(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print a warning message in orange.
    
    Use for: Cautions, things to watch for
    Color: ALWAYS orange (#F39C12)
    Symbol: ALWAYS ⚠️
    
    Args:
        message: Main message to print
        details: Optional list of detail lines to print indented
    """
    _print_semantic("warning", message, details)


def print_error(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print an error message in red.
    
    Use for: Failures, blocking issues
    Color: ALWAYS red (#E74C3C)
    Symbol: ALWAYS ✗
    
    Args:
        message: Main message to print
        details: Optional list of detail lines to print indented
    """
    _print_semantic("error", message, details)


def print_highlight(message: str, details: Optional[List[str]] = None) -> None:
    """
    Print a highlight message in purple.
    
    Use for: Important notices, new features
    Color: ALWAYS purple (#9B59B6)
    Symbol: ALWAYS ★
    
    Args:
        message: Main message to print
        details: Optional list of detail lines to print indented
    """
    _print_semantic("highlight", message, details)


# ============================================================================
# INTERNAL IMPLEMENTATION
# ============================================================================

def _print_semantic(semantic_type: str, message: str, details: Optional[List[str]] = None) -> None:
    """
    Internal: Print message with semantic color and symbol.
    
    Args:
        semantic_type: "security", "info", "success", "warning", "error", "highlight"
        message: Message to print
        details: Optional list of detail lines
    """
    symbol = SEMANTIC_SYMBOLS.get(semantic_type, "•")
    color = SEMANTIC_COLORS.get(semantic_type, "white")
    
    use_colors = _should_use_colors()
    
    import sys
    
    if use_colors:
        try:
            from rich.console import Console
            console = Console(stderr=True)
            # Print main message with color
            console.print(f"[{color}]{symbol}[/{color}] [{color}]{message}[/{color}]")
            # Print details if provided
            if details:
                for detail in details:
                    console.print(f"  [{color}]{detail}[/{color}]")
        except (ImportError, Exception):
            # Fallback if Rich not available
            print(f"{symbol} {message}", file=sys.stderr)
            if details:
                for detail in details:
                    print(f"  {detail}", file=sys.stderr)
    else:
        # Plain text when colors disabled
        print(f"{symbol} {message}", file=sys.stderr)
        if details:
            for detail in details:
                print(f"  {detail}", file=sys.stderr)
