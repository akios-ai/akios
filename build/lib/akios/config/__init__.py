"""
Configuration module - Secure, type-safe settings management

Provides centralized configuration loading and validation for all AKIOS components.
"""

from .settings import Settings
from .loader import get_settings, validate_config
from .validation import validate_env_file
from .modes import switch_to_real_api_mode, get_current_mode

__all__ = ["Settings", "get_settings", "validate_config", "validate_env_file", "switch_to_real_api_mode", "get_current_mode"]
