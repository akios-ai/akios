# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Output Extractor — Unified output key-probing and step result processing.

Extracts human-readable strings from agent results using a canonical
key priority: text → content → output → result → response → stdout → data

Used by the template renderer (for {previous_output} substitution),
the engine (for finalization), and step output display.
"""

from typing import Any

# Canonical key priority used everywhere in AKIOS.
# All output extraction uses this single ordering.
OUTPUT_KEY_ORDER = ('text', 'content', 'output', 'result', 'response', 'stdout', 'data')

# Maximum output string length (prevents memory issues with huge results)
MAX_OUTPUT_LENGTH = 2000


def extract_output_value(result: Any) -> str:
    """
    Extract a human-readable string from a step result.

    Uses a **single, canonical key priority** so that ``{previous_output}``,
    ``{step_X_output}``, and ``extract_step_output`` all agree.

    Priority: text → content → output → result → response → stdout → data

    Args:
        result: Raw step result (dict, list, or scalar).

    Returns:
        Extracted string (truncated to 2000 chars).
    """
    if not isinstance(result, dict):
        return str(result)[:MAX_OUTPUT_LENGTH] if result else ''

    for key in OUTPUT_KEY_ORDER:
        val = result.get(key)
        if val is not None:
            return str(val)[:MAX_OUTPUT_LENGTH]

    # Filesystem write summary
    if result.get('written'):
        return f"Written to {result.get('path', '?')} ({result.get('size', '?')} bytes)"

    # Fallback: serialise (skip internal keys)
    summary = {k: v for k, v in result.items() if k not in ('cost_incurred',)}
    return str(summary)[:MAX_OUTPUT_LENGTH] if summary else ''


def extract_step_output(step_result: Any) -> str:
    """
    Extract human-readable output from a step result dict.

    Different agents return results with different keys:
      - LLM → text
      - Filesystem read → content
      - Filesystem write → written + path
      - HTTP → content / json
      - Tool executor → stdout

    Args:
        step_result: The full step result dict (containing 'result' key).

    Returns:
        Extracted string (truncated to 2000 chars).
    """
    if not isinstance(step_result, dict):
        return str(step_result)[:MAX_OUTPUT_LENGTH]

    result = step_result.get('result')
    if not isinstance(result, dict):
        return str(result)[:MAX_OUTPUT_LENGTH] if result else ''

    return extract_output_value(result)
