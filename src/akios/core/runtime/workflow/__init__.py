"""
Workflow module - Sequential workflow handling for AKIOS V1.0

Parses and validates simple sequential YAML workflows (no conditional/parallel/loop).
"""

from .parser import parse_workflow
from .validator import validate_workflow

__all__ = ["parse_workflow", "validate_workflow"]
