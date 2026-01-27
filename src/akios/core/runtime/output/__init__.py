"""
Output module - Workflow output management and organization

Provides human-readable output directory naming and secure output handling
for AKIOS workflows.
"""

from .manager import (
    OutputManager,
    get_output_manager,
    create_output_directory,
    generate_output_summary
)

__all__ = [
    "OutputManager",
    "get_output_manager",
    "create_output_directory",
    "generate_output_summary"
]
