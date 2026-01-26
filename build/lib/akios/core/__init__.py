"""
AKIOS Core Services Package

Provides foundational services for the AKIOS system including error handling,
caching, performance monitoring, and UI utilities.
"""

# Version information
try:
    from ._version import __version__
except ImportError:
    __version__ = "0.1.0"

# Core service exports
from .error.classifier import classify_error, ErrorCategory, ErrorSeverity
from .cache.manager import get_cache_manager, cached_operation
from .performance.monitor import get_performance_monitor, measure_performance
from .ui.colors import (
    get_color_formatter,
    success, error, warning, info, bold, dim, header, highlight
)
from .ui.progress import spinner, with_spinner, show_progress

# First-run setup
from .config.first_run import run_setup_wizard

# Convenience functions for common use cases
def initialize_core_services() -> bool:
    """
    Initialize all core services with default configurations.

    This function ensures all core services are properly initialized
    and ready for use. Call this early in application startup.

    Returns:
        bool: True if all services initialized successfully, False otherwise
    """
    try:
        # Ensure cache manager is initialized
        get_cache_manager()

        # Ensure performance monitor is initialized
        get_performance_monitor()

        # Ensure color formatter is initialized
        get_color_formatter()

        return True
    except Exception as e:
        # Log error but don't crash - services can be initialized lazily
        import sys
        print(f"Warning: Core services initialization failed: {e}", file=sys.stderr)
        return False

__all__ = [
    # Version
    "__version__",

    # Error handling
    "classify_error", "ErrorCategory", "ErrorSeverity",

    # Caching
    "get_cache_manager", "cached_operation",

    # Performance monitoring
    "get_performance_monitor", "measure_performance",

    # UI utilities
    "get_color_formatter", "success", "error", "warning", "info",
    "bold", "dim", "header", "highlight", "spinner", "with_spinner", "show_progress",

    # Setup
    "run_setup_wizard", "initialize_core_services"
]
