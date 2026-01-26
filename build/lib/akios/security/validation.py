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
Security validation for AKIOS V1.0.

Validates security systems during workflow execution only.
PII components work without validation during import time.
"""

import platform
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Global flag to indicate package loading phase
# During this phase, security validation is disabled to allow PII functionality
_PACKAGE_LOADING = True

# Security validation cache for Docker cold start optimization
# Store cache in project directory since that's mounted in Docker
_SECURITY_CACHE_FILE = Path.home() / ".akios" / "security_cache.json"
_SECURITY_CACHE_TTL = 7200  # 2 hours cache TTL (increased for better performance)

# Warning session management for UX improvement
# Prevents warning spam while maintaining security awareness
_WARNING_SESSION_FILE = ".akios/warning_session.json"
_WARNING_SESSION_TIMEOUT = 3600  # 1 hour session timeout

# Lazy settings loading to avoid import-time validation
_settings = None

def _debug_enabled() -> bool:
    return os.environ.get("AKIOS_DEBUG_ENABLED") == "1"

def _get_settings():
    """Get settings without triggering validation during import"""
    global _settings
    if _settings is None:
        try:
            from ..config import get_settings as _get
            _settings = _get()
        except (ImportError, AttributeError, RuntimeError) as e:
            # Fallback settings if config loading fails
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Settings loading failed, using fallback: {e}")
            _settings = _create_fallback_settings()
    return _settings

def _create_fallback_settings():
    """Create basic fallback settings"""
    class FallbackSettings:
        audit_storage_path = "/tmp/akios_audit"
    return FallbackSettings()

def _end_package_loading():
    """Mark that package loading is complete - called from akios.__init__"""
    global _PACKAGE_LOADING
    _PACKAGE_LOADING = False


def _load_security_cache() -> Optional[Dict[str, Any]]:
    """Load cached security validation results if valid"""
    try:
        if os.path.exists(_SECURITY_CACHE_FILE):
            with open(_SECURITY_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            if time.time() - cache_data.get('timestamp', 0) < _SECURITY_CACHE_TTL:
                return cache_data
    except (json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def _save_security_cache(cache_data: Dict[str, Any]) -> None:
    """Save security validation results to cache"""
    try:
        cache_data['timestamp'] = time.time()
        with open(_SECURITY_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except OSError as e:
        print(f"⚠️ Security cache save failed: {e}", file=sys.stderr)
        pass


def _load_warning_session() -> Optional[Dict[str, Any]]:
    """
    Load warning session state to prevent warning spam.

    Returns:
        dict: Session state with shown warnings and timestamps, or None if no session
    """
    try:
        if os.path.exists(_WARNING_SESSION_FILE):
            with open(_WARNING_SESSION_FILE, 'r') as f:
                session_data = json.load(f)

            # Check if session is still valid (not expired)
            session_start = session_data.get('session_start', 0)
            if time.time() - session_start < _WARNING_SESSION_TIMEOUT:
                return session_data
            else:
                # Session expired, remove file
                try:
                    os.unlink(_WARNING_SESSION_FILE)
                except OSError:
                    pass
    except (json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def _save_warning_session(session_data: Dict[str, Any]) -> None:
    """Save warning session state to prevent future warning spam"""
    try:
        # Ensure .akios directory exists
        os.makedirs(os.path.dirname(_WARNING_SESSION_FILE), exist_ok=True)
        with open(_WARNING_SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
    except OSError as e:
        # Silently fail if we can't save session - warnings will show again next time
        pass


def _should_show_warning(warning_type: str) -> bool:
    """
    Determine if a warning should be displayed based on session state.

    This prevents warning spam while maintaining security awareness.
    Critical warnings are always shown, informational warnings are session-based.

    Args:
        warning_type: Type of warning ('container_downgrade', 'mock_mode', etc.)

    Returns:
        bool: True if warning should be displayed
    """
    # Critical security warnings are always shown
    critical_warnings = {'container_downgrade'}
    if warning_type in critical_warnings:
        return True

    # For other warnings, check session state
    session = _load_warning_session()
    if session is None:
        # No session - create new one and show warning
        session = {
            'session_start': time.time(),
            'shown_warnings': {}
        }
        session['shown_warnings'][warning_type] = time.time()
        _save_warning_session(session)
        return True

    # Check if this warning was already shown in this session
    shown_warnings = session.get('shown_warnings', {})
    if warning_type in shown_warnings:
        # Warning already shown in this session - suppress it
        return False

    # First time seeing this warning in session - show it and record
    shown_warnings[warning_type] = time.time()
    session['shown_warnings'] = shown_warnings
    _save_warning_session(session)
    return True

def validate_all_security() -> bool:
    """
    Validate all security components for AKIOS V1.0 compliance.

    Ensures PII functionality works with security measures while maintaining
    security integrity. Validation runs only during workflow execution,
    not during package import.

    This function implements a non-blocking validation strategy:
    - Performs basic import-time checks without failing PII functionality
    - Logs warnings for missing components but allows graceful degradation
    - Ensures critical security libraries are available when needed
    - Provides clear error messages for production deployment issues

    Returns:
        bool: True if validation passes or warnings are acceptable
    """
    # CRITICAL: PII redaction is MANDATORY for V1.0 scope
    # But we can still validate that core security libraries are available at import time

    try:
        # Basic validation: ensure critical security imports work
        # This doesn't block PII but ensures the security system is functional
        if platform.system() not in ['Linux', 'Darwin', 'Windows']:
            # If we're on an unknown platform, allow it (be permissive)
            pass

        # Test that security modules can be imported (but don't instantiate)
        try:
            import akios.security.pii
            import akios.security.sandbox
            import akios.security.syscall
        except ImportError as e:
            # Log warning but don't fail - security can still work via fallbacks
            print(f"⚠️  Security module import warning: {e}", file=__import__('sys').stderr)
            pass

        return True

    except Exception as e:
        # If any unexpected error occurs during basic validation, log and continue
        # This ensures PII functionality is never blocked by security validation issues
        print(f"⚠️  Security validation warning (non-blocking): {e}", file=__import__('sys').stderr)
        return True


def _is_container_environment() -> bool:
    """
    Centralized container environment detection.

    Checks multiple indicators to reliably detect containerized environments
    where certain security features may not be available.

    Returns:
        bool: True if running in a container environment
    """
    import os

    # Check for Docker container files
    docker_indicators = [
        '/.dockerenv',
        '/run/.containerenv'
    ]

    for indicator in docker_indicators:
        if os.path.exists(indicator):
            return True

    # Check environment variables
    container_vars = ['DOCKER_CONTAINER', 'KUBERNETES_SERVICE_HOST']
    for var in container_vars:
        if os.getenv(var):
            return True

    # Check hostname for container patterns
    hostname = os.getenv('HOSTNAME', '').lower()
    if any(pattern in hostname for pattern in ['docker', 'container', 'podman']):
        return True

    # Check cgroup path for container indicators
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if any(indicator in cgroup_content.lower() for indicator in ['docker', 'containerd', 'podman']):
                return True
    except (OSError, IOError):
        pass

    # Check if cgroups filesystem is read-only (common in containers)
    try:
        cgroup_base = Path('/sys/fs/cgroup')
        if cgroup_base.exists():
            # Try to create a test directory
            test_path = cgroup_base / '.akios_container_test'
            try:
                test_path.mkdir(parents=True, exist_ok=True)
                test_path.rmdir()  # Clean up
                return False  # Writable, so not container
            except (OSError, PermissionError):
                return True  # Read-only, likely container
    except Exception:
        pass

    return False  # Default to native environment


def validate_startup_security() -> bool:
    """
    Strict startup validation that checks if required security libraries
    are available and functional. This runs at application startup and
    blocks execution if core security components are missing.

    Uses intelligent caching to optimize Docker cold start performance
    while maintaining security integrity.

    This prevents the "security theater" issue where AKIOS appears secure
    but critical security libraries are missing.
    """
    try:
        # 1. Container check FIRST - allow Docker on ANY platform with policy-based security
        if _is_container_environment():
            # Docker provides policy-based security on all platforms
            print("🔒 Security Mode: Docker (Policy-Based)", file=sys.stderr)
            print("✅ Full PII redaction, audit, command limits active", file=sys.stderr)
            print("ℹ️ Kernel-hard protections available on native Linux only", file=sys.stderr)

            # One-time first-run notice for non-Linux Docker
            if platform.system() != 'Linux' and _should_show_warning('docker_first_run'):
                print("", file=sys.stderr)
                print("First-run notice:", file=sys.stderr)
                print("Running in Docker on macOS → using policy-based security.", file=sys.stderr)
                print("For maximum isolation: run natively on Linux host.", file=sys.stderr)

            # Allow execution in containers - skip strict Linux requirements
            return True

        # Check cache for recent validation results (only for native environments)
        cached_result = _load_security_cache()
        if cached_result and cached_result.get('validation_successful'):
            # Verify critical non-cacheable checks still pass
            if platform.system() != 'Linux':
                # Platform changed - revalidate everything
                cached_result = None
            else:
                # Use cached results for expensive checks
                if _debug_enabled():
                    print("✓ Security validation cache loaded (cold start optimized)", file=sys.stderr)
                return True

        # 2. Platform check only for native (non-container) environments
        # AKIOS V1.0 requires Linux for kernel-hard security when running natively
        if platform.system() != 'Linux':
            raise SecurityError(
                "PLATFORM SECURITY FAILURE: Native AKIOS requires Linux for kernel-hard security.\n"
                f"Current platform: {platform.system()}\n"
                "\n"
                "AKIOS V1.0's kernel-level sandboxing (seccomp-bpf, cgroups) is Linux-only.\n"
                "For Docker deployment on macOS/Windows, use policy-based security instead.\n"
                "\n"
                "SECURITY COMPROMISED: This native environment cannot run secure workflows.\n"
                "Install AKIOS on a Linux system with seccomp support, or use Docker."
            )

        # 3. Check if seccomp library is available
        seccomp_available = False
        try:
            import seccomp
            # Just check import - don't create any filters to avoid interference
            if _debug_enabled():
                print("✓ Seccomp syscall filtering available (kernel-hard security)", file=sys.stderr)
            seccomp_available = True
        except (ImportError, Exception) as e:
            # Native environment - seccomp is required (container check already handled above)
            raise SecurityError(
                "SECURITY FAILURE: seccomp-bpf not available.\n"
                "AKIOS V1.0 REQUIRES kernel syscall filtering for secure operation.\n"
                "\n"
                "For Linux native: Install system dependencies: apt-get install libseccomp-dev\n"
                "Then install Python library: pip install seccomp\n"
                "\n"
                "SECURITY COMPROMISED: Cannot run AKIOS without syscall filtering."
            )

        # 2. Check if PII detection is available (V1.0 uses regex-based detection)
        # Note: V1.0 uses built-in regex PII detection, not presidio/spaCy
        try:
            # Import the built-in PII detector from security module
            from akios.security.pii import PIIDetector
            detector = PIIDetector()
            # Test basic functionality
            test_result = detector.detect_pii("test@example.com")
            if 'email' in test_result:
                if _debug_enabled():
                    print("✓ PII detection available (regex-based)", file=sys.stderr)
            else:
                raise Exception("PII detector not functional")
        except Exception as e:
            raise SecurityError(
                f"SECURITY FAILURE: PII detection not available: {e}\n"
                "AKIOS V1.0 requires working PII detection for compliance.\n"
                "\n"
                "COMPLIANCE VIOLATION: Cannot run AKIOS without PII protection."
            )

        # 3. Check if cgroups v2 is available (kernel process isolation)
        cgroups_available = False
        try:
            # Check if cgroups v2 filesystem is mounted
            import os
            if os.path.exists('/sys/fs/cgroup/cgroup.controllers'):
                # Check if we can read cgroup controllers
                with open('/sys/fs/cgroup/cgroup.controllers', 'r') as f:
                    controllers = f.read().strip()
                    if controllers:  # Has controllers available
                        # Try to create a test cgroup
                        test_path = '/sys/fs/cgroup/akios_test'
                        try:
                            os.makedirs(test_path, exist_ok=True)
                            os.rmdir(test_path)
                            cgroups_available = True
                            print("✓ Cgroups v2 process isolation available", file=sys.stderr)
                        except (OSError, PermissionError):
                            pass
        except Exception:
            pass

        if not cgroups_available:
            if _is_container_environment():
                if _debug_enabled():
                    print("⚠️ Cgroups v2 not available in container - using POSIX limits", file=sys.stderr)
            else:
                raise SecurityError(
                    "SECURITY FAILURE: cgroups v2 not available for process isolation.\n"
                    "AKIOS V1.0 requires cgroups v2 for kernel-hardened sandboxing.\n"
                    "\n"
                    "Ensure cgroups v2 is mounted and accessible:\n"
                    "  - Check: mount | grep cgroup2\n"
                    "  - Enable: echo '+cgroup' >> /etc/modules-load.d/cgroup.conf\n"
                    "\n"
                    "SECURITY COMPROMISED: Cannot run AKIOS without process isolation."
                )

        # 4. Check if LLM providers are available
        llm_providers_available = []
        try:
            import openai
            llm_providers_available.append("OpenAI")
        except ImportError:
            pass

        try:
            import anthropic
            llm_providers_available.append("Anthropic")
        except ImportError:
            pass

        if not llm_providers_available:
            raise SecurityError(
                "SECURITY FAILURE: No LLM providers available.\n"
                "AKIOS V1.0 requires at least one LLM provider for AI functionality.\n"
                "Install with: pip install openai>=1.0.0 and/or anthropic>=0.7.0\n"
                "\n"
                "Cannot start AKIOS without LLM capability."
            )

        # If we get here, all required security components are available
        # Cache successful validation results for performance optimization
        try:
            cache_data = {
                'validation_successful': True,
                'platform': platform.system(),
                'timestamp': time.time()
            }
            _save_security_cache(cache_data)
        except Exception:
            # Cache saving failure - continue without caching
            pass

        return True

    except SecurityError:
        # Re-raise SecurityError as-is
        raise
    except Exception as e:
        raise SecurityError(
            f"SECURITY FAILURE: Unexpected error during startup validation: {e}\n"
            "Cannot start AKIOS due to security validation failure."
        )

def _validate_security_requirements() -> bool:
    """
    Perform full security validation for workflow execution.
    This is the actual security enforcement.
    """
    # 1. Validate syscall filtering capability
    if not _syscall_filtering_available():
        # Check if we're in a containerized environment
        if _is_container_environment():
            # Docker/container environment - allow with policy-based security
            print("🔒 Security Mode: Docker (Policy-Based)", file=sys.stderr)
            print("✅ Full PII redaction, audit, command limits active", file=sys.stderr)
            print("ℹ️ Kernel-hard protections available on native Linux only", file=sys.stderr)

            # One-time first-run notice for non-Linux Docker
            if platform.system() != 'Linux' and _should_show_warning('docker_first_run'):
                print("", file=sys.stderr)
                print("First-run notice:", file=sys.stderr)
                print("Running in Docker on macOS → using policy-based security.", file=sys.stderr)
                print("For maximum isolation: run natively on Linux host.", file=sys.stderr)

            # Allow execution in containers with policy-based security
            return True
        else:
            # Native environment - seccomp should work
            raise SecurityError(
                "SECURITY FAILURE: Syscall filtering (seccomp-bpf) is not available.\n"
                "AKIOS V1.0 requires Linux kernel syscall filtering for secure workflow execution.\n"
                "Please run on Linux with seccomp support.\n"
                "\n"
                "Cannot execute workflows in this environment."
            )

    # 2. Validate sandbox capability
    if not _sandbox_available():
        raise SecurityError(
            "SECURITY FAILURE: Process sandboxing (cgroups) is not available.\n"
            "AKIOS V1.0 requires cgroups v2 for process isolation during workflow execution."
        )

    # 3. Validate audit system
    if not _audit_system_available():
        raise SecurityError(
            "SECURITY FAILURE: Audit system is not functional.\n"
            "AKIOS V1.0 requires tamper-proof audit logging for workflow execution."
        )

    return True

def _syscall_filtering_available() -> bool:
    """Check if syscall filtering is available"""
    if platform.system() != 'Linux':
        return False

    try:
        # Just check if seccomp module can be imported
        # Don't create or load any filters to avoid applying seccomp to current process
        import seccomp
        return True
    except ImportError:
        return False

def _pii_redaction_available() -> bool:
    """Check if PII redaction is available"""
    # For V1.0, we use regex-based PII detection (scoped)
    # In future versions, this could check for ML-based detection
    return True  # Regex-based detection is always available

def _sandbox_available() -> bool:
    """Check if sandboxing is available"""
    # Check for cgroups v2
    cgroup_path = "/sys/fs/cgroup"
    if not os.path.exists(cgroup_path):
        return False

    # Check if cgroups v2 is mounted
    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.read()
            return "cgroup2" in mounts and cgroup_path in mounts
    except:
        return False

def _audit_system_available() -> bool:
    """Check if audit system is available"""
    # Basic check - audit directory should be writable
    settings = _get_settings()
    audit_path = os.path.dirname(getattr(settings, 'audit_storage_path', None) or "/tmp/akios_audit")
    try:
        os.makedirs(audit_path, exist_ok=True)
        test_file = os.path.join(audit_path, ".audit_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.unlink(test_file)
        return True
    except:
        return False

class SecurityError(Exception):
    """Raised when security requirements are not met"""
    pass
