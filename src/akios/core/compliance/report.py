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
Compliance report generator for AKIOS.

Generates compliance reports for workflow execution and security validation.
Scores are computed from real runtime data — audit ledger, cage status,
budget configuration — never hardcoded.
"""

from typing import Dict, Any, Optional, List
import json
import platform
from pathlib import Path
from datetime import datetime, timezone


def _get_settings_safe():
    """Load settings, returning None on failure."""
    try:
        from ...config import get_settings
        return get_settings()
    except Exception:
        return None


def _get_ledger_safe():
    """Load audit ledger, returning None on failure."""
    try:
        from ..audit.ledger import get_ledger
        return get_ledger()
    except Exception:
        return None


def _check_syscall_available() -> bool:
    """Check if kernel syscall filtering is available."""
    try:
        from ...security.validation import _syscall_filtering_available
        return _syscall_filtering_available()
    except Exception:
        return False


def _check_sandbox_available() -> bool:
    """Check if cgroups sandbox is available."""
    try:
        from ...security.validation import _sandbox_available
        return _sandbox_available()
    except Exception:
        return False


class ComplianceGenerator:
    """
    Generates compliance reports for AKIOS workflows.

    Scores are derived from real data:
    - Security score: cage status, PII redaction, sandbox, syscall filtering
    - Audit score: event count, Merkle integrity
    - Cost score: budget limits configured, no overruns
    """

    def __init__(self):
        """Initialize the compliance generator."""
        self.report_data = {}

    def _read_security_state(self) -> Dict[str, Any]:
        """Read actual security configuration state."""
        settings = _get_settings_safe()
        if settings is None:
            return {
                "pii_redaction": False,
                "audit_logging": False,
                "syscall_filtering": False,
                "process_isolation": False,
                "network_locked": False,
                "sandbox_enabled": False,
                "_settings_available": False,
            }

        return {
            "pii_redaction": getattr(settings, "pii_redaction_enabled", False),
            "audit_logging": getattr(settings, "audit_enabled", True),
            "syscall_filtering": _check_syscall_available(),
            "process_isolation": _check_sandbox_available(),
            "network_locked": not getattr(settings, "network_access_allowed", True),
            "sandbox_enabled": getattr(settings, "sandbox_enabled", False),
            "_settings_available": True,
        }

    def _read_audit_state(self) -> Dict[str, Any]:
        """Read actual audit ledger state."""
        ledger = _get_ledger_safe()
        if ledger is None:
            return {
                "event_count": 0,
                "merkle_root": None,
                "integrity_verified": False,
                "_ledger_available": False,
            }

        try:
            event_count = ledger.size()
        except Exception:
            event_count = 0

        try:
            merkle_root = ledger.get_merkle_root()
        except Exception:
            merkle_root = None

        try:
            integrity_ok = ledger.verify_integrity() if event_count > 0 else False
        except Exception:
            integrity_ok = False

        return {
            "event_count": event_count,
            "merkle_root": merkle_root,
            "integrity_verified": integrity_ok,
            "_ledger_available": True,
        }

    def _read_cost_state(self) -> Dict[str, Any]:
        """Read actual cost/budget configuration."""
        settings = _get_settings_safe()
        if settings is None:
            return {
                "budget_limit": None,
                "budget_configured": False,
                "_settings_available": False,
            }

        budget_limit = getattr(settings, "budget_limit_per_run", None)
        return {
            "budget_limit": budget_limit,
            "budget_configured": budget_limit is not None and budget_limit > 0,
            "_settings_available": True,
        }

    def _count_pii_events(self) -> int:
        """Count PII detection events from audit log."""
        ledger = _get_ledger_safe()
        if ledger is None:
            return 0
        try:
            events = ledger.get_all_events()
            return sum(
                1 for e in events
                if getattr(e, "event_type", "") in ("pii_scan", "pii_redaction", "pii_detection")
            )
        except Exception:
            return 0

    def _compute_security_score(self, security: Dict[str, Any]) -> float:
        """
        Compute security score from real state.

        5.0 = All protections active (PII + sandbox + syscall + network locked)
        4.0 = PII + sandbox active, missing syscall or network lock
        3.0 = PII active, sandbox/syscall missing
        2.0 = Some protections active
        1.0 = Minimal protections
        0.0 = No settings available
        """
        if not security.get("_settings_available", False):
            return 0.0

        score = 0.0
        if security.get("pii_redaction"):
            score += 2.0
        if security.get("sandbox_enabled"):
            score += 1.0
        if security.get("syscall_filtering"):
            score += 1.0
        if security.get("network_locked"):
            score += 0.5
        if security.get("process_isolation"):
            score += 0.5
        return min(score, 5.0)

    def _compute_audit_score(self, audit: Dict[str, Any]) -> float:
        """
        Compute audit score from real state.

        5.0 = Events exist + Merkle integrity verified
        4.0 = Events exist + Merkle root present (not verified)
        3.0 = Events exist, no Merkle
        1.0 = Ledger available but empty
        0.0 = Ledger unavailable
        """
        if not audit.get("_ledger_available", False):
            return 0.0

        event_count = audit.get("event_count", 0)
        if event_count == 0:
            return 1.0

        if audit.get("integrity_verified"):
            return 5.0

        if audit.get("merkle_root"):
            return 4.0

        return 3.0

    def _compute_cost_score(self, cost: Dict[str, Any]) -> float:
        """
        Compute cost score from real state.

        5.0 = Budget limits configured and enforced
        3.0 = Settings available but no budget limit set
        0.0 = Settings unavailable
        """
        if not cost.get("_settings_available", False):
            return 0.0

        if cost.get("budget_configured"):
            return 5.0

        return 3.0

    def _build_findings(self, security: Dict, audit: Dict, cost: Dict) -> List[str]:
        """Generate findings based on real state."""
        findings = []

        if not security.get("_settings_available"):
            findings.append("Settings not available — cannot assess compliance")
            return findings

        if not security.get("pii_redaction"):
            findings.append("PII redaction is DISABLED — data may be exposed in logs")
        if not security.get("sandbox_enabled"):
            findings.append("Sandbox is DISABLED — processes not isolated")
        if not security.get("syscall_filtering"):
            findings.append("Syscall filtering unavailable — requires Linux with root")
        if not security.get("network_locked"):
            findings.append("Network access is ALLOWED — outbound requests not restricted")

        if audit.get("_ledger_available") and audit.get("event_count", 0) == 0:
            findings.append("Audit ledger is empty — no workflow executions recorded")
        if audit.get("event_count", 0) > 0 and not audit.get("integrity_verified"):
            findings.append("Audit Merkle integrity NOT verified")

        if not cost.get("budget_configured"):
            findings.append("No budget limit configured — cost overruns possible")

        return findings

    def _build_recommendations(self, security: Dict, audit: Dict, cost: Dict) -> List[str]:
        """Generate recommendations based on real state."""
        recs = []

        if not security.get("pii_redaction"):
            recs.append("Enable PII redaction: set pii_redaction_enabled: true in config.yaml")
        if not security.get("sandbox_enabled"):
            recs.append("Enable sandbox: run 'akios cage up'")
        if not security.get("network_locked"):
            recs.append("Lock network: set network_access_allowed: false in config.yaml")
        if not cost.get("budget_configured"):
            recs.append("Set budget limit: add budget_limit_per_run to config.yaml")
        if audit.get("event_count", 0) == 0:
            recs.append("Run a workflow to generate audit data for compliance assessment")

        return recs

    def generate_report(self, workflow_name: str, report_type: str = "basic") -> Dict[str, Any]:
        """
        Generate a compliance report for a workflow.

        All scores are computed from real runtime data.

        Args:
            workflow_name: Name of the workflow
            report_type: Type of report (basic, detailed, executive)

        Returns:
            Compliance report data
        """
        now = datetime.now(tz=timezone.utc)

        # Read real state
        security = self._read_security_state()
        audit = self._read_audit_state()
        cost = self._read_cost_state()

        # Public security validation (booleans only, no internal keys)
        security_validation = {
            "pii_redaction": security.get("pii_redaction", False),
            "audit_logging": security.get("audit_logging", False),
            "syscall_filtering": security.get("syscall_filtering", False),
            "process_isolation": security.get("process_isolation", False),
        }

        # Compute real scores
        security_score = self._compute_security_score(security)
        audit_score = self._compute_audit_score(audit)
        cost_score = self._compute_cost_score(cost)

        component_scores = {
            "security": security_score,
            "audit": audit_score,
            "cost": cost_score,
        }
        overall_score = round(sum(component_scores.values()) / len(component_scores), 1)

        # Map score to level
        if overall_score >= 4.5:
            overall_level = "excellent"
        elif overall_score >= 3.5:
            overall_level = "good"
        elif overall_score >= 2.5:
            overall_level = "fair"
        else:
            overall_level = "poor"

        # Determine compliance status
        has_data = security.get("_settings_available", False)
        if not has_data:
            compliance_status = "unknown"
        elif overall_score >= 3.5:
            compliance_status = "compliant"
        elif overall_score >= 2.0:
            compliance_status = "partial"
        else:
            compliance_status = "non-compliant"

        findings = self._build_findings(security, audit, cost)
        recommendations = self._build_recommendations(security, audit, cost)

        report = {
            "workflow_name": workflow_name,
            "report_type": report_type,
            "timestamp": now.isoformat(),
            "compliance_status": compliance_status,
            "report_metadata": {
                "generated_at": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "generator_version": "1.0",
                "report_type": report_type,
            },
            "compliance_score": {
                "overall_score": overall_score,
                "overall_level": overall_level,
                "component_scores": component_scores,
            },
            "security_validation": security_validation,
            "findings": findings,
            "recommendations": recommendations,
        }

        if report_type == "detailed":
            pii_count = self._count_pii_events()
            report["technical_details"] = {
                "platform": platform.system().lower(),
                "security_level": (
                    "kernel-hardened"
                    if security.get("syscall_filtering") and security.get("process_isolation")
                    else "user-space"
                ),
                "audit_events": audit.get("event_count", 0),
                "pii_detected": pii_count,
                "merkle_root": audit.get("merkle_root"),
                "merkle_verified": audit.get("integrity_verified", False),
                "budget_limit_usd": cost.get("budget_limit"),
            }

        return report

    def export_report(self, report: Dict[str, Any], format: str = "json",
                     output_file: Optional[str] = None) -> str:
        """
        Export a compliance report to a file.

        Args:
            report: Report data to export
            format: Export format (json, txt)
            output_file: Output filename (auto-generated if None)

        Returns:
            Path to the exported file
        """
        if output_file is None:
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = f"compliance_report_{report['workflow_name']}_{timestamp}.{format}"

        output_path = Path(output_file)

        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
        else:
            # Text format
            with open(output_path, 'w') as f:
                f.write(f"AKIOS Compliance Report\n")
                f.write(f"======================\n\n")
                f.write(f"Workflow: {report['workflow_name']}\n")
                f.write(f"Status: {report['compliance_status']}\n")
                f.write(f"Generated: {report['timestamp']}\n\n")

                f.write("Security Validation:\n")
                for key, value in report['security_validation'].items():
                    f.write(f"  - {key}: {'✓' if value else '✗'}\n")

        return str(output_path)


def get_compliance_generator() -> ComplianceGenerator:
    """
    Get a compliance generator instance.

    Returns:
        ComplianceGenerator instance
    """
    return ComplianceGenerator()
