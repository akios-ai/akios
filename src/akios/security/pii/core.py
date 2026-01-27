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

Provides PII detection and redaction functionality for V1.0 templates.
PII redaction is mandatory and cannot be disabled for compliance.
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PIIDetector:
    """PII detector for V1.0 templates - detects emails, phones, SSNs"""

    def detect_pii(self, text) -> Dict[str, List[str]]:
        """
        Detect PII in text using regex patterns.

        Args:
            text: Text to scan for PII

        Returns:
            Dictionary of detected PII types and values
        """
        # Ensure text is a string
        if not isinstance(text, str):
            # Debug: log unexpected types
            import os
            if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
                logger.debug(f"detect_pii received {type(text)} instead of str")
            text = str(text)

        detected = {}

        # Email detection
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text, re.IGNORECASE):
            detected['email'] = ['detected']

        # Phone detection (US format)
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b'
        if re.search(phone_pattern, text):
            detected['phone'] = ['detected']

        # SSN detection
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, text):
            detected['ssn'] = ['detected']

        return detected


class PIIRedactor:
    """PII redactor for V1.0 templates - redacts detected PII"""

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

        # Apply redaction
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
    # Ensure text is a string
    if not isinstance(text, str):
        text = str(text)

    redactor = PIIRedactor()
    return redactor.redact_text(text, strategy)
