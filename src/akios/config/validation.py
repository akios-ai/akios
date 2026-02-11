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
Configuration and environment validation for AKIOS

Validates settings consistency and runtime environment requirements.
"""

import os
import platform
import sys
import subprocess
import logging
from pathlib import Path

from .settings import Settings

logger = logging.getLogger(__name__)

# LLM Provider-Model Compatibility Mapping (audited from source code)
# Updated with all supported models from provider implementations
PROVIDER_MODELS = {
    'openai': [
        'gpt-4o-mini',
        'gpt-4o',
        'gpt-4-turbo',
        'gpt-4'
    ],
    'anthropic': [
        'claude-3.5-haiku',
        'claude-3.5-sonnet',
        'claude-3-opus',
        'claude-3-haiku-20240307',
        'claude-3-sonnet-20240229',
        'claude-3-opus-20240229'
    ],
    'grok': [
        'grok-3',
        'grok-4.1',
        'grok-4.1-fast'
    ],
    'mistral': [
        'mistral-small',
        'mistral-medium',
        'mistral-large'
    ],
    'gemini': [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-1.0-pro'
    ],
    'mock': [
        'mock-model'
    ]
}

def validate_llm_provider_model(provider: str, model: str) -> None:
    """
    Validate that LLM model is compatible with provider.

    Args:
        provider: LLM provider name ('openai', 'anthropic', etc.)
        model: Model name to validate

    Raises:
        ValueError: If model is not valid for provider
    """
    if provider not in PROVIDER_MODELS:
        available_providers = list(PROVIDER_MODELS.keys())
        raise ValueError(
            f"Unknown LLM provider '{provider}'. "
            f"Available providers: {available_providers}"
        )

    valid_models = PROVIDER_MODELS[provider]
    # Case-insensitive comparison (nice-to-have for user convenience)
    if model.lower() not in [m.lower() for m in valid_models]:
        raise ValueError(
            f"Model '{model}' is not valid for provider '{provider}'.\n"
            f"Valid models for {provider}: {valid_models}\n"
            f"Example: AKIOS_LLM_MODEL={valid_models[0]}"
        )

# ANSI color codes for better error messages
try:
    from ..core.ui.rich_output import get_theme_ansi, ANSI_RESET
except ImportError:
    # Fallback if rich_output cannot be imported
    def get_theme_ansi(name): return ""
    ANSI_RESET = ""

def colored_error(message: str) -> str:
    """Add red color to error messages if terminal supports it."""
    try:
        if sys.stdout.isatty():
            return f"{get_theme_ansi('error')}{message}{ANSI_RESET}"
        else:
            return message
    except Exception:
        return message

def colored_warning(message: str) -> str:
    """Add yellow color to warning messages if terminal supports it."""
    try:
        if sys.stdout.isatty():
            return f"{get_theme_ansi('warning')}{message}{ANSI_RESET}"
        else:
            return message
    except Exception:
        return message


def validate_env_file(env_path: str) -> None:
    """
    Validate .env file for corruption, security issues, and provide fix suggestions.

    Performs comprehensive validation including:
    - Shell injection prevention
    - Duplicate key detection
    - Malformed value detection
    - API key format validation
    - Concatenation detection

    Args:
        env_path: Path to .env file to validate

    Raises:
        ValueError: If .env file contains corruption or security issues
    """
    if not os.path.exists(env_path):
        return  # .env file is optional

    corruption_issues = []
    parsed_vars = {}  # Track for duplicate detection

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError(f"Cannot read .env file {env_path}: {e}")

    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue

        # Check for key=value format
        if '=' not in line:
            corruption_issues.append({
                'line': line_num,
                'key': 'N/A',
                'value': line,
                'corruption_type': 'Invalid format: missing equals sign',
                'suggested_fix': 'Use KEY=value format'
            })
            continue

        # Check for spaces around = sign
        if ' =' in line or '= ' in line:
            corruption_issues.append({
                'line': line_num,
                'key': 'N/A',
                'value': line,
                'corruption_type': 'Spaces around equals sign',
                'suggested_fix': 'Remove spaces around = (use KEY=value format)'
            })

        key, value = line.split('=', 1)
        original_key = key
        original_value = value
        key = key.strip()
        value = value.strip()

        # Check for quoted values
        # Allow quotes for JSON-like values (lists/dicts)
        is_json_like = (value.startswith('"') and value.endswith('"') and 
                       (value.strip('"').startswith('[') or value.strip('"').startswith('{'))) or \
                       (value.startswith("'") and value.endswith("'") and 
                       (value.strip("'").startswith('[') or value.strip("'").startswith('{')))

        if ((value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))) and not is_json_like:
            value = value[1:-1]  # Strip quotes
            corruption_issues.append({
                'line': line_num,
                'key': key,
                'value': original_value,
                'corruption_type': 'Quoted value detected',
                'suggested_fix': f'Remove quotes: {key}={value}'
            })

        # Check for duplicate keys
        if key in parsed_vars:
            first_line = parsed_vars[key]["line"]
            corruption_issues.append({
                'line': line_num,
                'key': key,
                'value': value,
                'corruption_type': f"Duplicate key '{key}' (first seen on line {first_line})",
                'suggested_fix': f"Keep only one '{key}' entry and remove the duplicate line"
            })
        else:
            parsed_vars[key] = {'line': line_num, 'value': value}

        # Check for shell injection characters (expanded list)
        # Removed [, ], {, } to allow JSON structures
        injection_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '*', '?', '~', '!', '@', '#', '%', '^', '+']
        for char in injection_chars:
            if char in value:
                corruption_issues.append({
                    'line': line_num,
                    'key': key,
                    'value': value,
                    'corruption_type': f'Potential shell injection or invalid character: contains \'{char}\'',
                    'suggested_fix': 'Remove shell metacharacters and invalid characters'
                })
                break

        # API key format validation
        if key.endswith('_API_KEY') or key in ['GROK_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
            # Check if we're in mock mode (allow mock-key)
            is_mock_mode = any(
                line.strip().startswith('AKIOS_MOCK_LLM=1') or
                line.strip().startswith('AKIOS_LLM_PROVIDER=mock')
                for line in lines
            )

            # Allow mock-key in mock mode
            if not (value == 'mock-key' and is_mock_mode):
                # Check minimum length
                if len(value) < 10:
                    corruption_issues.append({
                        'line': line_num,
                        'key': key,
                        'value': value,
                        'corruption_type': f'Suspiciously short API key: {len(value)} characters',
                        'suggested_fix': 'Verify API key from provider dashboard'
                    })
            # Check for invalid characters (API keys should be alphanumeric + specific chars)
            invalid_chars = set(value) - set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
            if invalid_chars:
                corruption_issues.append({
                    'line': line_num,
                    'key': key,
                    'value': value,
                    'corruption_type': f'API key contains invalid characters: {sorted(invalid_chars)}',
                    'suggested_fix': 'API keys should contain only letters, numbers, hyphens, and underscores'
                })
            # Provider-specific format checks
            if key == 'OPENAI_API_KEY' and not value.startswith('sk-'):
                corruption_issues.append({
                    'line': line_num,
                    'key': key,
                    'value': value[:10] + '...' if len(value) > 10 else value,
                    'corruption_type': 'OpenAI API key should start with "sk-"',
                    'suggested_fix': 'Verify OpenAI API key format'
                })
            elif key == 'ANTHROPIC_API_KEY' and not value.startswith('sk-ant-'):
                corruption_issues.append({
                    'line': line_num,
                    'key': key,
                    'value': value[:15] + '...' if len(value) > 15 else value,
                    'corruption_type': 'Anthropic API key should start with "sk-ant-"',
                    'suggested_fix': 'Verify Anthropic API key format'
                })

        # Detect common corruption patterns (skip for mock API keys)
        is_api_key = key.endswith('_API_KEY') or key in ['GROK_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        is_mock_mode = any(
            line.strip().startswith('AKIOS_MOCK_LLM=1') or
            line.strip().startswith('AKIOS_LLM_PROVIDER=mock')
            for line in lines
        )

        if not (is_api_key and value == 'mock-key' and is_mock_mode):
            corruption_type = _detect_corruption(key, value)
            if corruption_type:
                corruption_issues.append({
                    'line': line_num,
                    'key': key,
                    'value': value,
                    'corruption_type': corruption_type,
                    'suggested_fix': _suggest_fix(key, value, corruption_type)
                })

    if corruption_issues:
        error_msg = ".env file contains configuration issues:\n\n"
        for issue in corruption_issues:
            error_msg += f"Line {issue['line']}: {issue['corruption_type']}\n"
            error_msg += f"  Key: {issue['key']}\n"
            error_msg += f"  Value: {issue['value']}\n"
            error_msg += f"  Suggested fix: {issue['suggested_fix']}\n\n"

        error_msg += "To fix manually:\n"
        error_msg += f"1. Open {env_path} in a text editor\n"
        error_msg += "2. Apply the suggested fixes above\n"
        error_msg += "3. Save and retry the command\n\n"
        error_msg += "Security note: AKIOS blocks shell injection to protect your system"

        raise ValueError(error_msg)


def _detect_corruption(key: str, value: str) -> str:
    """
    Detect common .env file corruption patterns.

    Args:
        key: Environment variable key
        value: Environment variable value

    Returns:
        Corruption type description, or empty string if no corruption detected
    """
    # Check for concatenated provider names (e.g., "grokopenai" instead of "grok")
    if key == 'AKIOS_LLM_PROVIDER':
        known_providers = {'openai', 'anthropic', 'grok', 'mistral', 'gemini'}
        if value not in known_providers:
            # Check for concatenated providers
            for provider1 in known_providers:
                for provider2 in known_providers:
                    if provider1 != provider2 and provider1 + provider2 == value:
                        return f"Concatenated provider names: '{provider1}' + '{provider2}' = '{value}'"

    # Check for concatenated model names (e.g., "grok-3gpt-4" instead of "grok-3")
    if key == 'AKIOS_LLM_MODEL':
        # Common model patterns
        models = [
            'gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-4',
            'claude-3.5-haiku', 'claude-3.5-sonnet', 'claude-3-opus',
            'grok-3', 'grok-4.1', 'grok-4.1-fast',
            'mistral-small', 'mistral-medium', 'mistral-large',
            'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'
        ]
        if value not in models:
            # Check for concatenated models
            for model1 in models:
                for model2 in models:
                    if model1 != model2 and model1 + model2 == value:
                        return f"Concatenated model names: '{model1}' + '{model2}' = '{value}'"

    # Check for malformed boolean values
    if key in ['AKIOS_MOCK_LLM', 'AKIOS_PII_REDACTION_ENABLED']:
        if value.lower() not in ['true', 'false', '0', '1']:
            return f"Invalid boolean value: '{value}' (expected: true/false or 0/1)"

    # Check for obviously corrupted API keys (too short, wrong format)
    # Skip validation for mock mode
    if key.endswith('_API_KEY') or key == 'GROK_API_KEY':
        # Allow mock keys in mock mode
        is_mock_mode = os.environ.get('AKIOS_MOCK_LLM') == '1' or os.environ.get('AKIOS_LLM_PROVIDER') == 'mock'
        if value == 'mock-key' and is_mock_mode:
            pass  # Allow mock-key in mock mode
        elif len(value) < 10:
            return f"Suspiciously short API key: {len(value)} characters (expected 20+)"
        if not value.replace('-', '').replace('_', '').replace('.', '').isalnum():
            return f"API key contains invalid characters: '{value}'"

    return ""  # No corruption detected


def _suggest_fix(key: str, value: str, corruption_type: str) -> str:
    """
    Suggest a fix for detected corruption.

    Args:
        key: Environment variable key
        value: Corrupted value
        corruption_type: Type of corruption detected

    Returns:
        Human-readable fix suggestion
    """
    if 'Concatenated provider names' in corruption_type:
        if 'grok' in value and 'openai' in value:
            return f"Change '{key}={value}' to '{key}=grok'"
        elif 'openai' in value and 'anthropic' in value:
            return f"Choose the correct provider and set '{key}=openai' or '{key}=anthropic'"

    if 'Concatenated model names' in corruption_type:
        if 'grok-3' in value and 'gpt-4' in value:
            return f"Change '{key}={value}' to '{key}=grok-3'"

    if 'Invalid boolean value' in corruption_type:
        return f"Change '{key}={value}' to '{key}=true' or '{key}=false'"

    if 'Suspiciously short API key' in corruption_type:
        return f"Replace with a valid API key from your provider's dashboard"

    if 'API key contains invalid characters' in corruption_type:
        return f"Check that the API key is copied correctly from your provider's dashboard"

    return "Review and correct the value manually"


def validate_config(settings: Settings) -> None:
    """
    Validate AKIOS configuration settings

    Performs consistency checks and enforces security requirements.
    Provides user-friendly error messages instead of technical Pydantic errors.

    Args:
        settings: Settings instance to validate

    Raises:
        ValueError: If configuration is invalid (with user-friendly messages)
    """
    errors = []

    # Production environment requires strict security
    if settings.environment == "production":
        if not settings.sandbox_enabled:
            errors.append("sandbox_enabled must be true in production environment (security requirement)")
        if settings.network_access_allowed:
            errors.append("network_access_allowed must be false in production environment (security requirement)")
        if not settings.audit_enabled:
            errors.append("audit_enabled must be true in production environment (compliance requirement)")

    # Path validation
    if settings.audit_enabled:
        audit_path = Path(settings.audit_storage_path)
        try:
            audit_path.mkdir(parents=True, exist_ok=True)
            # Test if we can write to the directory (thread-safe)
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(dir=str(audit_path), delete=True) as test_file:
                test_file.write(b"test")
                test_file.flush()
                # File is automatically deleted when context exits
        except (OSError, PermissionError) as e:
            errors.append(f"Cannot write to audit path '{audit_path}': {str(e).lower()}")

    # LLM provider/model validation (from AKIOS_LLM_PROVIDER and AKIOS_LLM_MODEL env vars)
    llm_provider = getattr(settings, 'llm_provider', None)
    llm_model = getattr(settings, 'llm_model', None)

    # Only validate if both provider and model are set (allows partial configuration)
    if llm_provider and llm_model:
        try:
            validate_llm_provider_model(llm_provider, llm_model)
        except ValueError as e:
            errors.append(f"LLM configuration error: {e}")

    # Security consistency checks
    if settings.pii_redaction_enabled and not settings.sandbox_enabled:
        errors.append("PII redaction requires sandbox_enabled to be true (security dependency)")

    if settings.cost_kill_enabled and settings.max_tokens_per_call <= 0:
        errors.append("cost_kill_enabled requires max_tokens_per_call to be a positive number")

    # Fail fast if any errors
    if errors:
        # Separate LLM errors from other errors for better UX
        llm_errors = [e for e in errors if "LLM configuration error" in e]
        other_errors = [e for e in errors if "LLM configuration error" not in e]

        error_msg = colored_error("Configuration validation failed:") + "\n"

        if llm_errors:
            error_msg += "\n🔧 " + colored_error("LLM Configuration Issues:") + "\n"
            error_msg += "\n".join(f"❌ {e.replace('LLM configuration error: ', '')}" for e in llm_errors)

        if other_errors:
            if llm_errors:
                error_msg += "\n\n" + colored_error("Other Configuration Issues:") + "\n"
            error_msg += "\n".join(f"❌ {e}" for e in other_errors)

        raise ValueError(error_msg)


def validate_environment():
    """
    Validate runtime environment against scope requirements.

    Performs the 4 scope-required validations:
    1. Thorough user flows + Linux distro validation
    2. Explicit kernel 5.4+ + cgroups v2 + seccomp-bpf validation
    3. Privileged mode kernel access validation
    4. pip-audit + Python supply chain (documented, not runtime)

    In production mode: Fails hard on missing kernel features.
    In development/testing: Logs warnings but continues.
    """
    # Get current environment setting (without full validation to avoid cycles)
    try:
        # Quick environment check - avoid full settings validation
        env_setting = os.environ.get('AKIOS_ENVIRONMENT', 'development')
        is_production = env_setting == 'production'
    except Exception:
        is_production = False  # Default to development if anything fails

    errors = []
    warnings = []

    # 1. Python version (basic check)
    if sys.version_info < (3, 8):
        errors.append("Python 3.8+ required. Current: " + platform.python_version())

    # 2. Linux kernel 5.4+ + cgroups v2 + seccomp-bpf
    if platform.system() != "Linux":
        errors.append("Linux kernel required. Current: " + platform.system())

    try:
        kernel_version = platform.release()
        major, minor = map(int, kernel_version.split(".")[:2])
        if major < 5 or (major == 5 and minor < 4):
            error_msg = f"Kernel 5.4+ required. Current: {kernel_version}"
            if is_production:
                errors.append(error_msg + " (production requirement)")
            else:
                warnings.append(error_msg)
    except Exception:
        error_msg = "Could not determine kernel version"
        if is_production:
            errors.append(error_msg + " (cannot verify kernel requirements)")
        else:
            warnings.append(error_msg)

    # Simple cgroup v2 check (best effort)
    try:
        with open("/proc/filesystems") as f:
            if "cgroup2" not in f.read():
                error_msg = "cgroups v2 not enabled"
                if is_production:
                    errors.append(error_msg + " (production security requirement)")
                else:
                    warnings.append(error_msg)
    except Exception:
        error_msg = "Could not check cgroups v2"
        if is_production:
            errors.append(error_msg + " (cannot verify security features)")
        else:
            warnings.append(error_msg)

    # seccomp-bpf check (basic)
    try:
        result = subprocess.run(["grep", "CONFIG_SECCOMP_FILTER", "/boot/config-$(uname -r)"],
                              capture_output=True, text=True)
        if "y" not in result.stdout.lower():
            warning_msg = "seccomp-bpf not enabled in kernel - syscall filtering will be limited"
            if is_production:
                errors.append(warning_msg + " (production security requirement)")
            else:
                warnings.append(warning_msg)
        else:
            logger.info("seccomp-bpf enabled in kernel")
    except Exception:
        warning_msg = "Could not check seccomp-bpf kernel config - syscall filtering may be limited"
        if is_production:
            errors.append(warning_msg + " (cannot verify security features)")
        else:
            warnings.append(warning_msg)

    # 3. Privileged mode (basic check)
    if os.getuid() == 0:
        warnings.append("Running as root - recommended to use non-root user for security")

    # 4. pip-audit (recommend in docs, not runtime check - too heavy)
    # Will be documented in README: "Run `pip-audit` regularly for security"

    # Handle errors (fail hard in production)
    if errors:
        error_msg = colored_error("Environment validation failed:") + "\n" + "\n".join(f"❌ {e}" for e in errors)
        if warnings:
            error_msg += "\n\nWarnings:\n" + "\n".join(f"⚠️ {colored_warning(w)}" for w in warnings)
        raise ValueError(error_msg)

    # Handle warnings (development/testing mode)
    if warnings:
        logger.warning("Environment validation warnings (AKIOS optimized for Linux):")
        for w in warnings:
            logger.warning(f"  - {w}")
        logger.warning("Continuing execution - some features may be limited or unavailable")

    logger.info("Environment validation passed")


def validate_linux_distro():
    """Validate Linux distribution compatibility and fail on unsupported distros."""
    # Get current environment setting
    try:
        env_setting = os.environ.get('AKIOS_ENVIRONMENT', 'development')
        is_production = env_setting == 'production'
    except Exception:
        is_production = False

    try:
        # Check /etc/os-release for supported distros
        with open("/etc/os-release", "r") as f:
            content = f.read().lower()

        supported = False
        distro_name = "unknown"

        if "ubuntu" in content:
            distro_name = "Ubuntu"
            # Check version (basic)
            if "20.04" in content or "22.04" in content or "24.04" in content:
                supported = True
            else:
                # Extract version for better error message
                for line in content.split('\n'):
                    if line.startswith('version_id='):
                        version = line.split('=')[1].strip('"')
                        if version:
                            distro_name = f"Ubuntu {version}"
                        break

        elif "centos" in content or "rhel" in content:
            distro_name = "CentOS/RHEL" if "centos" in content else "RHEL"
            supported = True
        elif "fedora" in content:
            distro_name = "Fedora"
            supported = True
        elif "alpine" in content:
            distro_name = "Alpine"
            supported = True  # musl libc support

        if not supported:
            error_msg = f"Unsupported Linux distribution: {distro_name}"
            if is_production:
                error_msg += " (production requires supported distro for security guarantees)"
                raise ValueError(f"Distribution validation failed:\n❌ {error_msg}")
            else:
                logger.warning(f"{error_msg}. Recommended: Ubuntu 20.04+, CentOS/RHEL 8+, Fedora 35+")

        return True
    except ValueError:
        raise  # Re-raise production validation errors
    except Exception:
        error_msg = "Could not determine Linux distribution"
        if is_production:
            raise ValueError(f"Distribution validation failed:\n❌ {error_msg} (cannot verify compatibility)")
        else:
            logger.warning(f"{error_msg} - proceeding with caution")
        return True
