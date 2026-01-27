# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Configuration loader for AKIOS v1.0.0

Loads settings from environment variables with optional YAML/JSON file override.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from .settings import Settings
from .defaults import DEFAULT_SETTINGS
from .validation import validate_config, validate_env_file

# Cache for .env file parsing to avoid reading twice
_env_cache = {}

# ANSI color codes for better error messages
class Colors:
    RED = '\033[91m'
    RESET = '\033[0m'

def colored_error(message: str) -> str:
    """Add red color to error messages if terminal supports it."""
    try:
        if sys.stdout.isatty():
            return f"{Colors.RED}{message}{Colors.RESET}"
        else:
            return message
    except:
        return message


def _convert_pydantic_errors_v1(validation_error) -> str:
    """Convert Pydantic v1 ValidationError to user-friendly messages."""
    friendly_lines = []

    for error in validation_error.errors():
        field_path = '.'.join(str(loc) for loc in error['loc'])
        error_type = error['type']
        error_msg = error['msg']

        # Convert common error types to user-friendly messages
        if error_type == 'value_error.const':
            if field_path == 'environment':
                friendly_lines.append("❌ environment must be 'development', 'testing', or 'production'")
            elif field_path == 'log_level':
                friendly_lines.append("❌ log_level must be 'DEBUG', 'INFO', 'WARNING', or 'ERROR'")
            elif field_path == 'redaction_strategy':
                friendly_lines.append("❌ redaction_strategy must be 'mask', 'hash', or 'remove'")
        elif 'greater_than' in error_type:
            friendly_lines.append(f"❌ {field_path} must be greater than {error.get('ctx', {}).get('gt', 0)}")
        elif 'pattern' in error_type or 'regex' in error_type.lower():
            friendly_lines.append(f"❌ {field_path} has invalid format (check allowed characters)")
        else:
            friendly_lines.append(f"❌ {field_path}: {error_msg}")

    return '\n'.join(friendly_lines)

def _convert_pydantic_errors_v2(validation_error) -> str:
    """Convert Pydantic v2 ValidationError to user-friendly messages."""
    friendly_lines = []

    for error in validation_error.errors():
        field_path_tuple = error['loc']
        field_path = field_path_tuple[0] if field_path_tuple else 'unknown'
        error_type = error['type']
        error_msg = error['msg']
        error_ctx = error.get('ctx', {})

        # Convert common error types to user-friendly messages
        if error_type == 'greater_than':
            gt_value = error_ctx.get('gt', 0)
            friendly_lines.append(f"❌ {field_path} must be greater than {gt_value}")
        elif error_type == 'string_pattern_mismatch':
            if field_path == 'environment':
                friendly_lines.append("❌ environment must be 'development', 'testing', or 'production'")
            elif field_path == 'log_level':
                friendly_lines.append("❌ log_level must be 'DEBUG', 'INFO', 'WARNING', or 'ERROR'")
            elif field_path == 'redaction_strategy':
                friendly_lines.append("❌ redaction_strategy must be 'mask', 'hash', or 'remove'")
            else:
                friendly_lines.append(f"❌ {field_path} has invalid format (check allowed characters)")
        elif 'literal_error' in error_type:
            if field_path == 'environment':
                friendly_lines.append("❌ environment must be 'development', 'testing', or 'production'")
            elif field_path == 'log_level':
                friendly_lines.append("❌ log_level must be 'DEBUG', 'INFO', 'WARNING', or 'ERROR'")
            elif field_path == 'redaction_strategy':
                friendly_lines.append("❌ redaction_strategy must be 'mask', 'hash', or 'remove'")
            else:
                friendly_lines.append(f"❌ {field_path} must be one of the allowed values")
        else:
            friendly_lines.append(f"❌ {field_path}: {error_msg}")

    return '\n'.join(friendly_lines) if friendly_lines else f"{colored_error('Configuration error:')} Invalid settings detected."

def _convert_pydantic_errors(error_str: str) -> str:
    """
    Convert technical Pydantic ValidationError messages to user-friendly explanations.

    Args:
        error_str: Raw Pydantic error string

    Returns:
        User-friendly error messages with suggestions
    """
    friendly_lines = []

    # Parse the error string for common patterns
    if 'greater_than' in error_str and 'cpu_limit' in error_str:
        friendly_lines.append("❌ cpu_limit must be greater than 0")
    if 'pattern' in error_str and 'environment' in error_str:
        friendly_lines.append("❌ environment must be 'development', 'testing', or 'production'")
    if 'greater_than' in error_str and 'memory_limit_mb' in error_str:
        friendly_lines.append("❌ memory_limit_mb must be greater than 0")
    if 'greater_than' in error_str and 'max_tokens_per_call' in error_str:
        friendly_lines.append("❌ max_tokens_per_call must be greater than 0")
    if 'greater_than' in error_str and 'budget_limit_per_run' in error_str:
        friendly_lines.append("❌ budget_limit_per_run must be greater than 0")
    if 'pattern' in error_str and 'log_level' in error_str:
        friendly_lines.append("❌ log_level must be 'DEBUG', 'INFO', 'WARNING', or 'ERROR'")
    if 'pattern' in error_str and 'redaction_strategy' in error_str:
        friendly_lines.append("❌ redaction_strategy must be 'mask', 'hash', or 'remove'")

    # Handle enumeration/literal errors
    if 'enumeration member' in error_str or 'literal_error' in error_str:
        if 'environment' in error_str:
            friendly_lines.append("❌ environment must be 'development', 'testing', or 'production'")
        elif 'log_level' in error_str:
            friendly_lines.append("❌ log_level must be 'DEBUG', 'INFO', 'WARNING', or 'ERROR'")
        elif 'redaction_strategy' in error_str:
            friendly_lines.append("❌ redaction_strategy must be 'mask', 'hash', or 'remove'")

    # Handle type errors
    if 'integer' in error_str:
        if 'cpu_limit' in error_str:
            friendly_lines.append("❌ cpu_limit must be a number (e.g., 0.8 for 80% CPU)")
        elif 'memory_limit_mb' in error_str:
            friendly_lines.append("❌ memory_limit_mb must be a whole number (e.g., 256)")
        elif 'max_tokens_per_call' in error_str:
            friendly_lines.append("❌ max_tokens_per_call must be a whole number (e.g., 1000)")
        elif 'max_open_files' in error_str:
            friendly_lines.append("❌ max_open_files must be a whole number (e.g., 100)")
        elif 'max_file_size_mb' in error_str:
            friendly_lines.append("❌ max_file_size_mb must be a whole number (e.g., 10)")

    if 'float' in error_str:
        if 'cpu_limit' in error_str:
            friendly_lines.append("❌ cpu_limit must be a decimal number (e.g., 0.8 for 80% CPU)")
        elif 'budget_limit_per_run' in error_str:
            friendly_lines.append("❌ budget_limit_per_run must be a decimal number (e.g., 1.0)")

    if 'boolean' in error_str:
        if 'sandbox_enabled' in error_str:
            friendly_lines.append("❌ sandbox_enabled must be true or false")
        elif 'pii_redaction_enabled' in error_str:
            friendly_lines.append("❌ pii_redaction_enabled must be true or false")
        elif 'audit_enabled' in error_str:
            friendly_lines.append("❌ audit_enabled must be true or false")
        elif 'cost_kill_enabled' in error_str:
            friendly_lines.append("❌ cost_kill_enabled must be true or false")
        elif 'network_access_allowed' in error_str:
            friendly_lines.append("❌ network_access_allowed must be true or false")

    if 'string' in error_str and 'pattern' in error_str:
        if 'environment' in error_str:
            friendly_lines.append("❌ environment must be 'development', 'testing', or 'production'")
        elif 'log_level' in error_str:
            friendly_lines.append("❌ log_level must be 'DEBUG', 'INFO', 'WARNING', or 'ERROR'")
        elif 'redaction_strategy' in error_str:
            friendly_lines.append("❌ redaction_strategy must be 'mask', 'hash', or 'remove'")

    # If we found specific errors, return them
    if friendly_lines:
        return '\n'.join(friendly_lines)

    # Ultimate fallback
    return f"{colored_error('Configuration error:')} Invalid settings detected. Please check your configuration values."


def get_settings(config_file: Optional[str] = None) -> Settings:
    """
    Load and validate AKIOS settings

    Priority order:
    1. Environment variables (AKIOS_*)
    2. Optional config file (YAML/JSON) if provided
    3. Project config.yaml in current directory (if exists)
    4. Default values

    Args:
        config_file: Optional path to YAML or JSON config file

    Returns:
        Validated Settings instance

    Raises:
        ValueError: If config is invalid
        FileNotFoundError: If specified config file doesn't exist
    """
    # Load config file first if provided
    file_config = {}
    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
    else:
        # Auto-detect project config.yaml in current directory
        auto_config = Path("config.yaml")
        if auto_config.exists():
            config_path = auto_config
        else:
            config_path = None

    # Validate .env file for corruption before loading configuration
    # This provides early feedback on configuration issues and prevents
    # cryptic errors later in the process
    env_file_path = Path(".env")
    if env_file_path.exists():
        try:
            validate_env_file(str(env_file_path))
            # Explicitly load .env file to ensure API keys are available
            from dotenv import load_dotenv
            load_dotenv(env_file_path)
        except ValueError as e:
            raise ValueError(f"Environment configuration error: {e}") from e

    if config_path:
        # Load from YAML/JSON file
        try:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
            elif config_path.suffix.lower() == '.json':
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")

        except Exception as e:
            # Provide specific error messages for common config file issues
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                # Check for specific YAML syntax errors
                if hasattr(e, '__class__') and 'YAMLError' in e.__class__.__name__:
                    raise ValueError(f"Invalid YAML syntax in config.yaml — check indentation and formatting: {e}")
                elif 'yaml' in str(e).lower():
                    raise ValueError(f"Invalid YAML syntax in {config_file}: {e}")
                else:
                    raise ValueError(f"Failed to read YAML config file {config_file}: {e}")
            elif config_path.suffix.lower() == '.json':
                if 'json' in str(e).lower():
                    raise ValueError(f"Invalid JSON syntax in {config_file}: {e}")
                else:
                    raise ValueError(f"Failed to read JSON config file {config_file}: {e}")
            else:
                raise ValueError(f"Failed to load config file {config_file}: {e}")

    # Create Settings instance with file config - this applies file config over defaults
    try:
        settings = Settings(**file_config)
    except Exception as e:
        # Convert technical Pydantic errors to user-friendly messages
        # Handle both Pydantic v1 ValidationError and v2 pydantic_core ValidationError
        if hasattr(e, 'errors') and callable(getattr(e, 'errors', None)):
            # Pydantic v2 ValidationError with errors() method
            error_msg = _convert_pydantic_errors_v2(e)
        else:
            # Generic error or fallback
            error_msg = _convert_pydantic_errors(str(e))
        raise ValueError(f"{colored_error('Invalid configuration:')}\n{error_msg}")

    # Apply environment variable overrides (highest priority)
    # Manually check for AKIOS_* environment variables and apply them
    env_prefix = "AKIOS_"
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            # Convert AKIOS_SANDBOX_ENABLED to sandbox_enabled
            config_key = key[len(env_prefix):].lower()
            # Always set AKIOS_* environment variables (even if not in Settings class)
            # This allows for dynamic attributes like llm_provider, llm_model, etc.
            try:
                # Convert string values to appropriate types
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                    value = int(value)
                elif value.replace('.', '', 1).isdigit() or (value.startswith('-') and value[1:].replace('.', '', 1).isdigit()):
                    value = float(value)

                # Use object.__setattr__ to bypass Pydantic field validation for dynamic attributes
                object.__setattr__(settings, config_key, value)
            except Exception as e:
                raise ValueError(f"Invalid environment variable {key}={value}: {e}")

    # Validate the loaded settings
    try:
        validate_config(settings)
    except ValueError as e:
        # Check if we're in JSON mode (for automation)
        json_mode = os.environ.get('AKIOS_JSON_MODE', '').lower() in ('1', 'true', 'yes')

        if json_mode:
            import json
            error_output = {
                "error": True,
                "message": str(e),
                "type": "configuration_error"
            }
            print(json.dumps(error_output, indent=2))
            sys.exit(1)
        else:
            raise  # Re-raise for normal error handling

    return settings
