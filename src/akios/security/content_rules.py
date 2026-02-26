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
Content rule enforcement bridge — AKIOS to EnforceCore RuleEngine (v1.2.0+)

Checks text/config for dangerous content patterns:
- Shell injection: rm -rf, sudo, backticks, $(), pipe to bash
- SQL injection: OR 1=1, UNION SELECT, DROP TABLE
- Path traversal: ../, null bytes, /etc/passwd
- Code execution: eval(), exec(), __import__()

Gracefully degrades to empty list (no blocking) when EnforceCore not installed.
Install with: pip install akios[enforcecore]
"""

from typing import Any, Dict, List


def check_content_rules(text: str, raise_on_violation: bool = False) -> List[Dict[str, Any]]:
    """
    Check text for dangerous content using EnforceCore built-in rules.

    Args:
        text: Text or serialized config to check.
        raise_on_violation: If True, raises ValueError on first violation.

    Returns:
        List of violation dicts: [{"rule": str, "matched": str, "action": str}]
        Empty list when no violations or EnforceCore not installed.
    """
    try:
        from enforcecore.core.rules import RuleEngine
        engine = RuleEngine.with_builtins()
        violations = engine.check(str(text))

        result = [
            {
                "rule": v.rule_name,
                "matched": v.matched_text,
                "action": v.action,
                "description": v.description,
            }
            for v in violations
        ]

        if raise_on_violation and result:
            first = result[0]
            raise ValueError(
                f"Content rule violation [{first['rule']}]: {first['matched']!r} detected"
            )

        return result

    except ImportError:
        return []  # No EnforceCore — no content rules (fail open, not closed)
    except ValueError:
        raise
    except Exception:
        return []  # Never block execution due to rule engine errors


def check_agent_config(agent_type: str, config: dict) -> List[Dict[str, Any]]:
    """
    Run content rules on a serialized agent config.
    Used in step_executor.validate_agent_config.
    """
    import json
    config_text = json.dumps(config, default=str)
    return check_content_rules(config_text)


BUILTIN_RULES = ["shell_injection", "path_traversal", "sql_injection", "code_execution"]
