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
PII Detector Protocol — pluggable backend interface for AKIOS

Defines the contract that all PII detector backends must implement.
The default backend is RegexPIIDetector (rules.py + detector.py).
Alternative backends (e.g. Presidio) can implement this protocol
and be swapped in via config.yaml: pii_backend: "presidio"

v1.0.8 — Pluggable PII Backend Interface
"""

from typing import Dict, List, Optional, Any, Protocol, runtime_checkable


@runtime_checkable
class PIIDetectorProtocol(Protocol):
    """
    Protocol defining the contract for PII detector backends.

    Any class implementing this protocol can be used as a PII detection
    backend in AKIOS. The default implementation is RegexPIIDetector.

    Implementors must provide:
      - detect_pii(): core detection returning {type: [values]}
      - has_pii(): quick boolean check
      - get_detector_info(): metadata about the detector
    """

    def detect_pii(
        self,
        text: str,
        categories: Optional[List[str]] = None,
        sensitivity_levels: Optional[List[str]] = None,
        force_detection: bool = False,
    ) -> Dict[str, List[str]]:
        """
        Detect PII in text.

        Args:
            text: Text to analyze for PII
            categories: Optional list of categories to check
                ('personal', 'financial', 'health', 'location', 'communication', 'digital')
            sensitivity_levels: Optional list of sensitivity levels ('high', 'medium', 'low')
            force_detection: If True, detect PII even when pii_redaction_enabled is False

        Returns:
            Dict mapping PII type names to lists of detected values.
            Example: {'email': ['user@example.com'], 'ssn': ['123-45-6789']}
        """
        ...

    def has_pii(
        self,
        text: str,
        categories: Optional[List[str]] = None,
        sensitivity_levels: Optional[List[str]] = None,
    ) -> bool:
        """
        Quick check if text contains any PII.

        Args:
            text: Text to check
            categories: Optional categories to check
            sensitivity_levels: Optional sensitivity levels

        Returns:
            True if any PII detected
        """
        ...

    def get_detector_info(self) -> Dict[str, Any]:
        """
        Get information about the detector configuration.

        Returns:
            Dict with detector metadata including:
              - 'backend': str (e.g. 'regex', 'presidio')
              - 'enabled': bool
              - 'patterns_loaded': int
              - Any backend-specific metadata
        """
        ...


def create_pii_detector(backend: Optional[str] = None) -> PIIDetectorProtocol:
    """
    Factory function to create a PII detector instance.

    Args:
        backend: Backend name. None = auto-detect from settings.
                 Supported: 'regex' (default), 'presidio' (future)

    Returns:
        A PIIDetectorProtocol-compatible detector instance

    Raises:
        ValueError: If backend is not supported
    """
    if backend is None:
        # Auto-detect from settings
        try:
            from ...config import get_settings
            settings = get_settings()
            backend = getattr(settings, 'pii_backend', 'regex')
        except Exception:
            backend = 'regex'

    if backend == 'regex':
        from .detector import RegexPIIDetector
        return RegexPIIDetector()
    elif backend == 'presidio':
        raise ValueError(
            "Presidio backend is not yet available. "
            "Install akios-pro for Presidio support, or use pii_backend: 'regex'"
        )
    else:
        raise ValueError(
            f"Unknown PII backend: '{backend}'. "
            f"Supported backends: 'regex'. Future: 'presidio'"
        )
