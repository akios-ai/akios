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
AKIOS V1.0 - Security-First AI Agent Runtime

PII components are available for templates. Security validation occurs during workflow execution.
"""

# Import CLI
from .cli.main import main
from ._version import __version__

# Import PII functionality from dedicated module
from .security.pii import PIIDetector, PIIRedactor, apply_pii_redaction

# Mark package loading as complete - security validation now active for workflow execution
from .security.validation import _end_package_loading
_end_package_loading()

# Package-level security validation
# PII functionality works without blocking during package imports
# Real security validation occurs during workflow execution
def validate_all_security() -> bool:
    """
    Validate basic package security state.

    For V1.0 scope compliance, PII functionality must work
    without blocking during package imports. Real security
    validation occurs during workflow execution.

    Returns:
        True if security components are available and functional
    """
    # Basic validation - PII components are available
    try:
        detector = PIIDetector()
        redactor = PIIRedactor()
        # Test basic functionality
        test_text = "Contact john@example.com for details"
        detected = detector.detect_pii(test_text)
        redacted = redactor.redact_text(test_text)
        return True
    except (ImportError, AttributeError, RuntimeError) as e:
        # Log the specific error for debugging but don't fail import
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Security validation failed: {e}")
        return False

# Legacy functions for backward compatibility
get_pii_detector = PIIDetector
get_pii_redactor = PIIRedactor

__all__ = ["__version__", "main", "validate_all_security", "get_pii_detector", "get_pii_redactor", "apply_pii_redaction"]
