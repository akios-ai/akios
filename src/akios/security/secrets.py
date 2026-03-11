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
Secret detection bridge — AKIOS to EnforceCore SecretScanner (v1.2.0+)

Scans text for leaked credentials: AWS keys, GitHub tokens, PEM private keys,
database connection strings, etc. (11 categories via EnforceCore).

Gracefully degrades to a no-op when EnforceCore is not installed.
Install with: pip install akios[enforcecore]
"""

from typing import Any, Dict, List


def is_enforcecore_available() -> bool:
    """Check whether EnforceCore is installed."""
    try:
        import enforcecore  # noqa: F401
        return True
    except ImportError:
        return False


def scan_secrets(text: str) -> Dict[str, Any]:
    """
    Scan text for leaked secrets/credentials using EnforceCore SecretScanner.

    Returns a dict with:
        - secrets_found (int): number of secrets detected
        - categories (list[str]): unique categories found
        - details (list[dict]): each detection with category, start, end
        - enforcecore_available (bool): whether EnforceCore was used

    When EnforceCore is not installed, returns zeros with enforcecore_available=False.
    """
    try:
        from enforcecore.redactor.secrets import SecretScanner
        scanner = SecretScanner()
        results = scanner.detect(text)
        return {
            "secrets_found": len(results),
            "categories": sorted(set(r.category for r in results)),
            "details": [
                {"category": r.category, "start": r.start, "end": r.end}
                for r in results
            ],
            "enforcecore_available": True,
        }
    except ImportError:
        return {
            "secrets_found": 0,
            "categories": [],
            "details": [],
            "enforcecore_available": False,
        }
    except Exception:
        return {
            "secrets_found": 0,
            "categories": [],
            "details": [],
            "enforcecore_available": True,
            "error": "SecretScanner error",
        }


def get_supported_categories() -> List[str]:
    """Return the list of secret categories supported by EnforceCore."""
    return [
        "aws_access_key",
        "aws_secret_key",
        "github_token",
        "generic_api_key",
        "bearer_token",
        "private_key",
        "password_in_url",
        "gcp_service_account",
        "azure_connection_string",
        "database_connection_string",
        "ssh_private_key",
    ]
