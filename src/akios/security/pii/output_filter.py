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
PII Output Filter for LLM Responses

Applies PII redaction to LLM-generated content to prevent accidental data leakage.
Ensures compliance with data protection requirements for AI-generated outputs.

v1.0.9: Consolidated to use canonical PIIDetector/PIIRedactor instead of
maintaining independent regex patterns. Eliminates divergent placeholders.
"""

from typing import Dict, Any, Optional, List
from .redactor import PIIRedactor, create_pii_redactor


class PIIOutputFilter:
    """
    Specialized PII filter for LLM-generated content.

    v1.0.9: Now delegates ALL detection and redaction to the canonical
    PIIRedactor (which uses RegexPIIDetector internally). This eliminates
    the divergent patterns and placeholder formats that existed before.
    """

    def __init__(self, redactor: Optional[PIIRedactor] = None):
        """
        Initialize the output filter.

        Args:
            redactor: Optional PIIRedactor instance (creates default if None)
        """
        self.redactor = redactor or create_pii_redactor()

    def filter_output(self, text: str, context: Optional[Dict[str, Any]] = None,
                     aggressive: bool = False) -> Dict[str, Any]:
        """
        Filter PII from LLM output text.

        Args:
            text: Raw LLM-generated text
            context: Optional context about the generation (workflow, agent, etc.)
            aggressive: Whether to apply more aggressive redaction rules

        Returns:
            Dict containing filtered text and metadata
        """
        if not text or not isinstance(text, str):
            return {
                'filtered_text': text,
                'redactions_applied': 0,
                'patterns_found': []
            }

        # Use canonical detector to find PII
        detected_pii = self.redactor.detector.detect_pii(text, force_detection=True)

        if not detected_pii:
            return {
                'filtered_text': text,
                'redactions_applied': 0,
                'patterns_found': [],
                'filter_applied': True,
                'aggressive_mode': aggressive
            }

        # Use canonical redactor for consistent placeholder format
        filtered_text = self.redactor.redact_text(text, force_redaction=True)

        # Count redactions
        redactions_applied = sum(len(v) for v in detected_pii.values())
        patterns_found = list(detected_pii.keys())

        return {
            'filtered_text': filtered_text,
            'redactions_applied': redactions_applied,
            'patterns_found': patterns_found,
            'filter_applied': True,
            'aggressive_mode': aggressive
        }

    def get_filter_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the filter configuration.

        Returns:
            Dict with filter configuration and capabilities
        """
        detector_info = self.redactor.detector.get_detector_info()
        return {
            'backend': detector_info.get('backend', 'regex'),
            'patterns_loaded': detector_info.get('patterns_loaded', 0),
            'supported_patterns': list(detector_info.get('rule_summary', {}).get('categories', {}).keys()),
        }


def create_pii_output_filter() -> PIIOutputFilter:
    """
    Create a PII output filter instance.

    Returns:
        Configured PIIOutputFilter instance
    """
    return PIIOutputFilter()


def filter_llm_output(text: str, context: Optional[Dict[str, Any]] = None,
                     aggressive: bool = False) -> Dict[str, Any]:
    """
    Convenience function to filter PII from LLM output.

    Args:
        text: LLM-generated text to filter
        context: Optional context about the generation
        aggressive: Whether to use aggressive filtering

    Returns:
        Dict with filtered text and metadata
    """
    filter_instance = create_pii_output_filter()
    return filter_instance.filter_output(text, context, aggressive)
