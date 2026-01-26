"""
Application constants for AKIOS V1.0

Fixed values that should not be user-configurable.
Separated from defaults.py for better organization.
"""

# Security violation error patterns for reliable detection in engine
SECURITY_VIOLATION_PATTERNS = {
    'quota', 'limit', 'security', 'not in allowed list', 'command blocked',
    'security violation',
    'access denied', 'permission denied', 'unauthorized'
}

# Workflow execution constants
DEFAULT_WORKFLOW_TIMEOUT = 1800.0  # 30 minutes in seconds
TEMPLATE_SUBSTITUTION_MAX_DEPTH = 10

# Token estimation fallbacks (characters per token)
ROUGH_TOKEN_ESTIMATION_RATIO = 4

# Audit event metadata keys
AUDIT_ERROR_CONTEXT_KEY = 'error_context'
AUDIT_EXECUTION_TIME_KEY = 'execution_time'
AUDIT_WORKFLOW_NAME_KEY = 'workflow_name'
AUDIT_STEP_ID_KEY = 'step_id'
