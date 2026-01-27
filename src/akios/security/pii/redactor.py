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
PII redactor for AKIOS v1.0.0

Replace detected personally identifiable information with safe placeholders.
Supports configurable redaction strategies.
"""

import re
from typing import Dict, List, Optional, Any

from ...config import get_settings
from .detector import PIIDetector, create_pii_detector


class PIIRedactionFailure(Exception):
    """Raised when PII redaction fails"""
    pass


class PIIRedactor:
    """
    PII redaction engine with configurable strategies

    Replaces detected sensitive information with safe placeholders
    using configurable redaction strategies.
    """

    def __init__(self):
        # Delay config and detector loading to avoid import-time validation
        self._settings = None
        self._detector = None

        # Placeholder templates for different strategies - ENSURE ALWAYS SET
        self.placeholders = {
            'mask': '[PII_TYPE]',
            'remove': '',
            'hash': '[HASHED_PII_TYPE]'
        }

    @property
    def settings(self):
        """Lazily load settings to avoid import-time validation"""
        if self._settings is None:
            try:
                self._settings = get_settings()
            except Exception:
                # Fallback to basic settings if config unavailable
                self._settings = self._create_fallback_settings()
        return self._settings

    @property
    def detector(self):
        """Lazily load detector to avoid import-time validation"""
        if self._detector is None:
            try:
                self._detector = create_pii_detector()
            except Exception as e:
                # Fallback to basic detector if creation fails
                print(f"Warning: Could not load PII detector: {e}", file=__import__('sys').stderr)
                from .detector import PIIDetector
                try:
                    self._detector = PIIDetector()
                except Exception as fallback_e:
                    print(f"Warning: PII detector fallback failed: {fallback_e}", file=__import__('sys').stderr)
                    # Create minimal dummy detector
                    self._detector = self._create_minimal_detector()
        return self._detector

    def _create_fallback_settings(self):
        """Create basic fallback settings when config is unavailable"""
        class FallbackSettings:
            pii_redaction_enabled = True
            redaction_strategy = "mask"

        return FallbackSettings()

    def _create_minimal_detector(self):
        """Create minimal PII detector when all else fails"""
        class MinimalDetector:
            def detect_pii(self, text, **kwargs):
                return {}  # No PII detected
            def get_detector_info(self):
                return {"enabled": False, "minimal_fallback": True}

        return MinimalDetector()

    def redact_text(self, text: str, strategy: Optional[str] = None,
                   categories: Optional[List[str]] = None) -> str:
        """
        Redact PII from text using specified strategy

        Args:
            text: Input text containing potential PII
            strategy: Redaction strategy ('mask', 'remove', 'hash')
            categories: Optional categories to redact

        Returns:
            Text with PII redacted

        Raises:
            PIIRedactionFailure: If redaction fails
        """
        # Ensure placeholders are always available
        if not hasattr(self, 'placeholders'):
            self.placeholders = {
                'mask': '[PII_TYPE]',
                'remove': '',
                'hash': '[HASHED_PII_TYPE]'
            }

        if not self.settings.pii_redaction_enabled:
            return text

        if strategy is None:
            strategy = self.settings.redaction_strategy

        if strategy not in self.placeholders:
            raise PIIRedactionFailure(f"Unknown redaction strategy: {strategy}")

        try:
            # Detect PII in the text
            detected_pii = self.detector.detect_pii(text, categories)

            if not detected_pii:
                return text  # No PII found

            # Apply redaction
            redacted_text = self._apply_redaction(text, detected_pii, strategy)

            return redacted_text

        except Exception as e:
            raise PIIRedactionFailure(f"PII redaction failed: {e}") from e

    def _apply_redaction(self, text: str, detected_pii: Dict[str, List[str]],
                        strategy: str) -> str:
        """
        Apply redaction to text based on detected PII

        Args:
            text: Original text
            detected_pii: Dict of detected PII
            strategy: Redaction strategy

        Returns:
            Redacted text
        """
        redacted = text
        business_prefixes = (
            "INV-", "INVOICE-", "SKU-", "PO-", "SO-", "ORD-", "ORDER-", "REF-",
            "CASE-", "BUG-", "TASK-", "DOC-", "FILE-", "RUN-", "JOB-", "TCK-",
            "TICKET-", "TKT-"
        )
        prefix_pattern = r'(?<!' + r')(?<!'.join(re.escape(p) for p in business_prefixes) + r')'

        # Process each PII type
        for pii_type, values in detected_pii.items():
            # Ensure placeholders are available
            if not hasattr(self, 'placeholders'):
                self.placeholders = {
                    'mask': '[PII_TYPE]',
                    'remove': '',
                    'hash': '[HASHED_PII_TYPE]'
                }
            placeholder = self.placeholders[strategy].replace('PII_TYPE', pii_type.upper())

            if strategy == 'hash':
                for value in values:
                    hashed_placeholder = self._create_hash_placeholder(pii_type, value)
                    if pii_type == "license_plate":
                        pattern = prefix_pattern + re.escape(value)
                        redacted = re.sub(pattern, hashed_placeholder, redacted)
                    else:
                        redacted = redacted.replace(value, hashed_placeholder)
            else:
                for value in values:
                    if pii_type == "license_plate":
                        pattern = prefix_pattern + re.escape(value)
                        redacted = re.sub(pattern, placeholder, redacted)
                    else:
                        redacted = redacted.replace(value, placeholder)

        return redacted

    def _create_hash_placeholder(self, pii_type: str, value: str) -> str:
        """
        Create a hash-based placeholder for sensitive data

        Args:
            pii_type: Type of PII (email, phone, etc.)
            value: Original PII value

        Returns:
            Hash-based placeholder
        """
        import hashlib

        # Create a hash of the value for consistent replacement
        # Note: This is not cryptographically secure hashing, just for placeholder consistency
        hash_obj = hashlib.sha256(value.encode('utf-8'))
        hash_suffix = hash_obj.hexdigest()[:8].upper()

        return f"[HASHED_{pii_type.upper()}_{hash_suffix}]"

    def redact_structured_data(self, data: Any, strategy: Optional[str] = None) -> Any:
        """
        Redact PII from structured data (dict, list, etc.)

        Args:
            data: Structured data to redact
            strategy: Redaction strategy

        Returns:
            Data with PII redacted
        """
        if isinstance(data, str):
            return self.redact_text(data, strategy)
        elif isinstance(data, dict):
            return {key: self.redact_structured_data(value, strategy) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.redact_structured_data(item, strategy) for item in data]
        elif isinstance(data, tuple):
            return tuple(self.redact_structured_data(item, strategy) for item in data)
        else:
            return data

    def preview_redaction(self, text: str, strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Preview what would be redacted without actually redacting

        Args:
            text: Text to analyze
            strategy: Redaction strategy to preview

        Returns:
            Dict with preview information
        """
        if strategy is None:
            strategy = self.settings.redaction_strategy

        detected_pii = self.detector.detect_pii(text)
        redacted_preview = self.redact_text(text, strategy)

        return {
            'original_text': text,
            'detected_pii': detected_pii,
            'redaction_strategy': strategy,
            'redacted_preview': redacted_preview,
            'characters_changed': len(text) - len(redacted_preview),
            'pii_instances_found': sum(len(values) for values in detected_pii.values())
        }

    def get_redaction_stats(self) -> Dict[str, Any]:
        """
        Get redaction statistics

        Returns:
            Dict with redaction and detection statistics
        """
        # Ensure placeholders are available
        if not hasattr(self, 'placeholders'):
            self.placeholders = {
                'mask': '[PII_TYPE]',
                'remove': '',
                'hash': '[HASHED_PII_TYPE]'
            }

        return {
            'redaction_enabled': self.settings.pii_redaction_enabled,
            'default_strategy': self.settings.redaction_strategy,
            'detector_info': self.detector.get_detector_info(),
            'supported_strategies': list(self.placeholders.keys())
        }


def create_pii_redactor() -> PIIRedactor:
    """
    Create a PII redactor instance

    Returns:
        Configured PIIRedactor instance
    """
    return PIIRedactor()


def apply_pii_redaction(data, strategy: Optional[str] = None):
    """
    Apply PII redaction to text or structured data (convenience function)

    Args:
        data: Input text or structured data to redact
        strategy: Redaction strategy ('mask', 'hash', 'remove')

    Returns:
        Redacted data (same type as input)
    """
    redactor = create_pii_redactor()
    return redactor.redact_structured_data(data, strategy)


def preview_pii_redaction(text: str, strategy: Optional[str] = None) -> Dict[str, Any]:
    """
    Preview PII redaction without applying it (convenience function)

    Args:
        text: Text to preview redaction for
        strategy: Redaction strategy

    Returns:
        Preview information dict
    """
    redactor = create_pii_redactor()
    return redactor.preview_redaction(text, strategy)
