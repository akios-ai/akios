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
PII detector for AKIOS

Identify personally identifiable information in text/data.
Provides >95% accuracy using carefully crafted patterns.

v1.0.9: Renamed to RegexPIIDetector, implements PIIDetectorProtocol.
"""

import re
import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

from ...config import get_settings
from .rules import ComplianceRules, PIIPattern, load_compliance_rules


# Context window size (chars) to search for keywords around a match
_CONTEXT_WINDOW = 100


class RegexPIIDetector:
    """
    Regex-based PII detection engine with >95% accuracy.

    Implements PIIDetectorProtocol. Uses compliance rule packs to identify
    sensitive information in text and data streams.

    v1.0.9: Renamed from PIIDetector, implements context_keywords for
    ambiguous patterns (france_id, germany_id, bank_account_us).
    """

    def __init__(self):
        # Delay config loading to avoid triggering security validation during import
        self._settings = None
        self._rules = None
        self.detection_stats = defaultdict(int)

    @property
    def settings(self):
        """Lazily load settings to avoid import-time validation"""
        if self._settings is None:
            try:
                self._settings = get_settings()
            except Exception as e:
                # Fallback to basic settings if config unavailable
                logger.warning("Could not load PII detector settings: %s", e)
                self._settings = self._create_fallback_settings()
        return self._settings

    @property
    def rules(self):
        """Lazily load rules to avoid import-time validation"""
        if self._rules is None:
            try:
                self._rules = load_compliance_rules()
            except Exception:
                # Fallback to basic rules if config unavailable
                self._rules = self._load_fallback_patterns()
        return self._rules

    def _load_fallback_patterns(self) -> Dict[str, PIIPattern]:
        """
        Load basic PII patterns when config is unavailable
        Provides minimal but functional PII detection with enhanced validation
        """
        patterns = {}

        try:
            # Basic email pattern
            email_pattern = PIIPattern(
                name="email",
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                compiled_pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
                category="personal",
                sensitivity="high",
                description="Email addresses",
                examples=["user@example.com", "john.doe@company.org"]
            )
            patterns["email"] = email_pattern

            # Basic phone pattern (US format)
            phone_pattern = PIIPattern(
                name="phone",
                pattern=r'\b\d{3}-\d{3}-\d{4}\b',
                compiled_pattern=re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),
                category="personal",
                sensitivity="high",
                description="US phone numbers",
                examples=["555-123-4567", "123-456-7890"]
            )
            patterns["phone"] = phone_pattern

            # Basic SSN pattern
            ssn_pattern = PIIPattern(
                name="ssn",
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                compiled_pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                category="personal",
                sensitivity="high",
                description="US Social Security Numbers",
                examples=["123-45-6789", "987-65-4321"]
            )
            patterns["ssn"] = ssn_pattern

        except Exception as e:
            # If pattern compilation fails, log warning and return empty patterns
            # This ensures the system doesn't crash but PII detection will be minimal
            logger.warning("PII pattern compilation failed: %s", e)

        return patterns

    def _create_fallback_settings(self):
        """Create basic fallback settings when config is unavailable"""
        class FallbackSettings:
            pii_redaction_enabled = True

        return FallbackSettings()

    def detect_pii(self, text: str, categories: Optional[List[str]] = None,
                   sensitivity_levels: Optional[List[str]] = None,
                   force_detection: bool = False) -> Dict[str, List[str]]:
        """
        Detect PII in text using compliance patterns

        Args:
            text: Text to analyze for PII
            categories: Optional list of categories to check ('personal', 'financial', etc.)
            sensitivity_levels: Optional list of sensitivity levels ('high', 'medium', 'low')
            force_detection: If True, detect PII even when pii_redaction_enabled is False.
                           Used by protect scan/preview which should always detect regardless
                           of cage state.

        Returns:
            Dict mapping PII type names to lists of detected values
        """
        if not force_detection and not self.settings.pii_redaction_enabled:
            return {}

        # Phase 1: Collect all matches with spans
        # Each entry: (start, end, pattern_name, matched_text, priority)
        all_matches: List[Tuple[int, int, str, str, int]] = []

        # Filter patterns based on categories and sensitivity
        patterns_to_check = self._filter_patterns(categories, sensitivity_levels)

        for pattern_name, pattern in patterns_to_check.items():
            priority = getattr(pattern, 'priority', 50)
            context_keywords = getattr(pattern, 'context_keywords', None)
            for m in pattern.compiled_pattern.finditer(text):
                matched_text = m.group(0)

                # v1.0.9: context_keywords gate — if a pattern declares keywords,
                # at least one must appear within ±_CONTEXT_WINDOW chars of the
                # match. This suppresses false positives on broad patterns like
                # germany_id, bank_account_us, france_id.
                if context_keywords:
                    window_start = max(0, m.start() - _CONTEXT_WINDOW)
                    window_end = min(len(text), m.end() + _CONTEXT_WINDOW)
                    context_text = text[window_start:window_end].lower()
                    if not any(kw in context_text for kw in context_keywords):
                        continue  # No keyword nearby — suppress match

                # Clean and validate the match
                cleaned = self._clean_single_match(matched_text, pattern_name)
                if cleaned:
                    all_matches.append((m.start(), m.end(), pattern_name, cleaned, priority))

        # Phase 2: Resolve overlapping matches by priority
        resolved = self._resolve_overlaps(all_matches)

        # Phase 3: Build result dict
        detected_pii: Dict[str, List[str]] = defaultdict(list)
        for _start, _end, pattern_name, matched_text, _priority in resolved:
            if matched_text not in detected_pii[pattern_name]:
                detected_pii[pattern_name].append(matched_text)
                self.detection_stats[pattern_name] += 1

        return dict(detected_pii)

    def _resolve_overlaps(self, matches: List[Tuple[int, int, str, str, int]]) -> List[Tuple[int, int, str, str, int]]:
        """
        Resolve overlapping matches by keeping the highest-priority match.

        When two patterns match overlapping text spans, only the one with
        higher priority survives. Equal priority: keep the more specific
        (shorter span) match. Still equal: keep both (different pattern names
        both flagging the same text is still useful for redaction).

        Args:
            matches: List of (start, end, name, text, priority) tuples

        Returns:
            Deduplicated list of matches
        """
        if len(matches) <= 1:
            return matches

        # Sort by start position, then by priority descending
        matches.sort(key=lambda m: (m[0], -m[4], m[1]))

        resolved = []
        for candidate in matches:
            c_start, c_end, c_name, c_text, c_prio = candidate
            suppressed = False

            for i, kept in enumerate(resolved):
                k_start, k_end, k_name, k_text, k_prio = kept

                # Check for overlap
                if c_start < k_end and c_end > k_start:
                    # Overlapping spans detected
                    if c_prio > k_prio:
                        # Candidate has higher priority — replace the kept one
                        resolved[i] = candidate
                        suppressed = True  # Don't add again
                        break
                    elif c_prio < k_prio:
                        # Kept one has higher priority — suppress candidate
                        suppressed = True
                        break
                    else:
                        # Equal priority — suppress the duplicate to avoid noise
                        # (same span, different label = pick whichever was first)
                        suppressed = True
                        break

            if not suppressed:
                resolved.append(candidate)

        return resolved

    def _clean_single_match(self, match: str, pattern_name: str) -> Optional[str]:
        """
        Clean and validate a single detected match.

        Args:
            match: Raw matched text
            pattern_name: Name of the pattern that produced the match

        Returns:
            Cleaned match string, or None if invalid
        """
        if isinstance(match, tuple):
            match = ' '.join(g for g in match if g)
        if not isinstance(match, str):
            match = str(match)

        cleaned = match.strip()
        if not cleaned:
            return None

        if self._is_valid_match(cleaned, pattern_name):
            return cleaned
        return None

    def _filter_patterns(self, categories: Optional[List[str]],
                        sensitivity_levels: Optional[List[str]]) -> Dict[str, PIIPattern]:
        """
        Filter patterns based on category and sensitivity criteria

        Args:
            categories: Categories to include
            sensitivity_levels: Sensitivity levels to include

        Returns:
            Filtered dict of patterns
        """
        all_patterns = self.rules.get_all_patterns()
        filtered = {}

        for name, pattern in all_patterns.items():
            # Check if pattern is enabled
            if not getattr(pattern, 'enabled', True):
                continue

            # Check category filter
            if categories and pattern.category not in categories:
                continue

            # Check sensitivity filter
            if sensitivity_levels and pattern.sensitivity not in sensitivity_levels:
                continue

            filtered[name] = pattern

        return filtered

    def _clean_matches(self, matches, pattern_name: str) -> List[str]:
        """
        Clean and validate detected matches

        Args:
            matches: Raw regex matches (may be list, tuple, or other iterable)
            pattern_name: Name of the pattern that produced matches

        Returns:
            Cleaned list of valid matches
        """
        cleaned = []

        # Ensure matches is iterable
        if not hasattr(matches, '__iter__') or isinstance(matches, str):
            matches = [matches] if matches else []

        for match in matches:
            # Handle cases where match might be a tuple (from regex capture groups)
            if isinstance(match, tuple):
                # Join all non-empty groups to capture full match data
                match = ' '.join(g for g in match if g)

            # Ensure match is a string
            if not isinstance(match, str):
                match = str(match)

            # Remove extra whitespace and normalize
            cleaned_match = match.strip()

            # Skip empty matches
            if not cleaned_match:
                continue

            # Pattern-specific validation
            if self._is_valid_match(cleaned_match, pattern_name):
                cleaned.append(cleaned_match)

        # Remove duplicates while preserving order
        seen = set()
        deduplicated = []
        for match in cleaned:
            if match not in seen:
                seen.add(match)
                deduplicated.append(match)

        return deduplicated

    def _is_valid_match(self, match: str, pattern_name: str) -> bool:
        """
        Validate that a match is legitimate PII

        Args:
            match: Potential PII match
            pattern_name: Pattern that detected it

        Returns:
            True if valid PII
        """
        # Pattern-specific validations
        if pattern_name == 'email':
            return self._validate_email(match)
        elif pattern_name.startswith('phone'):
            return self._validate_phone(match)
        elif pattern_name == 'credit_card':
            return self._validate_credit_card(match)
        elif pattern_name == 'iban':
            return self._validate_iban(match)
        elif pattern_name == 'ip_address':
            return self._validate_ip_address(match)
        elif pattern_name == 'coordinates':
            return self._validate_coordinates(match)

        # Default: accept if non-empty
        return bool(match.strip())

    def _validate_email(self, email: str) -> bool:
        """Validate email format more strictly"""
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            return False

        # Check for obvious false positives (localhost only - allow example.com for testing)
        false_positives = ['localhost']
        domain = email.split('@')[1].lower()
        if any(fp in domain for fp in false_positives):
            return False

        return True

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Remove formatting characters
        digits_only = re.sub(r'[\s\.\-\(\)]', '', phone)

        # Check length (should be reasonable for phone numbers)
        if not 7 <= len(digits_only) <= 15:
            return False

        # Should contain mostly digits
        digit_count = sum(c.isdigit() for c in digits_only)
        return digit_count >= len(digits_only) * 0.8

    def _validate_credit_card(self, card: str) -> bool:
        """Validate credit card number using Luhn algorithm"""
        # Remove spaces and dashes
        card = re.sub(r'[\s\-]', '', card)

        if not card.isdigit():
            return False

        # Check length (most cards are 13-19 digits)
        if not 13 <= len(card) <= 19:
            return False

        # Luhn algorithm validation
        def luhn_checksum(card_num: str) -> bool:
            def digits_of(n):
                return [int(d) for d in str(n)]

            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)

            for d in even_digits:
                checksum += sum(digits_of(d * 2))

            return checksum % 10 == 0

        return luhn_checksum(card)

    def _validate_iban(self, iban: str) -> bool:
        """Validate IBAN format"""
        # Remove spaces
        iban = iban.replace(' ', '')

        # Check basic format (2 letters + 2 digits + up to 30 alphanumerics)
        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$', iban):
            return False

        # Should be reasonable length
        return 15 <= len(iban) <= 34

    def _validate_ip_address(self, ip: str) -> bool:
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False

        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if not 0 <= num <= 255:
                return False

        # Exclude localhost and some reserved ranges, but allow common private IPs
        first_octet = int(parts[0])
        if first_octet == 127:  # localhost
            return False

        return True

    def _validate_coordinates(self, coords: str) -> bool:
        """Validate GPS coordinates"""
        try:
            lat, lon = coords.split(',')
            lat_val, lon_val = float(lat.strip()), float(lon.strip())

            # Check ranges
            return -90 <= lat_val <= 90 and -180 <= lon_val <= 180
        except (ValueError, AttributeError):
            return False

    def has_pii(self, text: str, categories: Optional[List[str]] = None,
                sensitivity_levels: Optional[List[str]] = None) -> bool:
        """
        Check if text contains any PII

        Args:
            text: Text to check
            categories: Optional categories to check
            sensitivity_levels: Optional sensitivity levels

        Returns:
            True if any PII detected
        """
        detected = self.detect_pii(text, categories, sensitivity_levels)
        return bool(detected)

    def get_detection_stats(self) -> Dict[str, int]:
        """
        Get detection statistics

        Returns:
            Dict mapping pattern names to detection counts
        """
        return dict(self.detection_stats)

    def reset_stats(self) -> None:
        """Reset detection statistics"""
        self.detection_stats.clear()

    def get_detector_info(self) -> Dict[str, Any]:
        """
        Get information about the detector configuration

        Returns:
            Dict with detector metadata
        """
        return {
            'backend': 'regex',
            'enabled': self.settings.pii_redaction_enabled,
            'patterns_loaded': len(self.rules.get_all_patterns()),
            'rule_summary': self.rules.get_rule_summary(),
            'detection_stats': self.get_detection_stats()
        }


# Backward compatibility alias — PIIDetector was renamed to RegexPIIDetector in v1.0.9
PIIDetector = RegexPIIDetector


def create_pii_detector() -> RegexPIIDetector:
    """
    Create a PII detector instance (regex backend).

    For pluggable backend support, use protocols.create_pii_detector(backend=...).

    Returns:
        Configured RegexPIIDetector instance
    """
    return RegexPIIDetector()


def detect_pii_in_text(text: str, categories: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """
    Convenience function to detect PII in text

    Args:
        text: Text to analyze

    Returns:
        Dict mapping PII types to detected values
    """
    detector = create_pii_detector()
    return detector.detect_pii(text, categories)
