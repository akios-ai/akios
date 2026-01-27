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
Mode switching utilities for AKIOS v1.0.0

Provides automatic configuration switching between mock and real API modes.
Handles interactive API key setup and validation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

from .settings import Settings
from .loader import get_settings
from .validation import validate_config


def switch_to_real_api_mode() -> None:
    """
    Switch to real API mode by modifying environment and configuration.

    This function:
    1. Sets AKIOS_MOCK_LLM=0 (disable mock mode)
    2. Sets network_access_allowed=true in config
    3. Prompts for missing API keys interactively
    4. Validates the configuration

    Raises:
        ValueError: If configuration cannot be switched or validated
    """
    # Modify environment variables
    os.environ['AKIOS_MOCK_LLM'] = '0'

    # Modify configuration file if it exists
    config_path = Path('config.yaml')
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

            # Set network access to enabled
            config['network_access_allowed'] = True

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            raise ValueError(f"Failed to update config.yaml: {e}")

    # Check for required API keys and prompt if missing
    _ensure_api_keys_available()

    # Validate the new configuration
    try:
        settings = get_settings()
        validate_config(settings)
    except Exception as e:
        raise ValueError(f"Real API mode configuration validation failed: {e}")


def _ensure_api_keys_available() -> None:
    """
    Ensure required API keys are available, prompting user if needed.

    Checks for API keys in this priority order:
    1. Environment variables (highest priority)
    2. .env file
    3. Interactive prompt (fallback)

    Raises:
        ValueError: If required API keys cannot be obtained
    """
    # Define supported providers and their key requirements
    providers = {
        'openai': ['OPENAI_API_KEY'],
        'anthropic': ['ANTHROPIC_API_KEY'],
        'grok': ['GROK_API_KEY'],
        'mistral': ['MISTRAL_API_KEY'],
        'gemini': ['GEMINI_API_KEY']
    }

    # Get current LLM provider setting
    provider = os.environ.get('AKIOS_LLM_PROVIDER', 'grok')  # Default to grok

    if provider not in providers:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {', '.join(providers.keys())}")

    required_keys = providers[provider]

    # Check if all required keys are available
    missing_keys = []
    for key in required_keys:
        if not os.environ.get(key):
            missing_keys.append(key)

    if missing_keys:
        # Try to load from .env file first
        env_file = Path('.env')
        if env_file.exists():
            _load_keys_from_env_file(env_file, missing_keys)

            # Check again after loading from file
            still_missing = []
            for key in missing_keys:
                if not os.environ.get(key):
                    still_missing.append(key)
            missing_keys = still_missing

        # If still missing, prompt interactively
        if missing_keys:
            _prompt_for_api_keys(missing_keys, provider)


def _load_keys_from_env_file(env_file: Path, keys_to_load: list) -> None:
    """
    Load specific API keys from .env file into environment.

    Args:
        env_file: Path to .env file
        keys_to_load: List of environment variable names to load
    """
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key in keys_to_load and value:
                        os.environ[key] = value
                        if key in keys_to_load:
                            keys_to_load.remove(key)

    except Exception:
        # Silently continue if .env file cannot be read
        pass


def _prompt_for_api_keys(missing_keys: list, provider: str) -> None:
    """
    Interactively prompt user for missing API keys.

    Works in both native terminal and Docker container environments.
    Handles TTY availability and provides graceful fallbacks.

    Args:
        missing_keys: List of environment variable names needed
        provider: LLM provider name for context

    Raises:
        ValueError: If user cancels or provides invalid input
    """
    print(f"\n🔑 API Key Setup for {provider.title()}", file=sys.stderr)
    print("The following API keys are required but not found:", file=sys.stderr)
    print(file=sys.stderr)

    provider_docs = {
        'openai': 'https://platform.openai.com/api-keys',
        'anthropic': 'https://console.anthropic.com/',
        'grok': 'https://console.x.ai/',
        'mistral': 'https://console.mistral.ai/',
        'gemini': 'https://makersuite.google.com/app/apikey'
    }

    doc_url = provider_docs.get(provider, 'provider documentation')
    print(f"Get your API key from: {doc_url}", file=sys.stderr)
    print(file=sys.stderr)

    # Check if we have TTY access (important for Docker containers)
    try:
        has_tty = sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        has_tty = False

    if not has_tty:
        print("❌ Interactive input not available (no TTY access)", file=sys.stderr)
        print("Please set API keys manually using environment variables or .env file", file=sys.stderr)
        print(f"Required keys: {', '.join(missing_keys)}", file=sys.stderr)
        raise ValueError("Cannot prompt for API keys: no interactive terminal available")

    for key in missing_keys:
        while True:
            try:
                # Use stderr for prompts to avoid interfering with stdout
                prompt = f"Enter {key}: "
                value = input(prompt).strip()

                if not value:
                    print("API key cannot be empty. Please try again.", file=sys.stderr)
                    continue

                # Basic validation
                if len(value) < 10:
                    print("API key seems too short. Please verify and try again.", file=sys.stderr)
                    continue

                if not _validate_api_key_format(key, value):
                    print("API key format appears invalid. Please check and try again.", file=sys.stderr)
                    continue

                os.environ[key] = value

                # Optionally save to .env file
                _offer_to_save_to_env(key, value)
                break

            except (EOFError, KeyboardInterrupt):
                print("\n❌ API key setup cancelled.", file=sys.stderr)
                raise ValueError("API key setup was cancelled by user")


def _validate_api_key_format(key: str, value: str) -> bool:
    """
    Perform basic format validation for API keys.

    Args:
        key: Environment variable name
        value: API key value

    Returns:
        bool: True if format appears valid
    """
    # Basic checks - these are not foolproof but catch obvious errors
    if not value.replace('-', '').replace('_', '').replace('.', '').isalnum():
        return False

    # Provider-specific checks
    if key == 'OPENAI_API_KEY' and not value.startswith('sk-'):
        return False
    elif key == 'ANTHROPIC_API_KEY' and not value.startswith('sk-ant-'):
        return False
    # Grok keys can have various formats

    return True


def _offer_to_save_to_env(key: str, value: str) -> None:
    """
    Offer to save the API key to .env file for persistence.

    Args:
        key: Environment variable name
        value: API key value
    """
    try:
        response = input("Save this API key to .env file for future use? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            env_file = Path('.env')
            # Check if .env exists and has the key
            existing_content = ""
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

            # Add or update the key
            lines = existing_content.split('\n') if existing_content else []
            key_found = False

            for i, line in enumerate(lines):
                if line.strip().startswith(f'{key}='):
                    lines[i] = f'{key}={value}'
                    key_found = True
                    break

            if not key_found:
                if lines and not lines[-1].strip():  # Remove empty last line
                    lines.pop()
                lines.append(f'{key}={value}')
                lines.append('')  # Add trailing newline

            with open(env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print(f"✅ API key saved to .env file", file=sys.stderr)

    except Exception as e:
        print(f"⚠️ Could not save to .env file: {e}", file=sys.stderr)
        print("Your API key is set for this session only.", file=sys.stderr)


def get_current_mode() -> Dict[str, any]:
    """
    Get information about the current operating mode.

    Returns:
        dict: Mode information including mock status, provider, etc.
    """
    try:
        settings = get_settings()
        return {
            'mock_mode': os.environ.get('AKIOS_MOCK_LLM', '1') == '1',
            'llm_provider': os.environ.get('AKIOS_LLM_PROVIDER', 'grok'),
            'network_access': settings.network_access_allowed,
            'has_api_keys': _check_api_keys_available()
        }
    except Exception:
        return {
            'mock_mode': True,
            'llm_provider': 'unknown',
            'network_access': False,
            'has_api_keys': False
        }


def _check_api_keys_available() -> bool:
    """
    Check if the required API keys for current provider are available.

    Returns:
        bool: True if all required API keys are present
    """
    provider = os.environ.get('AKIOS_LLM_PROVIDER', 'grok')
    providers = {
        'openai': ['OPENAI_API_KEY'],
        'anthropic': ['ANTHROPIC_API_KEY'],
        'grok': ['GROK_API_KEY']
    }

    required_keys = providers.get(provider, [])
    return all(os.environ.get(key) for key in required_keys)
