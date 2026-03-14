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
HTML Security Posture Report Generator for AKIOS.

Generates a self-contained HTML report from workflow execution results
and security posture data. Used by `akios run --report`.

This is a key feature for compliance reporting and security posture visibility.
"""

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _score_color(score: float) -> str:
    """Return CSS color for a compliance score."""
    if score >= 4.5:
        return "#22c55e"  # green
    elif score >= 3.5:
        return "#3b82f6"  # blue
    elif score >= 2.5:
        return "#f59e0b"  # amber
    else:
        return "#ef4444"  # red


def _status_badge(status: str) -> str:
    """Return HTML badge for compliance status."""
    colors = {
        "compliant": ("#22c55e", "#f0fdf4"),
        "partial": ("#f59e0b", "#fffbeb"),
        "non-compliant": ("#ef4444", "#fef2f2"),
        "unknown": ("#6b7280", "#f9fafb"),
    }
    fg, bg = colors.get(status, colors["unknown"])
    return (
        f'<span style="background:{bg};color:{fg};padding:4px 12px;'
        f'border-radius:9999px;font-weight:600;font-size:0.875rem;'
        f'border:1px solid {fg}30">{html.escape(status.upper())}</span>'
    )


def _check_icon(val: bool) -> str:
    """Return check/cross icon."""
    if val:
        return '<span style="color:#22c55e;font-size:1.1rem">✓</span>'
    return '<span style="color:#ef4444;font-size:1.1rem">✗</span>'


def _score_bar(score: float, max_score: float = 5.0) -> str:
    """Return HTML progress bar for a score."""
    pct = min((score / max_score) * 100, 100)
    color = _score_color(score)
    return (
        f'<div style="background:#e5e7eb;border-radius:6px;height:10px;width:100%;overflow:hidden">'
        f'<div style="background:{color};height:100%;width:{pct:.0f}%;border-radius:6px;'
        f'transition:width 0.3s"></div></div>'
    )


def generate_html_report(
    report_data: Dict[str, Any],
    execution_result: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a self-contained HTML security posture report.

    Args:
        report_data: Compliance report dict from ComplianceGenerator.generate_report()
        execution_result: Optional workflow execution result dict

    Returns:
        Complete HTML string (self-contained, no external dependencies)
    """
    now = datetime.now(tz=timezone.utc)
    workflow_name = html.escape(report_data.get("workflow_name", "Unknown"))
    compliance_status = report_data.get("compliance_status", "unknown")
    scores = report_data.get("compliance_score", {})
    overall_score = scores.get("overall_score", 0)
    overall_level = scores.get("overall_level", "unknown")
    component_scores = scores.get("component_scores", {})
    security_validation = report_data.get("security_validation", {})
    findings = report_data.get("findings", [])
    recommendations = report_data.get("recommendations", [])
    technical = report_data.get("technical_details", {})

    # Execution metrics
    exec_steps = ""
    exec_time = ""
    exec_tokens = ""
    exec_cost = ""
    exec_pii = ""
    if execution_result:
        exec_steps = str(execution_result.get("steps_executed", "—"))
        t = execution_result.get("execution_time", 0)
        exec_time = f"{t:.2f}s" if t else "—"
        ti = execution_result.get("tokens_input", 0)
        to = execution_result.get("tokens_output", 0)
        exec_tokens = f"{ti + to:,}" if (ti or to) else "—"
        c = execution_result.get("total_cost", 0)
        exec_cost = f"${c:.4f}" if c else "$0.0000"
        pii_count = execution_result.get("pii_redaction_count", 0)
        exec_pii = str(pii_count) if pii_count else "0"

    # Build findings HTML
    findings_html = ""
    if findings:
        for f in findings:
            findings_html += f'<li style="margin-bottom:6px;color:#374151">{html.escape(f)}</li>\n'
    else:
        findings_html = '<li style="color:#22c55e">No issues found — all checks passed</li>'

    # Build recommendations HTML
    recs_html = ""
    if recommendations:
        for r in recommendations:
            recs_html += f'<li style="margin-bottom:6px;color:#374151">{html.escape(r)}</li>\n'
    else:
        recs_html = '<li style="color:#22c55e">No recommendations — security posture is strong</li>'

    # Build security checks table
    sec_checks = ""
    check_labels = {
        "pii_redaction": "PII Redaction",
        "audit_logging": "Audit Logging",
        "syscall_filtering": "Syscall Filtering",
        "process_isolation": "Process Isolation",
    }
    for key, label in check_labels.items():
        val = security_validation.get(key, False)
        sec_checks += (
            f'<tr><td style="padding:8px 12px;border-bottom:1px solid #e5e7eb">{label}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center">'
            f'{_check_icon(val)}</td></tr>\n'
        )

    # Build component scores
    comp_html = ""
    comp_labels = {"security": "Security", "audit": "Audit", "cost": "Cost Control"}
    comp_weights = {"security": "50%", "audit": "30%", "cost": "20%"}
    for key, label in comp_labels.items():
        s = component_scores.get(key, 0)
        comp_html += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;font-weight:500">{label}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center;color:#6b7280;font-size:0.85rem">{comp_weights[key]}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;width:50%">{_score_bar(s)}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600;color:{_score_color(s)}">{s:.1f}/5.0</td>
        </tr>
        """

    # Technical details section
    tech_html = ""
    if technical:
        tech_html = f"""
        <div style="margin-top:32px">
            <h2 style="font-size:1.25rem;font-weight:600;color:#1f2937;margin-bottom:16px;border-bottom:2px solid #e5e7eb;padding-bottom:8px">
                🔍 Technical Details
            </h2>
            <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
                <tr><td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280">Platform</td>
                    <td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;font-family:monospace">{html.escape(str(technical.get("platform", "—")))}</td></tr>
                <tr><td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280">Security Level</td>
                    <td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;font-family:monospace">{html.escape(str(technical.get("security_level", "—")))}</td></tr>
                <tr><td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280">Audit Events</td>
                    <td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;font-family:monospace">{technical.get("audit_events", 0):,}</td></tr>
                <tr><td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280">PII Detections</td>
                    <td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;font-family:monospace">{technical.get("pii_detected", 0):,}</td></tr>
                <tr><td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280">Merkle Root</td>
                    <td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;font-family:monospace;font-size:0.75rem;word-break:break-all">{html.escape(str(technical.get("merkle_root", "—")))}</td></tr>
                <tr><td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280">Merkle Verified</td>
                    <td style="padding:6px 12px;border-bottom:1px solid #f3f4f6">{_check_icon(technical.get("merkle_verified", False))}</td></tr>
                <tr><td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280">Budget Limit</td>
                    <td style="padding:6px 12px;border-bottom:1px solid #f3f4f6;font-family:monospace">${technical.get("budget_limit_usd", 0) or 0:.2f}</td></tr>
            </table>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AKIOS Security Posture Report — {workflow_name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f9fafb; color: #1f2937; line-height: 1.6; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 32px 24px; }}
  .header {{ background: linear-gradient(135deg, #020f32 0%, #0a2463 100%);
             color: white; padding: 32px; border-radius: 12px; margin-bottom: 24px; }}
  .header h1 {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 4px; }}
  .header p {{ opacity: 0.8; font-size: 0.9rem; }}
  .card {{ background: white; border-radius: 12px; padding: 24px;
           margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .score-ring {{ width: 120px; height: 120px; border-radius: 50%;
                 display: flex; align-items: center; justify-content: center;
                 font-size: 2rem; font-weight: 700; margin: 0 auto 12px;
                 border: 6px solid {_score_color(overall_score)}; }}
  .metric {{ text-align: center; }}
  .metric-value {{ font-size: 1.5rem; font-weight: 700; color: #1f2937; }}
  .metric-label {{ font-size: 0.8rem; color: #6b7280; margin-top: 2px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
  @media (max-width: 640px) {{ .grid-4 {{ grid-template-columns: repeat(2, 1fr); }} }}
  .footer {{ text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 32px; padding-top: 16px;
             border-top: 1px solid #e5e7eb; }}
  @media print {{
    body {{ background: white; }}
    .card {{ box-shadow: none; border: 1px solid #e5e7eb; }}
  }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <h1>🔒 AKIOS Security Posture Report</h1>
    <p>Workflow: <strong>{workflow_name}</strong> · Generated: {now.strftime("%Y-%m-%d %H:%M UTC")}</p>
  </div>

  <!-- Overall Score -->
  <div class="card" style="text-align:center">
    <div class="score-ring" style="color:{_score_color(overall_score)}">
      {overall_score:.1f}
    </div>
    <div style="margin-bottom:8px">{_status_badge(compliance_status)}</div>
    <p style="color:#6b7280;font-size:0.9rem">Overall Posture: <strong>{html.escape(overall_level.title())}</strong> · Score out of 5.0</p>
  </div>

  <!-- Execution Metrics -->
  {"" if not execution_result else f'''
  <div class="card">
    <h2 style="font-size:1.1rem;font-weight:600;margin-bottom:16px;color:#1f2937">⚡ Execution Summary</h2>
    <div class="grid-4">
      <div class="metric"><div class="metric-value">{exec_steps}</div><div class="metric-label">Steps</div></div>
      <div class="metric"><div class="metric-value">{exec_time}</div><div class="metric-label">Duration</div></div>
      <div class="metric"><div class="metric-value">{exec_tokens}</div><div class="metric-label">Tokens</div></div>
      <div class="metric"><div class="metric-value">{exec_cost}</div><div class="metric-label">Cost</div></div>
    </div>
    <div style="margin-top:12px;text-align:center;color:#6b7280;font-size:0.85rem">
      PII redactions applied: <strong>{exec_pii}</strong>
    </div>
  </div>
  '''}

  <!-- Component Scores -->
  <div class="card">
    <h2 style="font-size:1.1rem;font-weight:600;margin-bottom:16px;color:#1f2937">📊 Component Scores</h2>
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="border-bottom:2px solid #e5e7eb">
          <th style="padding:8px 12px;text-align:left;font-size:0.85rem;color:#6b7280">Component</th>
          <th style="padding:8px 12px;text-align:center;font-size:0.85rem;color:#6b7280">Weight</th>
          <th style="padding:8px 12px;text-align:left;font-size:0.85rem;color:#6b7280">Score</th>
          <th style="padding:8px 12px;text-align:right;font-size:0.85rem;color:#6b7280">Value</th>
        </tr>
      </thead>
      <tbody>
        {comp_html}
      </tbody>
    </table>
  </div>

  <!-- Security Checks -->
  <div class="card">
    <h2 style="font-size:1.1rem;font-weight:600;margin-bottom:16px;color:#1f2937">🛡️ Security Checks</h2>
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="border-bottom:2px solid #e5e7eb">
          <th style="padding:8px 12px;text-align:left;font-size:0.85rem;color:#6b7280">Check</th>
          <th style="padding:8px 12px;text-align:center;font-size:0.85rem;color:#6b7280">Status</th>
        </tr>
      </thead>
      <tbody>
        {sec_checks}
      </tbody>
    </table>
  </div>

  <!-- Findings -->
  <div class="card">
    <h2 style="font-size:1.1rem;font-weight:600;margin-bottom:16px;color:#1f2937">🔎 Findings</h2>
    <ul style="list-style:disc;padding-left:20px">
      {findings_html}
    </ul>
  </div>

  <!-- Recommendations -->
  <div class="card">
    <h2 style="font-size:1.1rem;font-weight:600;margin-bottom:16px;color:#1f2937">💡 Recommendations</h2>
    <ul style="list-style:disc;padding-left:20px">
      {recs_html}
    </ul>
  </div>

  {tech_html}

  <!-- Footer -->
  <div class="footer">
    <p>Generated by <strong>AKIOS v1.5.0</strong> — Security-cage runtime for AI agents</p>
    <p style="margin-top:4px">
      <a href="https://github.com/akios-ai/akios" style="color:#3b82f6;text-decoration:none">GitHub</a> ·
      <a href="https://pypi.org/project/akios/" style="color:#3b82f6;text-decoration:none">PyPI</a> ·
      GPL-3.0-only
    </p>
  </div>

</div>
</body>
</html>"""


def save_html_report(
    report_data: Dict[str, Any],
    output_dir: str,
    execution_result: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate and save HTML report to the output directory.

    Args:
        report_data: Compliance report data
        output_dir: Directory to save the report
        execution_result: Optional workflow execution result

    Returns:
        Path to the saved HTML report
    """
    html_content = generate_html_report(report_data, execution_result)
    output_path = Path(output_dir) / "security_posture_report.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return str(output_path)
