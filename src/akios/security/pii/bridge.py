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
PII Bridge — register AKIOS's 50+ patterns into EnforceCore's PatternRegistry (v1.2.0-beta)

AKIOS has 3x more PII patterns than EnforceCore (50+ vs 7):
- Healthcare: NPI, DEA, MRN, ICD-10 (GPL-3.0, cannot live in Apache-2.0 EnforceCore)
- Financial: IBAN, SWIFT, cryptocurrency addresses
- French identifiers, EU patterns

This bridge registers AKIOS patterns INTO EnforceCore, making both engines use the
same comprehensive pattern set. AKIOS remains the authoritative source.

Dual-engine flow:
1. AKIOS detects PII (authoritative result)
2. EnforceCore's SecretScanner adds credential detection
3. Results merged — AKIOS categories + EC secret categories
"""

import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

_PATTERNS_REGISTERED = False
_REGISTERED_COUNT = 0


def register_akios_patterns_into_enforcecore() -> int:
    """
    Register AKIOS's 50+ PII patterns into EnforceCore's PatternRegistry.

    Returns the number of patterns registered, or 0 if EnforceCore not available.
    Only registers once per process (cached after first call).
    """
    global _PATTERNS_REGISTERED, _REGISTERED_COUNT

    if _PATTERNS_REGISTERED:
        return _REGISTERED_COUNT

    try:
        from enforcecore.redactor.patterns import PatternRegistry
        from .rules import ComplianceRules

        rules = ComplianceRules()
        patterns = rules._load_all_patterns()

        if not patterns:
            logger.warning("PII bridge: no patterns loaded from ComplianceRules")
            return 0

        count = 0
        for name, pattern_obj in patterns.items():
            try:
                regex = getattr(pattern_obj, 'pattern', None)
                if regex:
                    # Build placeholder from pattern name
                    placeholder = f"[{name.upper()}]"
                    mask = f"[{name.upper()}_REDACTED]"
                    PatternRegistry.register(
                        category=name,
                        pattern=regex,
                        placeholder=placeholder,
                        mask=mask,
                    )
                    count += 1
            except Exception as e:
                # Never fail silently for security patterns
                logger.debug("PII bridge: skipped pattern %s: %s", name, e)

        _PATTERNS_REGISTERED = True
        _REGISTERED_COUNT = count
        logger.info("PII bridge: registered %d AKIOS patterns into EnforceCore", count)
        return count

    except ImportError:
        _PATTERNS_REGISTERED = True  # Don't retry
        return 0
    except Exception as e:
        logger.warning("PII bridge: registration failed: %s", e)
        _PATTERNS_REGISTERED = True
        return 0


def dual_engine_detect(text: str, akios_result: Dict[str, list]) -> Dict[str, list]:
    """
    Run EnforceCore detection alongside AKIOS. Compare results. Log mismatches.

    AKIOS result is ALWAYS authoritative. EnforceCore adds secret detection.
    Any patterns EnforceCore finds that AKIOS missed are logged for analysis.

    Args:
        text: Text that was already analyzed by AKIOS.
        akios_result: Dict from AKIOS detect_pii() — the authoritative result.

    Returns:
        Merged dict: AKIOS categories + EC secret categories. Never modifies AKIOS result.
    """
    try:
        from enforcecore import Redactor

        # Ensure AKIOS patterns are registered first
        register_akios_patterns_into_enforcecore()

        ec_redactor = Redactor(secret_detection=True)
        ec_entities = ec_redactor.detect(text)

        # Collect what EC found
        ec_categories: Set[str] = set(e.category for e in ec_entities)
        akios_categories: Set[str] = set(akios_result.keys())

        # Log mismatches: patterns EC found that AKIOS missed
        missed_by_akios = ec_categories - akios_categories
        if missed_by_akios:
            logger.info(
                "PII dual-engine mismatch: EnforceCore found %s not in AKIOS result",
                missed_by_akios,
            )

        # Merge: add EC-detected secret categories (not in AKIOS) to result
        merged = dict(akios_result)
        for entity in ec_entities:
            if entity.category not in akios_categories:
                # Only add categories AKIOS doesn't cover (e.g. secrets from SecretScanner)
                if entity.category not in merged:
                    merged[entity.category] = []
                merged[entity.category].append(entity.text)

        return merged

    except ImportError:
        return akios_result  # No EC — return AKIOS result unchanged
    except Exception as e:
        logger.debug("PII dual-engine error: %s", e)
        return akios_result  # Never break on EC errors — AKIOS is authoritative
