"""AKIOS UI module - Terminal output and visualization utilities."""

from .rich_output import (
    print_panel,
    print_table,
    print_code,
    print_success,
    print_warning,
    print_error,
    print_info,
    print_pii_findings,
    print_audit_log,
    progress_bar,
    clear_screen,
    is_rich_available,
    get_status_badge,
    print_budget_progress,
    print_cost_breakdown_table,
    print_spending_trend,
)

from .pii_display import (
    display_pii_summary,
    display_pii_candidates,
    display_pii_breakdown,
    display_pii_report,
    display_scanning_progress,
    export_pii_report_csv,
    get_remediation_guidance,
    PII_Severity,
    PII_Type,
)

__all__ = [
    # Rich output functions
    "print_panel",
    "print_table",
    "print_code",
    "print_success",
    "print_warning",
    "print_error",
    "print_info",
    "print_pii_findings",
    "print_audit_log",
    "progress_bar",
    "clear_screen",
    "is_rich_available",
    "get_status_badge",
    "print_budget_progress",
    "print_cost_breakdown_table",
    "print_spending_trend",
    
    # PII display functions
    "display_pii_summary",
    "display_pii_candidates",
    "display_pii_breakdown",
    "display_pii_report",
    "display_scanning_progress",
    "export_pii_report_csv",
    "get_remediation_guidance",
    "PII_Severity",
    "PII_Type",
]
