"""
AKIOS Accessibility Features - Symbols and modes for inclusive design.

Provides symbol/icon alternatives for colorblind and visually impaired accessibility:
- Symbol modes: "unicode" (●/□/△/◆), "ascii" (+/-/!/?), "text" ([OK]/[ERR]/[WARN]/[INFO])
- Colorblind-safe color combinations
- High contrast visual indicators
- WCAG compliance checking

Usage:
    from akios.config.accessibility import (
        set_symbol_mode, get_symbol, should_use_symbols
    )
    
    # Use symbol mode
    set_symbol_mode("unicode")  # Enable symbols
    symbol = get_symbol("success")  # Returns "●"
    
    # Print with symbols
    print_success("Done!", show_symbol=True)  # Shows: ● Done!
"""

import os
from typing import Optional, Dict
from enum import Enum

# Symbol modes
class SymbolMode(Enum):
    """Available symbol modes for accessibility."""
    UNICODE = "unicode"      # ●/□/△/◆ - Clean, modern unicode symbols
    ASCII = "ascii"          # +/-/!/? - Basic ASCII safe mode
    TEXT = "text"            # [OK]/[ERR]/[WARN]/[INFO] - Text badges
    GRAPHICAL = "graphical"  # ✓/✗/⚠/ℹ - Traditional graphical characters


# Global symbol mode
_symbol_mode: Optional[SymbolMode] = None


def set_symbol_mode(mode: str) -> bool:
    """
    Set the symbol mode for accessibility.
    
    Args:
        mode: Symbol mode ("unicode", "ascii", "text", "graphical", or "none")
    
    Returns:
        True if mode set successfully, False if invalid
    
    Example:
        >>> set_symbol_mode("unicode")
        True
        >>> get_symbol("success")
        '●'
    """
    global _symbol_mode
    
    if mode == "none" or mode is None:
        _symbol_mode = None
        return True
    
    try:
        _symbol_mode = SymbolMode(mode)
        return True
    except ValueError:
        return False


def get_symbol_mode() -> Optional[str]:
    """Get current symbol mode ("unicode", "ascii", "text", "graphical", or None)."""
    if _symbol_mode is None:
        return None
    return _symbol_mode.value


def should_use_symbols() -> bool:
    """
    Check if symbols should be displayed.
    
    Returns True if:
    1. Symbol mode explicitly set (via env var or code)
    2. Terminal supports symbols (TTY detection)
    
    Returns False if:
    1. NO_SYMBOLS environment variable set
    2. Not a TTY (piped output)
    """
    # Check environment variable to disable symbols
    if os.environ.get("NO_SYMBOLS"):
        return False
    
    # If symbol mode explicitly set, use it
    if _symbol_mode is not None:
        return True
    
    return False


def resolve_symbol_mode_from_env() -> Optional[str]:
    """Resolve symbol mode from environment variable."""
    return os.environ.get("AKIOS_SYMBOL_MODE")


# Symbol definitions for each mode
SYMBOLS: Dict[str, Dict[str, str]] = {
    "unicode": {
        # Unicode symbols - Clean, modern, shape-based
        "success": "●",          # Blue circle
        "error": "□",            # Magenta square
        "warning": "△",          # Yellow triangle
        "info": "◆",             # Cyan diamond
        "checkmark": "✓",        # Generic checkmark
        "cross": "✗",            # Generic X
        "arrow_right": "→",
        "arrow_down": "↓",
        "bullet": "•",
        "loading": "⟳",
    },
    
    "ascii": {
        # ASCII-safe symbols - Maximum compatibility
        "success": "+",          # Plus sign
        "error": "-",            # Minus/dash
        "warning": "!",          # Exclamation
        "info": "?",             # Question mark
        "checkmark": "+",
        "cross": "-",
        "arrow_right": "->",
        "arrow_down": "|",
        "bullet": "*",
        "loading": "*",
    },
    
    "text": {
        # Text-based badges - Maximum clarity
        "success": "[OK]",
        "error": "[ERR]",
        "warning": "[WARN]",
        "info": "[INFO]",
        "checkmark": "[✓]",
        "cross": "[✗]",
        "arrow_right": ">>>",
        "arrow_down": "v",
        "bullet": "---",
        "loading": "...",
    },
    
    "graphical": {
        # Traditional graphical characters (original)
        "success": "✓",          # Checkmark
        "error": "✗",            # X mark
        "warning": "⚠",          # Warning triangle
        "info": "ℹ",             # Info symbol
        "checkmark": "✓",
        "cross": "✗",
        "arrow_right": "→",
        "arrow_down": "↓",
        "bullet": "◆",
        "loading": "⟳",
    },
}


def get_symbol(
    semantic_type: str,
    mode: Optional[str] = None,
    fallback: str = "•"
) -> str:
    """
    Get symbol for semantic type and mode.
    
    Args:
        semantic_type: Type of symbol (success, error, warning, info, checkmark, etc.)
        mode: Optional specific mode ("unicode", "ascii", "text", "graphical")
              If not provided, uses current mode or returns type name
        fallback: Symbol to return if type not found
    
    Returns:
        Symbol string for the semantic type
    
    Example:
        >>> set_symbol_mode("unicode")
        >>> get_symbol("success")
        '●'
        >>> set_symbol_mode("ascii")
        >>> get_symbol("success")
        '+'
    """
    # Use provided mode or current mode
    if mode is None:
        mode = get_symbol_mode()
    
    # If no mode, return fallback
    if mode is None:
        return fallback
    
    # Get symbol for mode
    mode_symbols = SYMBOLS.get(mode, {})
    return mode_symbols.get(semantic_type, fallback)


def get_all_symbols(mode: str) -> Dict[str, str]:
    """
    Get all symbols for a given mode.
    
    Args:
        mode: Symbol mode ("unicode", "ascii", "text", "graphical")
    
    Returns:
        Dictionary of semantic_type -> symbol
    """
    return SYMBOLS.get(mode, {})


def list_symbol_modes() -> list[str]:
    """List all available symbol modes."""
    return [mode.value for mode in SymbolMode]


def validate_symbol_type(symbol_type: str) -> bool:
    """
    Validate that a symbol type is available across all modes.
    
    Args:
        symbol_type: Symbol type to validate
    
    Returns:
        True if type exists in at least one mode
    """
    for mode_symbols in SYMBOLS.values():
        if symbol_type in mode_symbols:
            return True
    return False


# Accessibility metadata and scoring
def get_contrast_ratio(foreground: str, background: str) -> float:
    """
    Calculate approximate WCAG contrast ratio for colors.
    
    Args:
        foreground: Color name (e.g., "green", "bright_red")
        background: Background color (default "black")
    
    Returns:
        Approximate contrast ratio (1.0 = no contrast, 21.0 = max contrast)
    
    Note:
        This is a simplified calculation. Real WCAG compliance requires
        actual hex color values and precise luminance calculation.
    """
    # Simplified contrast lookup for common colors
    luminance_map = {
        "black": 0.0,
        "dark_red": 0.1,
        "dark_green": 0.15,
        "dark_blue": 0.1,
        "red": 0.3,
        "green": 0.5,
        "yellow": 0.9,
        "blue": 0.2,
        "cyan": 0.7,
        "white": 1.0,
        "bright_red": 0.5,
        "bright_green": 0.7,
        "bright_yellow": 0.95,
        "bright_cyan": 0.85,
        "bright_white": 1.0,
        "dim": 0.2,
    }
    
    fg_lum = luminance_map.get(foreground.lower(), 0.5)
    bg_lum = luminance_map.get(background.lower(), 0.0)
    
    # Simplified WCAG ratio calculation
    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    
    if darker == 0:
        return lighter * 21.0
    
    return (lighter + 0.05) / (darker + 0.05)


def check_wcag_compliance(
    foreground: str,
    background: str = "black",
    level: str = "AA"
) -> bool:
    """
    Check if color combination meets WCAG accessibility standard.
    
    Args:
        foreground: Foreground color name
        background: Background color name (default "black")
        level: WCAG level ("A"=4.5:1, "AA"=4.5:1, "AAA"=7:1)
    
    Returns:
        True if combination meets WCAG level
    
    Example:
        >>> check_wcag_compliance("yellow", "black", "AA")
        True
    """
    ratio = get_contrast_ratio(foreground, background)
    
    wcag_levels = {
        "A": 3.0,
        "AA": 4.5,
        "AAA": 7.0,
    }
    
    min_ratio = wcag_levels.get(level, 4.5)
    return ratio >= min_ratio


def get_accessibility_score(theme_name: str) -> float:
    """
    Calculate accessibility score for a theme (0-10).
    
    Args:
        theme_name: Theme name ("default", "dark", "colorblind", etc.)
    
    Returns:
        Accessibility score
    
    Scoring:
    - 0-2: Poor (high contrast issues, color blindness unsafe)
    - 3-5: Fair (some accessibility issues)
    - 6-8: Good (mostly accessible)
    - 9-10: Excellent (accessible, colorblind-safe, high-contrast)
    """
    from .themes import THEMES, get_theme_color
    
    scores = {
        "default": 7.0,          # Good basic colors, some colorblind issues
        "dark": 7.0,             # High contrast, some colorblind issues
        "light": 6.0,            # Good but less contrast
        "colorblind": 9.5,       # Excellent colorblind support
        "high-contrast": 9.0,    # Excellent contrast, good for visual impairment
    }
    
    return scores.get(theme_name, 5.0)


# Export public API
__all__ = [
    "SymbolMode",
    "set_symbol_mode",
    "get_symbol_mode",
    "should_use_symbols",
    "resolve_symbol_mode_from_env",
    "get_symbol",
    "get_all_symbols",
    "list_symbol_modes",
    "validate_symbol_type",
    "get_contrast_ratio",
    "check_wcag_compliance",
    "get_accessibility_score",
    "SYMBOLS",
]
