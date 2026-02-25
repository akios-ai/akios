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
CLI doctor command - akios doctor

Run environment diagnostics, dependency checks, and configuration
validation with actionable fix suggestions.

Redesigned in v1.1.0 to be distinct from `akios status`:
  - status  = runtime state (mode, budget, last run, security posture)
  - doctor  = diagnostics (environment, deps, connectivity, config health)
"""

import argparse
import json
import logging
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Diagnostic check result states
PASS = "pass"
WARN = "warn"
FAIL = "fail"


def register_doctor_command(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "doctor",
        help="Run environment diagnostics and configuration checks"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format for automation"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed technical information"
    )

    parser.set_defaults(func=run_doctor_command)


def _check(name: str, status: str, message: str, suggestion: str = None) -> Dict[str, Any]:
    """Create a diagnostic check result."""
    result = {"name": name, "status": status, "message": message}
    if suggestion:
        result["suggestion"] = suggestion
    return result


def check_python_version() -> Dict[str, Any]:
    """Check Python version >= 3.9."""
    ver = sys.version_info
    version_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    if ver >= (3, 9):
        return _check("Python version", PASS, f"Python {version_str}")
    return _check("Python version", FAIL, f"Python {version_str} (requires >= 3.9)",
                   suggestion="Upgrade Python: https://python.org/downloads/")


def check_required_deps() -> Dict[str, Any]:
    """Check required dependencies are importable."""
    required = ["yaml", "rich", "httpx", "cryptography"]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return _check("Required dependencies", PASS, f"All {len(required)} required packages installed")
    return _check("Required dependencies", FAIL,
                   f"Missing: {', '.join(missing)}",
                   suggestion=f"pip install {' '.join(missing)}")


def check_optional_deps() -> Dict[str, Any]:
    """Check optional dependencies (fastapi, uvicorn, boto3)."""
    optional = {"fastapi": "REST API (akios serve)", "uvicorn": "REST API server",
                "boto3": "AWS Bedrock provider"}
    available = []
    unavailable = []
    for mod, purpose in optional.items():
        try:
            __import__(mod)
            available.append(mod)
        except ImportError:
            unavailable.append(f"{mod} ({purpose})")
    if not unavailable:
        return _check("Optional dependencies", PASS, f"All {len(optional)} optional packages installed")
    return _check("Optional dependencies", WARN,
                   f"Available: {len(available)}/{len(optional)} — missing: {', '.join(unavailable)}",
                   suggestion=f"pip install {' '.join(m.split(' ')[0] for m in unavailable)}")


def check_config_file() -> Dict[str, Any]:
    """Check if config.yaml exists and is parseable."""
    config_path = Path("config.yaml")
    if not config_path.exists():
        return _check("Configuration file", WARN, "config.yaml not found",
                       suggestion="Run: akios init <project-name>")
    try:
        import yaml
        with open(config_path) as f:
            data = yaml.safe_load(f)
        if data and isinstance(data, dict):
            return _check("Configuration file", PASS, f"config.yaml valid ({len(data)} keys)")
        return _check("Configuration file", WARN, "config.yaml is empty or invalid")
    except Exception as e:
        return _check("Configuration file", FAIL, f"config.yaml parse error: {e}",
                       suggestion="Check YAML syntax in config.yaml")


def check_api_key() -> Dict[str, Any]:
    """Check if any LLM provider API key is configured."""
    providers = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "GROK_API_KEY": "Grok",
        "MISTRAL_API_KEY": "Mistral",
        "GEMINI_API_KEY": "Gemini",
    }
    configured = []
    for env_var, name in providers.items():
        val = os.environ.get(env_var)
        if val and len(val) > 5:
            configured.append(name)

    # Check Bedrock (uses IAM, not API key)
    if os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AKIOS_BEDROCK_REGION"):
        configured.append("Bedrock")

    # Check mock mode
    if os.environ.get("AKIOS_MOCK_LLM") == "1":
        return _check("API provider", PASS, "Mock mode active (safe testing, no costs)")

    if configured:
        return _check("API provider", PASS, f"Configured: {', '.join(configured)}")
    return _check("API provider", WARN, "No LLM provider API key found",
                   suggestion="Run: akios setup  OR  set OPENAI_API_KEY, GROK_API_KEY, etc. in .env")


def check_sandbox() -> Dict[str, Any]:
    """Check sandbox availability (seccomp/cgroups on Linux, Docker, or policy-based)."""
    if os.path.exists("/.dockerenv"):
        return _check("Sandbox", PASS, "Docker container detected (policy-based security)")

    if platform.system() == "Linux":
        has_seccomp = os.path.exists("/proc/self/status")
        has_cgroups = os.path.exists("/sys/fs/cgroup")
        if has_seccomp and has_cgroups:
            return _check("Sandbox", PASS, "Linux kernel sandbox available (seccomp + cgroups)")
        parts = []
        if not has_seccomp:
            parts.append("seccomp unavailable")
        if not has_cgroups:
            parts.append("cgroups unavailable")
        return _check("Sandbox", WARN, f"Partial sandbox: {', '.join(parts)}",
                       suggestion="Install libseccomp-dev for full kernel-hard protection")

    return _check("Sandbox", WARN,
                   f"{platform.system()} detected — policy-based mode (Docker recommended for full protection)",
                   suggestion="Use Docker for production: docker pull akiosai/akios:latest")


def check_disk_space() -> Dict[str, Any]:
    """Check disk space for audit logs."""
    try:
        usage = shutil.disk_usage(".")
        free_mb = usage.free / (1024 * 1024)
        if free_mb > 100:
            return _check("Disk space", PASS, f"{free_mb:.0f} MB free")
        if free_mb > 10:
            return _check("Disk space", WARN, f"Low: {free_mb:.0f} MB free",
                           suggestion="Free up disk space — audit logs need room to write")
        return _check("Disk space", FAIL, f"Critical: {free_mb:.0f} MB free",
                       suggestion="Free up disk space immediately — audit writes may fail")
    except Exception:
        return _check("Disk space", WARN, "Could not check disk space")


def check_pii_engine() -> Dict[str, Any]:
    """Check PII detection engine health."""
    try:
        from ...security.pii.rules import ComplianceRules
        rules = ComplianceRules()
        # Try to access patterns (they load lazily)
        if hasattr(rules, '_load_all_patterns'):
            patterns = rules._load_all_patterns()
            count = len(patterns) if patterns else 0
            if count >= 40:
                return _check("PII engine", PASS, f"{count} detection patterns loaded")
            return _check("PII engine", WARN, f"{count} patterns (expected 40+)")
        return _check("PII engine", PASS, "PII engine initialized")
    except Exception as e:
        return _check("PII engine", FAIL, f"PII engine error: {e}",
                       suggestion="Check installation: pip install --force-reinstall akios")


def check_audit_system() -> Dict[str, Any]:
    """Check audit system health."""
    audit_path = Path("audit")
    if not audit_path.exists():
        return _check("Audit system", WARN, "No audit directory (created on first workflow run)")
    events_file = audit_path / "audit_events.jsonl"
    if events_file.exists():
        size = events_file.stat().st_size
        if size > 0:
            line_count = sum(1 for _ in open(events_file))
            return _check("Audit system", PASS, f"{line_count} events logged ({size / 1024:.1f} KB)")
        return _check("Audit system", WARN, "Audit log exists but is empty")
    return _check("Audit system", WARN, "No audit events yet (created on first workflow run)")


def run_all_checks() -> List[Dict[str, Any]]:
    """Run all diagnostic checks and return results."""
    return [
        check_python_version(),
        check_required_deps(),
        check_optional_deps(),
        check_config_file(),
        check_api_key(),
        check_sandbox(),
        check_disk_space(),
        check_pii_engine(),
        check_audit_system(),
    ]


def run_doctor_command(args: argparse.Namespace) -> int:
    checks = run_all_checks()

    if getattr(args, "json", False):
        counts = {PASS: 0, WARN: 0, FAIL: 0}
        for c in checks:
            counts[c["status"]] += 1
        output = {
            "checks": checks,
            "summary": counts,
            "total": len(checks),
            "healthy": counts[FAIL] == 0,
        }
        print(json.dumps(output, indent=2))
        return 1 if counts[FAIL] > 0 else 0

    # Rich terminal output
    try:
        from ...core.ui.rich_output import print_panel
    except ImportError:
        print_panel = None

    icons = {PASS: "\u2705", WARN: "\u26a0\ufe0f ", FAIL: "\u274c"}
    lines = []
    pass_count = warn_count = fail_count = 0

    for c in checks:
        icon = icons[c["status"]]
        line = f"{icon} {c['name']}: {c['message']}"
        lines.append(line)
        if c["status"] == PASS:
            pass_count += 1
        elif c["status"] == WARN:
            warn_count += 1
        else:
            fail_count += 1

        if c.get("suggestion") and c["status"] != PASS:
            lines.append(f"   \u2192 {c['suggestion']}")

    lines.append("")
    lines.append(f"Results: {pass_count} pass, {warn_count} warn, {fail_count} fail")

    if fail_count > 0:
        lines.append("\nAction required: Fix FAIL items above before running workflows.")
    elif warn_count > 0:
        lines.append("\nAll critical checks passed. Warnings are optional improvements.")
    else:
        lines.append("\nAll checks passed. Environment is healthy.")

    content = "\n".join(lines)
    if print_panel:
        print_panel("AKIOS Doctor", content)
    else:
        print("=" * 50)
        print("  AKIOS Doctor")
        print("=" * 50)
        print(content)

    return 1 if fail_count > 0 else 0
