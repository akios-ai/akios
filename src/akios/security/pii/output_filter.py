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
"""

from typing import Dict, Any, Optional, List
from .redactor import PIIRedactor


class PIIOutputFilter:
    """
    Specialized PII filter for LLM-generated content.

    Applies context-aware redaction to AI responses while preserving
    content meaning and utility. Designed specifically for post-processing
    LLM outputs before presentation to users.
    """

    def __init__(self, redactor: Optional[PIIRedactor] = None):
        """
        Initialize the output filter.

        Args:
            redactor: Optional PIIRedactor instance (creates default if None)
        """
        self.redactor = redactor or PIIRedactor()

        # Output-specific redaction rules (more conservative than input filtering)
        self.output_patterns = {
            'email_addresses': True,    # Always redact emails in outputs
            'phone_numbers': True,      # Always redact phones in outputs
            'credit_cards': True,       # Always redact credit cards
            'social_security': True,    # Always redact SSN-like patterns
            'ip_addresses': True,       # Redact IPs that might be sensitive
            'addresses': False,         # Don't redact generic addresses
            'names': False,            # Don't redact names (context-dependent)
            'dates': False,            # Don't redact dates
        }

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

        # Apply output-specific PII detection and redaction
        filtered_text = self._apply_output_redaction(text, aggressive)

        # Calculate redaction statistics
        redactions_applied = self._count_redactions(text, filtered_text)
        patterns_found = self._identify_patterns(text)

        return {
            'filtered_text': filtered_text,
            'redactions_applied': redactions_applied,
            'patterns_found': patterns_found,
            'filter_applied': True,
            'aggressive_mode': aggressive
        }

    def _apply_output_redaction(self, text: str, aggressive: bool) -> str:
        """
        Apply conservative PII redaction suitable for LLM outputs.

        Args:
            text: Input text to redact
            aggressive: Whether to use aggressive redaction

        Returns:
            Redacted text
        """
        redacted = text

        # Apply redaction based on configured patterns
        if self.output_patterns['email_addresses']:
            redacted = self._redact_emails(redacted)

        if self.output_patterns['phone_numbers']:
            redacted = self._redact_phone_numbers(redacted)

        if self.output_patterns['credit_cards']:
            redacted = self._redact_credit_cards(redacted)

        if self.output_patterns['social_security']:
            redacted = self._redact_ssn_patterns(redacted)

        if self.output_patterns['ip_addresses']:
            redacted = self._redact_sensitive_ips(redacted)

        # Aggressive mode: additional patterns
        if aggressive:
            if self.output_patterns['addresses']:
                redacted = self._redact_addresses(redacted)

        return redacted

    def _redact_emails(self, text: str) -> str:
        """Redact email addresses in text."""
        import re
        return re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL_REDACTED]',
            text,
            flags=re.IGNORECASE
        )

    def _redact_phone_numbers(self, text: str) -> str:
        """Redact phone numbers in various formats."""
        import re
        # US phone patterns
        patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
            r'\b\d{3}-\d{4}\b',        # 123-4567
            r'\(\d{3}\)\s*\d{3}-\d{4}', # (123) 456-7890
            r'\+\d{1,3}\s*\d{3}\s*\d{4}\s*\d{4}',  # International
        ]

        redacted = text
        for pattern in patterns:
            redacted = re.sub(pattern, '[PHONE_REDACTED]', redacted)

        return redacted

    def _redact_credit_cards(self, text: str) -> str:
        """Redact credit card numbers."""
        import re
        # Basic credit card pattern (16 digits, possibly with spaces/dashes)
        pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        return re.sub(pattern, '[CREDIT_CARD_REDACTED]', text)

    def _redact_ssn_patterns(self, text: str) -> str:
        """Redact Social Security Number patterns."""
        import re
        pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        return re.sub(pattern, '[SSN_REDACTED]', text)

    def _redact_sensitive_ips(self, text: str) -> str:
        """Redact potentially sensitive IP addresses."""
        import re
        # Only redact private IPs and localhost (public IPs are generally OK)
        private_ip_pattern = r'\b(10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|127\.0\.0\.1)\d{1,3}\.\d{1,3}\b'
        return re.sub(private_ip_pattern, '[PRIVATE_IP_REDACTED]', text)

    def _redact_addresses(self, text: str) -> str:
        """Redact physical addresses (aggressive mode only)."""
        # This would be more complex - for now, just redact obvious patterns
        import re
        # Simple street address pattern
        pattern = r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b'
        return re.sub(pattern, '[ADDRESS_REDACTED]', text, flags=re.IGNORECASE)

    def _count_redactions(self, original: str, redacted: str) -> int:
        """Count how many redactions were applied."""
        if original == redacted:
            return 0

        # Count redaction markers
        markers = ['[EMAIL_REDACTED]', '[PHONE_REDACTED]', '[CREDIT_CARD_REDACTED]',
                  '[SSN_REDACTED]', '[PRIVATE_IP_REDACTED]', '[ADDRESS_REDACTED]']

        count = 0
        for marker in markers:
            count += redacted.count(marker)

        return count

    def _identify_patterns(self, text: str) -> List[str]:
        """Identify what PII patterns were found in the text."""
        patterns = []

        if self._redact_emails(text) != text:
            patterns.append('email_addresses')
        if self._redact_phone_numbers(text) != text:
            patterns.append('phone_numbers')
        if self._redact_credit_cards(text) != text:
            patterns.append('credit_cards')
        if self._redact_ssn_patterns(text) != text:
            patterns.append('social_security_numbers')
        if self._redact_sensitive_ips(text) != text:
            patterns.append('private_ip_addresses')

        return patterns

    def get_filter_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the filter configuration.

        Returns:
            Dict with filter configuration and capabilities
        """
        return {
            'output_patterns_enabled': self.output_patterns,
            'supported_patterns': list(self.output_patterns.keys()),
            'redaction_markers': [
                'EMAIL_REDACTED', 'PHONE_REDACTED', 'CREDIT_CARD_REDACTED',
                'SSN_REDACTED', 'PRIVATE_IP_REDACTED', 'ADDRESS_REDACTED'
            ]
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
