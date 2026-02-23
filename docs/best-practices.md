# Best Practices Guide
**Document Version:** 1.0.15  
**Date:** 2026-02-23  

**Optimize AKIOS workflows for performance, security, and maintainability**

This guide covers recommended practices for building robust, efficient, and secure AKIOS workflows.

## Project Organization

### Directory Structure

```bash
my-akios-project/
├── data/
│   ├── input/           # Input files and data
│   │   ├── documents/   # Document files
│   │   ├── api/         # API response data
│   │   └── raw/         # Raw input data
│   ├── output/          # Workflow outputs
│   │   ├── reports/     # Generated reports
│   │   ├── processed/   # Processed data
│   │   └── run_YYYY-MM-DD_HH-MM-SS/  # One folder per run
│   └── audit/           # Audit logs
├── workflows/           # Custom workflow definitions
│   ├── production/      # Production workflows
│   ├── development/     # Development workflows
│   └── templates/       # Reusable workflow components
├── config.yaml          # Configuration file
├── .env                 # Environment variables (gitignored)
└── scripts/             # Automation scripts
    ├── deploy.sh        # Deployment scripts
    ├── backup.sh        # Backup scripts
    └── monitor.sh       # Monitoring scripts
```

### File Naming Conventions

```bash
# Workflows
document_processing.yml
api_data_sync.yml
batch_analysis.yml

# Data files
customer_data_2026-01-15.json
monthly_report_january.pdf
processed_batch_001.txt

# Scripts
deploy_production.sh
backup_audit_logs.sh
health_check.sh
```

## Configuration Management

### Environment Separation

```bash
# .env.development
AKIOS_MOCK_LLM=true
AKIOS_NETWORK_ACCESS=true
AKIOS_LLM_PROVIDER=grok

# .env.production
AKIOS_MOCK_LLM=false
AKIOS_NETWORK_ACCESS=true
AKIOS_LLM_PROVIDER=grok
GROK_API_KEY=your-production-key
```

### Configuration Templates

```yaml
# config.yaml.template
mock_llm: ${AKIOS_MOCK_LLM:-true}
audit_export_format: "json"

agents:
  filesystem:
    allowed_paths:
      - "./data/input"
      - "./data/output"
      - "./workflows"

  http:
    network_access_allowed: ${AKIOS_NETWORK_ACCESS:-false}
    timeout: 30
    allowed_domains:             # Restrict HTTP agent to specific domains
      - api.example.com

  llm:
    provider: ${AKIOS_LLM_PROVIDER:-grok}
    max_tokens_per_call: 1000
    cost_limit_per_run: 1.0
```

## Workflow Design

### Modular Workflow Design

Break complex workflows into smaller, reusable components:

```yaml
# _common_steps.yml (shared components)
_common_extract_data:
  agent: "filesystem"
  action: "read"
  config:
    allowed_paths: ["./data/input"]
  parameters:
    path: "./data/input/source_data.json"

_common_validate_data:
  agent: "llm"
  action: "complete"
  config: {}
  parameters:
    prompt: |
      Validate this data structure and format.
      Return validation results as JSON.

      Data: {{_common_extract_data.content}}
```

```yaml
# main workflow using anchors
name: "Data Processing Pipeline"
description: "Complete data processing with validation"

steps:
  - step: "extract"
    <<: *_common_extract_data

  - step: "validate"
    <<: *_common_validate_data

  - step: "process"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Process validated data: {{validate.content}}
```

### Error Handling Patterns

```yaml
name: "Robust Data Processing"
description: "Handle errors gracefully"

steps:
  - step: "safe_read"
    agent: "filesystem"
    action: "read"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/data.json"

  - step: "validate_input"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Validate JSON structure: {{safe_read.content}}
        Return {"valid": true/false, "errors": [...]}

  - step: "process_valid_data"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: "Process: {{safe_read.content}}"
      skip_if: "{{validate_input.content.valid != true}}"

  - step: "handle_errors"
    agent: "filesystem"
    action: "write"
    config:
      allowed_paths: ["./data/output"]
    parameters:
      path: "./data/output/errors.json"
      content: "{{validate_input.content}}"
      skip_if: "{{validate_input.content.valid == true}}"
```

## Security Best Practices

### Principle of Least Privilege

```yaml
# Restrict filesystem access
agents:
  filesystem:
    allowed_paths:
      - "./data/input"      # Read-only input
      - "./data/output"     # Write-only output
      # Never allow: "./config", "./.env", "/etc"
```

### API Key Management

```bash
# Use different keys for different environments
# Never commit keys to version control
# Rotate keys regularly
# Use key management services when possible

# .env (add to .gitignore)
GROK_API_KEY=sk-prod-123456789
OPENAI_API_KEY=sk-prod-987654321
```

### Prompt Safety

Always preview prompts before sending to LLM providers, especially when templates include file content or user data:

```bash
# Preview the interpolated + PII-redacted prompt the LLM will receive
akios protect show-prompt workflow.yml

# Verify no sensitive data leaks (SSN, NPI, DEA, medical records, etc.)
akios protect scan data/input/document.txt
```

**Why:** Prompts may inadvertently include PII from interpolated file contents. `show-prompt` reveals the exact redacted text sent to the LLM, catching leaks before they happen.

### HTTP Domain Whitelisting

When workflows use the HTTP agent, restrict outbound requests to known domains:

```yaml
# config.yaml or akios.yml
allowed_domains:
  - api.example.com
  - data.provider.com
```

```bash
# Or via environment variable
export AKIOS_ALLOWED_DOMAINS="api.example.com,data.provider.com"

# Use the standalone HTTP command for quick API checks
akios http GET https://api.example.com/health
```

**Why:** Prevents workflows from exfiltrating data to unauthorized endpoints. LLM provider APIs always bypass the whitelist.

### Shell Injection Prevention

AKIOS blocks the hidden `--exec` flag to prevent shell-injection attacks. Never pass unsanitized user input as command arguments in tool_executor workflows.

### Input Validation

```yaml
name: "Secure Data Processing"
description: "Validate all inputs before processing"

steps:
  - step: "validate_path"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "test"
      args: ["-f", "./data/input/{{input_file}}"]

  - step: "check_file_size"
    agent: "filesystem"
    action: "stat"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/{{input_file}}"
      skip_if: "{{validate_path.returncode != 0}}"

  - step: "validate_content"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Validate file content for security issues.
        Check for: malicious code, oversized content, invalid format

        File: {{read_file.content}}
        Size: {{check_file_size.size}} bytes
```

## Performance Optimization

### Caching Strategies

```yaml
# Cache expensive operations
name: "Optimized Document Processing"
description: "Use caching for better performance"

steps:
  - step: "read_document"
    agent: "filesystem"
    action: "read"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/document.pdf"

  - step: "analyze_content"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: "Analyze: {{read_document.content}}"
```

### Batch Processing

```yaml
name: "Batch File Processing"
description: "Process multiple files efficiently"

steps:
  - step: "list_files"
    agent: "filesystem"
    action: "list"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input"
      pattern: "*.pdf"

  - step: "batch_process"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "parallel"
      args: [
        "--no-notice",
        "--max-procs", "2",  # Limit concurrency
        "./akios run document_processor.yml --input-file {} ::: {{list_files.files}}"
      ]
```

### Memory Management

```yaml
name: "Memory-Efficient Processing"
description: "Handle large files without memory issues"

steps:
  - step: "check_file_size"
    agent: "filesystem"
    action: "stat"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/large_file.pdf"

  - step: "conditional_processing"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        {% if check_file_size.size > 10000000 %}
          This is a large file ({{check_file_size.size}} bytes).
          Provide a summary only to avoid memory issues.
        {% else %}
          Provide detailed analysis.
        {% endif %}

        File size: {{check_file_size.size}}
        Content: {{read_file.content}}
```

## Monitoring and Observability

### Budget Monitoring

Monitor your workflow costs and budget consumption to avoid unexpected charges:

```bash
# View budget dashboard with cost breakdown and kill-switch status
akios status --budget

# Export budget data as JSON for automation/alerting
akios status --budget --json
```

Set appropriate `budget_limit_per_run` values in `config.yaml` (default: $1.00). AKIOS automatically terminates workflows that exceed the budget via kill-switches.

### Health Checks

```yaml
name: "System Health Monitoring"
description: "Monitor system and API health"

steps:
  - step: "check_api_health"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.x.ai/health"
      timeout: 10

  - step: "check_disk_space"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "df"
      args: ["/data"]

  - step: "send_alert"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://alerts.company.com/webhook"
      json:
        service: "akios"
        status: "unhealthy"
        api_health: "{{check_api_health.status_code}}"
        disk_usage: "{{check_disk_space.stdout}}"
      skip_if: "{{check_api_health.status_code == 200}}"
```

### Performance Monitoring

```python
# performance_monitor.py
from akios.core.performance.monitor import get_performance_monitor, measure_performance

monitor = get_performance_monitor()

@measure_performance("workflow_execution")
def run_workflow(workflow_path):
    # Workflow execution code
    pass

# Get performance report
report = monitor.get_performance_report()
if report['memory_usage']['percentage'] > 80:
    print("Warning: High memory usage")
```

### Audit Trail Management

```bash
# Regular audit maintenance
#!/bin/bash

# Export weekly audit summary
./akios audit export --since "7 days ago" --format json --output weekly_audit.json

# Archive old audit logs
./akios audit archive --older-than 90d --compress

# Verify audit integrity
if ./akios audit verify; then
    echo "Audit integrity OK"
else
    echo "Audit integrity compromised!"
    exit 1
fi
```

## Testing Strategies

### Unit Testing

```python
# test_workflow.py
import pytest
from akios.core.runtime.workflow.parser import parse_workflow_string

def test_workflow_parsing():
    yaml_content = """
    name: "Test Workflow"
    steps:
      - step: "test"
        agent: "filesystem"
        action: "read"
        config: {}
        parameters:
          path: "./test.txt"
    """

    workflow = parse_workflow_string(yaml_content)
    assert workflow.name == "Test Workflow"
    assert len(workflow.steps) == 1

def test_error_handling():
    # Test invalid workflow
    with pytest.raises(ValueError):
        parse_workflow_string("invalid: yaml: content:")
```

### Integration Testing

```bash
# test_integration.sh
#!/bin/bash

# Test with mock data
export AKIOS_MOCK_LLM=true

# Run test workflows
./akios run test_workflow.yml --verbose

# Verify outputs
if [ ! -f "data/output/test_result.txt" ]; then
    echo "Test failed: Output file not created"
    exit 1
fi

# Check audit logs
if ! ./akios audit verify; then
    echo "Test failed: Audit integrity compromised"
    exit 1
fi

echo "All integration tests passed"
```

### Mock Data Testing

```yaml
# test_data_generator.yml
name: "Generate Test Data"
description: "Create mock data for testing"

steps:
  - step: "generate_mock_data"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Generate realistic test data as JSON:
        - 10 customer records
        - Various data types
        - Include edge cases

  - step: "save_test_data"
    agent: "filesystem"
    action: "write"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/mock_customers.json"
      content: "{{generate_mock_data.content}}"
```

## Deployment Practices

### Environment Configuration

```bash
# deploy.sh
#!/bin/bash

# Load environment-specific configuration
if [ "$ENVIRONMENT" = "production" ]; then
    cp .env.production .env
else
    cp .env.development .env
fi

# Validate configuration
if ! ./akios config validate; then
    echo "Configuration validation failed"
    exit 1
fi

# Run health checks
if ! ./akios status | grep -q "healthy"; then
    echo "System health check failed"
    exit 1
fi

# Deploy
echo "Deployment completed successfully"
```

### Backup and Recovery

```bash
# backup.sh
#!/bin/bash

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configurations
cp config.yaml .env "$BACKUP_DIR/"

# Backup data (excluding cache)
rsync -a --exclude="cache/" data/ "$BACKUP_DIR/data/"

# Backup audit logs
./akios audit export --format json --output "$BACKUP_DIR/audit_backup.json"

# Compress backup
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup created: ${BACKUP_DIR}.tar.gz"
```

### Rollback Strategy

```bash
# rollback.sh
#!/bin/bash

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop current workflows
pkill -f akios

# Restore from backup
tar -xzf "$BACKUP_FILE" -C /

# Validate restored configuration
if ./akios config validate; then
    echo "Rollback completed successfully"
else
    echo "Rollback failed - configuration invalid"
    exit 1
fi
```

## Maintenance Tasks

### Regular Maintenance Schedule

```bash
# cron jobs for maintenance
# Add to crontab: crontab -e

# Daily: Clean old cache files
0 2 * * * cd /path/to/akios && ./akios clean cache --older-than 7d

# Weekly: Archive audit logs
0 3 * * 1 cd /path/to/akios && ./akios audit archive --older-than 30d

# Monthly: Full system backup
0 4 1 * * cd /path/to/akios && ./scripts/backup.sh

# Monthly: Security audit
0 5 1 * * cd /path/to/akios && ./akios audit verify && ./akios security audit
```

### Log Rotation

```yaml
# logrotate configuration
# /etc/logrotate.d/akios
/path/to/akios/data/audit/audit_events.jsonl {
    weekly
    rotate 52
    compress
    delaycompress
    missingok
    notifempty
    create 644 akios akios
    postrotate
        /path/to/akios/akios audit verify
    endscript
}
```

## Compliance and Governance

### Data Retention Policies

```yaml
name: "Data Retention Enforcement"
description: "Automatically clean up old data"

steps:
  - step: "find_old_files"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "find"
      args: ["./data/output", "-name", "*.txt", "-mtime", "+90"]

  - step: "archive_old_data"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "tar"
      args: ["-czf", "archive_$(date +%Y%m%d).tar.gz", "{{find_old_files.stdout}}"]

  - step: "cleanup_archived"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "rm"
      args: ["{{find_old_files.stdout}}"]
```

### Access Control

```yaml
# Role-based access control
name: "Access Control Validation"
description: "Validate user permissions"

steps:
  - step: "check_user_role"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://auth.company.com/user/{{current_user}}/role"

  - step: "validate_permissions"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Validate if user {{current_user}} with role {{check_user_role.content}}
        has permission to run workflow: {{workflow_name}}

        Return: {"authorized": true/false, "reason": "explanation"}

  - step: "log_access_attempt"
    agent: "filesystem"
    action: "write"
    config:
      allowed_paths: ["./data/audit"]
    parameters:
      path: "./data/audit/access_log.json"
      content: |
        {
          "user": "{{current_user}}",
          "workflow": "{{workflow_name}}",
          "authorized": "{{validate_permissions.content.authorized}}",
          "timestamp": "{{timestamp}}"
        }
```

## Summary

Following these best practices will help you build:

- **Secure**: Principle of least privilege, input validation, audit trails
- **Performant**: Caching, batch processing, memory management
- **Maintainable**: Modular design, testing, documentation
- **Reliable**: Error handling, monitoring, backup strategies
- **Compliant**: Access control, data retention, audit capabilities

Remember: Security is not optional in AKIOS V1.0. Always prioritize security controls while optimizing for performance and usability.
