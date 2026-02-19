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
PII Detection and Redaction Core

Thin wrapper around the canonical PII detector for template compatibility.
All patterns are defined in rules.py — no duplicates here.
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PIIDetector:
    """PII detector for templates — delegates to canonical detector."""

    def __init__(self):
        self._detector = None

    @property
    def _canonical(self):
        """Lazy-load the canonical detector to avoid circular imports."""
        if self._detector is None:
            try:
                from .detector import create_pii_detector
                self._detector = create_pii_detector()
            except Exception:
                self._detector = None
        return self._detector

    def detect_pii(self, text) -> Dict[str, List[str]]:
        """
        Detect PII in text.

        Delegates to the canonical PIIDetector from detector.py.
        Falls back to minimal inline detection only if import fails.

        Args:
            text: Text to scan for PII

        Returns:
            Dictionary of detected PII types and values
        """
        if not isinstance(text, str):
            text = str(text)

        canonical = self._canonical
        if canonical is not None:
            try:
                return canonical.detect_pii(text, force_detection=True)
            except Exception:
                pass

        # Last-resort fallback — only used if canonical detector fails entirely
        detected = {}
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text, re.IGNORECASE):
            detected['email'] = ['detected']
        if re.search(r'\b\d{3}-\d{3}-\d{4}\b', text):
            detected['phone'] = ['detected']
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
            detected['ssn'] = ['detected']
        return detected


class PIIRedactor:
    """PII redactor for templates - redacts detected PII"""

    def __init__(self):
        self.detector = PIIDetector()

    def redact_text(self, text: str, strategy: str = 'mask') -> str:
        """
        Redact PII from text.

        Args:
            text: Text to redact
            strategy: Redaction strategy ('mask' or other future strategies)

        Returns:
            Text with PII redacted
        """
        detected = self.detector.detect_pii(text)
        if not detected:
            return text

        # Apply redaction for common types
        redacted = text
        redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', redacted, flags=re.IGNORECASE)
        redacted = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', redacted)
        redacted = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', redacted)

        return redacted


def apply_pii_redaction(text, strategy: str = 'mask') -> str:
    """
    Apply PII redaction to text (convenience function).

    Args:
        text: Text to redact (should be string)
        strategy: Redaction strategy

    Returns:
        Redacted text
    """
    if not isinstance(text, str):
        text = str(text)

    redactor = PIIRedactor()
    return redactor.redact_text(text, strategy)
