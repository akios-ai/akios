"""
JSON audit export with Merkle root and full trace.

Generates human-readable JSON exports including integrity verification.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from ..ledger import get_ledger, get_merkle_root


def export_audit_json(output_file: Optional[str] = None, include_sensitive: bool = False) -> Dict[str, Any]:
    """
    Export complete audit trail as JSON with access controls.

    SECURITY NOTE: Audit exports may contain sensitive information.
    Use include_sensitive=False for production exports.

    Args:
        output_file: Optional output file path
        include_sensitive: Whether to include potentially sensitive metadata

    Returns:
        Dict containing the exported audit data
    """
    try:
        from akios.config import get_settings
    except ImportError:
        # Fallback for Docker environment
        import sys
        sys.path.insert(0, '/app')
        from akios.config import get_settings

    # Security check: Only allow exports in development or with explicit permission
    settings = get_settings()
    if not settings.audit_export_enabled and not include_sensitive:
        raise PermissionError(
            "Audit export is disabled. Set audit_export_enabled: true in config.yaml, "
            "or use include_sensitive=True for development only."
        )

    # Additional security: check if audit is enabled at all
    if not settings.audit_enabled:
        raise PermissionError("Audit system is disabled. Cannot export audit data.")

    ledger = get_ledger()

    # CRITICAL: Load all events from disk into memory for export
    # Lazy loading means events aren't loaded until explicitly requested
    ledger._load_all_events()

    def sanitize_event(event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive information from audit events"""
        if include_sensitive:
            return event_dict

        # Apply comprehensive PII redaction (optional)
        try:
            from ...security.pii import apply_pii_redaction
            pii_available = True
        except ImportError:
            pii_available = False

        sanitized = event_dict.copy()

        # Redact PII in all text fields that might contain sensitive data
        text_fields = ['workflow_id', 'agent', 'action', 'result']
        for field in text_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                if pii_available:
                    sanitized[field] = apply_pii_redaction(sanitized[field])
                # If PII redaction not available, leave as-is

        # Redact PII in metadata comprehensively
        if 'metadata' in sanitized and pii_available:
            metadata = sanitized['metadata'].copy()
            # Apply PII redaction to all string values in metadata recursively
            def redact_recursive(obj):
                if isinstance(obj, str):
                    return apply_pii_redaction(obj)
                elif isinstance(obj, dict):
                    return {k: redact_recursive(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [redact_recursive(item) for item in obj]
                else:
                    return obj

            sanitized['metadata'] = redact_recursive(metadata)

        return sanitized

    export_data = {
        'total_events': len(ledger.events),
        'merkle_root': get_merkle_root(),
        'export_timestamp': ledger.events[-1].timestamp if ledger.events else None,
        'export_security_level': 'full' if include_sensitive else 'sanitized',
        'events': [sanitize_event(event.to_dict()) for event in ledger.events]
    }

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        export_data['output_file'] = str(output_path)

    return export_data