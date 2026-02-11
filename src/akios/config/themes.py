"""
Theme management for AKIOS CLI.

Provides dynamic color theming with built-in themes (default, dark, light)
and custom theme support via config.yaml.

Theme priorities:
1. CLI flag: --theme dark
2. Environment variable: AKIOS_THEME=dark
3. Config file: ui.theme
4. Default: "default"

Example:
    >>> from akios.config.themes import get_theme_color, load_theme
    >>> load_theme("dark")
    >>> color = get_theme_color("success")  # Returns "bright_green"
"""

import os
from typing import Dict, Any, Optional

# Global theme cache
_current_theme: Optional[str] = None
_theme_colors: Dict[str, str] = {}

# Built-in theme definitions
THEMES: Dict[str, Dict[str, str]] = {
    "default": {
        # Status colors
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "info": "cyan",
        
        # UI elements
        "primary": "cyan",
        "border": "cyan",
        "accent": "bright_cyan",
        "header": "bold cyan",
        "dim": "dim",
        
        # Progress/budget colors
        "progress_bar": "cyan",
        "progress_complete": "green",
        "budget_healthy": "green",
        "budget_caution": "yellow",
        "budget_critical": "red",
    },
    
    "dark": {
        # Status colors (brighter for dark backgrounds)
        "success": "bright_green",
        "error": "bright_red",
        "warning": "bright_yellow",
        "info": "bright_cyan",
        
        # UI elements (high contrast)
        "primary": "bright_cyan",
        "border": "bright_cyan",
        "accent": "bright_magenta",
        "header": "bold bright_cyan",
        "dim": "bright_black",
        
        # Progress/budget colors
        "progress_bar": "bright_cyan",
        "progress_complete": "bright_green",
        "budget_healthy": "bright_green",
        "budget_caution": "bright_yellow",
        "budget_critical": "bright_red",
    },
    
    "light": {
        # Status colors (darker for light backgrounds)
        "success": "dark_green",
        "error": "dark_red",
        "warning": "dark_orange",
        "info": "blue",
        
        # UI elements (medium contrast)
        "primary": "blue",
        "border": "blue",
        "accent": "magenta",
        "header": "bold blue",
        "dim": "grey50",
        
        # Progress/budget colors
        "progress_bar": "blue",
        "progress_complete": "dark_green",
        "budget_healthy": "dark_green",
        "budget_caution": "dark_orange",
        "budget_critical": "dark_red",
    },
    
    "colorblind": {
        # Status colors (accessible for color blindness)
        # Uses blue/magenta/yellow/cyan instead of red/green conflicts
        "success": "blue",
        "error": "magenta",
        "warning": "yellow",
        "info": "cyan",
        
        # UI elements (high contrast, colorblind-safe)
        "primary": "cyan",
        "border": "cyan",
        "accent": "white",
        "header": "bold cyan",
        "dim": "dim",
        
        # Progress/budget colors (colorblind-accessible)
        "progress_bar": "cyan",
        "progress_complete": "blue",
        "budget_healthy": "blue",
        "budget_caution": "yellow",
        "budget_critical": "magenta",
    },
    
    "high-contrast": {
        # Status colors (maximum visibility, bold)
        "success": "bold bright_green",
        "error": "bold bright_red",
        "warning": "bold bright_yellow",
        "info": "bold bright_cyan",
        
        # UI elements (extra bold for visibility)
        "primary": "bold bright_cyan",
        "border": "bold white",
        "accent": "bold bright_magenta",
        "header": "bold bright_white",
        "dim": "bright_black",
        
        # Progress/budget colors (high contrast)
        "progress_bar": "bold bright_cyan",
        "progress_complete": "bold bright_green",
        "budget_healthy": "bold bright_green",
        "budget_caution": "bold bright_yellow",
        "budget_critical": "bold bright_red",
    },
}


def get_available_themes() -> list[str]:
    """
    Get list of available theme names.
    
    Returns:
        List of theme names
    
    Example:
        >>> themes = get_available_themes()
        >>> "default" in themes
        True
    """
    return list(THEMES.keys())


def validate_theme_name(theme: str) -> bool:
    """
    Check if theme name is valid.
    
    Args:
        theme: Theme name to validate
    
    Returns:
        True if theme exists or is "custom", False otherwise
    
    Example:
        >>> validate_theme_name("dark")
        True
        >>> validate_theme_name("invalid")
        False
    """
    return theme in THEMES or theme == "custom"


def load_theme(theme_name: str, custom_colors: Optional[Dict[str, str]] = None) -> bool:
    """
    Load a theme and set it as current.
    
    Args:
        theme_name: Name of theme to load ("default", "dark", "light", "custom")
        custom_colors: Custom color overrides (used when theme_name="custom")
    
    Returns:
        True if theme loaded successfully, False if invalid
    
    Example:
        >>> load_theme("dark")
        True
        >>> get_theme_color("success")
        'bright_green'
    """
    global _current_theme, _theme_colors
    
    # Handle custom theme
    if theme_name == "custom":
        if not custom_colors:
            # Fallback to default if no custom colors provided
            theme_name = "default"
        else:
            # Start with default theme as base
            _theme_colors = THEMES["default"].copy()
            # Override with custom colors
            _theme_colors.update(custom_colors)
            _current_theme = "custom"
            return True
    
    # Handle built-in themes
    if theme_name not in THEMES:
        # Invalid theme, fallback to default
        theme_name = "default"
    
    _theme_colors = THEMES[theme_name].copy()
    _current_theme = theme_name
    return True


def get_theme_color(key: str, fallback: str = "white") -> str:
    """
    Get color for a theme key.
    
    Args:
        key: Theme color key (e.g., "success", "error", "primary")
        fallback: Color to return if key not found (default: "white")
    
    Returns:
        Color string for Rich styling
    
    Example:
        >>> load_theme("default")
        >>> get_theme_color("success")
        'green'
        >>> get_theme_color("unknown", "cyan")
        'cyan'
    """
    global _theme_colors
    
    # Initialize with default theme if not loaded
    if not _theme_colors:
        load_theme("default")
    
    return _theme_colors.get(key, fallback)


def get_current_theme() -> str:
    """
    Get name of currently loaded theme.
    
    Returns:
        Current theme name
    
    Example:
        >>> load_theme("dark")
        >>> get_current_theme()
        'dark'
    """
    global _current_theme
    return _current_theme or "default"


def resolve_theme_from_env() -> str:
    """
    Resolve theme name from environment variables.
    
    Priority:
    1. AKIOS_THEME environment variable
    2. Return None if not set (caller will use config/default)
    
    Returns:
        Theme name from environment, or None
    
    Example:
        >>> os.environ["AKIOS_THEME"] = "dark"
        >>> resolve_theme_from_env()
        'dark'
    """
    return os.environ.get("AKIOS_THEME")


def apply_theme_inheritance(custom_colors: Dict[str, str]) -> Dict[str, str]:
    """
    Apply theme inheritance: custom colors override default ones.
    
    Args:
        custom_colors: Custom color overrides
    
    Returns:
        Full theme dict with defaults + custom overrides
    
    Example:
        >>> custom = {"success": "bright_green"}
        >>> theme = apply_theme_inheritance(custom)
        >>> theme["success"]
        'bright_green'
        >>> "error" in theme  # Inherited from default
        True
    """
    # Start with default theme
    full_theme = THEMES["default"].copy()
    # Override with custom colors
    full_theme.update(custom_colors)
    return full_theme


def validate_color_name(color: str) -> bool:
    """
    Validate that a color name is valid for Rich.
    
    Args:
        color: Color name to validate
    
    Returns:
        True if valid Rich color, False otherwise
    
    Example:
        >>> validate_color_name("green")
        True
        >>> validate_color_name("bright_cyan")
        True
    """
    # Rich supports standard colors + bright_ + dark_ variants
    valid_base_colors = [
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
        "dark_red", "dark_green", "dark_orange", "dark_blue", "dark_magenta",
        "dim", "bold", "grey50", "grey70", "gold1", "orange1",
    ]
    
    # Check if color is a valid base color
    if color in valid_base_colors:
        return True
    
    # Check if it's a style string (e.g., "bold cyan")
    parts = color.split()
    if all(part in valid_base_colors or part == "bold" for part in parts):
        return True
    
    return False


def get_theme_preview(theme_name: str) -> str:
    """
    Get preview string showing theme colors.
    
    Args:
        theme_name: Theme to preview
    
    Returns:
        Formatted preview string
    
    Example:
        >>> preview = get_theme_preview("default")
        >>> "success" in preview
        True
    """
    if theme_name not in THEMES:
        return f"Theme '{theme_name}' not found"
    
    theme = THEMES[theme_name]
    lines = [f"Theme: {theme_name}", ""]
    
    for key, color in sorted(theme.items()):
        lines.append(f"  {key:20} = {color}")
    
    return "\n".join(lines)
