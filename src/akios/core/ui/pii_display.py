"""
PII Detection Results Display - Rich-powered professional visualization

Provides professional, formatted display of PII (Personally Identifiable Information)
detection results for security scanning and compliance auditing.

Features:
  - Colored severity indicators (Green/Yellow/Red)
  - Professional tables for PII type summaries
  - Detailed discovery reports with line/position information
  - Progress tracking for large file analyses
  - Export-friendly formatting
  - Compliance report generation
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from .rich_output import print_panel, print_table, print_success, print_error, print_warning, print_info, get_theme_color


class PII_Severity(Enum):
    """Severity levels for PII detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PII_Type(Enum):
    """Types of PII that can be detected."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "social_security_number"
    CREDIT_CARD = "credit_card"
    ADDRESS = "address"
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport_number"
    IP_ADDRESS = "ip_address"
    API_KEY = "api_key"
    CUSTOM = "custom_pattern"


def get_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        "low": get_theme_color("success"),
        "medium": get_theme_color("warning"),
        "high": get_theme_color("error"),
        "critical": f"bold {get_theme_color('error')}"
    }
    return colors.get(severity.lower(), "white")


def get_severity_icon(severity: str) -> str:
    """Get icon for severity level."""
    icons = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🔴",
        "critical": "⛔"
    }
    return icons.get(severity.lower(), "•")


def display_pii_summary(
    file_path: str,
    pii_found: bool,
    pii_counts: Dict[str, int],
    severity_level: str = "unknown"
) -> None:
    """
    Display overall PII detection summary for a single file.
    
    Args:
        file_path: Path to the analyzed file
        pii_found: Whether PII was detected
        pii_counts: Dict of PII type -> count
        severity_level: Overall severity level
    """
    status_icon = "✓" if not pii_found else "⚠"
    status_color = get_theme_color("success") if not pii_found else get_severity_color(severity_level)
    
    if not pii_found:
        print_success(f"File '{file_path}' is clean - no PII detected")
    else:
        severity_icon = get_severity_icon(severity_level)
        print_warning(f"{severity_icon} File '{file_path}' contains {len(pii_counts)} PII type(s)")


def display_pii_candidates(
    candidates: List[Dict[str, Any]],
    file_path: Optional[str] = None
) -> None:
    """
    Display detailed list of PII candidates found.
    
    Args:
        candidates: List of PII candidates with position/context info
        file_path: Path to the analyzed file
    """
    if not candidates:
        print_info("No PII candidates detected")
        return
    
    # Prepare table data
    display_data = []
    for candidate in candidates:
        severity = candidate.get("severity", "unknown").lower()
        severity_icon = get_severity_icon(severity)
        
        display_data.append({
            "type": candidate.get("type", "unknown").capitalize(),
            "severity": f"{severity_icon} {severity.capitalize()}",
            "pattern": candidate.get("pattern", "N/A")[:30] + "..." if len(str(candidate.get("pattern", ""))) > 30 else candidate.get("pattern", "N/A"),
            "line": str(candidate.get("line", "?")),
            "confidence": f"{candidate.get('confidence', 0):.0%}"
        })
    
    title = f"📋 PII Candidates Found ({len(candidates)})"
    if file_path:
        title = f"📋 PII Candidates in {file_path} ({len(candidates)})"
    
    print_table(
        display_data,
        title=title,
        columns=["type", "severity", "pattern", "line", "confidence"]
    )


def display_pii_breakdown(
    pii_counts: Dict[str, int],
    total_candidates: int
) -> None:
    """
    Display breakdown of PII types detected.
    
    Args:
        pii_counts: Dict mapping PII type to count
        total_candidates: Total number of PII candidates found
    """
    if not pii_counts:
        return
    
    # Prepare breakdown data
    breakdown_data = [
        {
            "pii_type": pii_type.replace("_", " ").title(),
            "count": str(count),
            "percentage": f"{(count / total_candidates * 100):.1f}%" if total_candidates > 0 else "0%"
        }
        for pii_type, count in sorted(pii_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    print_table(
        breakdown_data,
        title="📊 PII Type Breakdown",
        columns=["pii_type", "count", "percentage"]
    )


def display_pii_report(
    scan_results: Dict[str, Any],
    detailed: bool = False
) -> None:
    """
    Display comprehensive PII scan report.
    
    Args:
        scan_results: Complete scan results with all detections
        detailed: Whether to show detailed information
    """
    # Extract summary information
    files_scanned = scan_results.get("files_scanned", 0)
    files_with_pii = scan_results.get("files_with_pii", 0)
    total_candidates = scan_results.get("total_candidates", 0)
    severity_level = scan_results.get("overall_severity", "unknown")
    
    # Display header
    pii_found = total_candidates > 0
    severity_icon = get_severity_icon(severity_level) if pii_found else "✓"
    status_text = f"[{get_theme_color('error')}]PII DETECTED[/{get_theme_color('error')}]" if pii_found else f"[{get_theme_color('success')}]CLEAN[/{get_theme_color('success')}]"
    
    report_title = f"🔍 PII Scan Report - {status_text}"
    report_content = f"Files Scanned: {files_scanned}\nFiles with PII: {files_with_pii}\nTotal Candidates: {total_candidates}\nSeverity: {severity_icon} {severity_level.upper()}"
    
    print_panel(report_title, report_content, style=f"bold {get_theme_color('error')}" if pii_found else f"bold {get_theme_color('success')}")
    
    # Display PII breakdown if found
    pii_counts = scan_results.get("pii_counts", {})
    if pii_counts:
        display_pii_breakdown(pii_counts, total_candidates)
    
    # Display detailed results if requested
    if detailed:
        file_results = scan_results.get("file_results", [])
        for file_result in file_results:
            if file_result.get("pii_found"):
                file_path = file_result.get("file_path", "unknown")
                candidates = file_result.get("candidates", [])
                print_panel(f"File: {file_path}", f"Candidates: {len(candidates)}")
                display_pii_candidates(candidates, file_path)


def display_scanning_progress(
    current_file: str,
    current_count: int,
    total_count: int
) -> None:
    """
    Display file scanning progress.
    
    Args:
        current_file: Currently scanning file
        current_count: Number of files processed
        total_count: Total files to process
    """
    percentage = (current_count / total_count * 100) if total_count > 0 else 0
    print_info(f"Scanning: {current_file} ({current_count}/{total_count}) [{percentage:.0f}%]")


def export_pii_report_csv(
    scan_results: Dict[str, Any],
    output_path: str
) -> bool:
    """
    Export PII detection results to CSV format.
    
    Args:
        scan_results: Complete scan results
        output_path: Path to write CSV file
    
    Returns:
        True if export successful
    """
    try:
        import csv
        
        file_results = scan_results.get("file_results", [])
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['file', 'pii_type', 'severity', 'confidence', 'line', 'pattern']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for file_result in file_results:
                file_path = file_result.get("file_path", "unknown")
                candidates = file_result.get("candidates", [])
                
                for candidate in candidates:
                    writer.writerow({
                        'file': file_path,
                        'pii_type': candidate.get('type', 'unknown'),
                        'severity': candidate.get('severity', 'unknown'),
                        'confidence': f"{candidate.get('confidence', 0):.2%}",
                        'line': candidate.get('line', '?'),
                        'pattern': candidate.get('pattern', '')[:50]
                    })
        
        print_success(f"Report exported to {output_path}")
        return True
    
    except Exception as e:
        print_error(f"Failed to export report: {e}")
        return False


def get_remediation_guidance(pii_types: List[str]) -> str:
    """
    Get guidance for remediating detected PII.
    
    Args:
        pii_types: List of PII types found
    
    Returns:
        Remediation guidance text
    """
    guidance = {
        "email": "Remove or mask email addresses using: name@***example.com",
        "phone": "Remove or mask phone numbers using: +1-***-***-1234",
        "social_security_number": "Remove all SSN references - never store in plaintext",
        "credit_card": "Remove or tokenize credit card numbers immediately",
        "address": "Remove or generalize address information (city/state only)",
        "name": "Anonymize personal names using pseudonyms or initials",
        "date_of_birth": "Remove DOB - use age or age ranges instead",
        "passport_number": "Remove passport numbers - not needed in files",
        "ip_address": "Mask IP addresses in logs (e.g., 192.168.*.*)‌",
        "api_key": "Rotate compromised API keys and use environment variables",
    }
    
    messages = []
    for pii_type in pii_types:
        key = pii_type.lower().replace(" ", "_")
        if key in guidance:
            messages.append(f"• {guidance[key]}")
    
    return "\n".join(messages) if messages else "Review detected PII and apply appropriate masking/removal"
