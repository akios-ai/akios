# Developer API Reference
**Document Version:** 1.0  
**Date:** 2026-01-25  

**Programmatic integration with AKIOS workflows**

This reference covers the Python API for integrating AKIOS into your applications, scripts, and automated systems.

## Installation

```bash
# Install AKIOS
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

# Or for development
pip install -e .
```

## Core Classes

### RuntimeEngine

Main class for executing workflows programmatically.

```python
from akios.core.runtime.engine import RuntimeEngine

# Initialize engine
engine = RuntimeEngine()

# Execute workflow
result = engine.run("path/to/workflow.yml")

# Check execution status
if result["status"] == "completed":
    print(f"Workflow completed in {result['execution_time']:.2f}s")
    print(f"Output: {result['output_directory']}")
```

#### Methods

**`__init__(workflow=None)`**
- Initialize runtime engine
- `workflow`: Optional pre-loaded workflow object

**`run(workflow_path_or_workflow=None, context=None)`**
- Execute a workflow
- `workflow_path_or_workflow`: Path to YAML file or workflow dict
- `context`: Optional execution context variables
- Returns: Execution result dictionary


## Agents

### Filesystem Agent

Secure file operations with path restrictions.

```python
from akios.core.runtime.agents.filesystem import FilesystemAgent

agent = FilesystemAgent({
    "allowed_paths": ["./data/input", "./data/output"]
})

# Read file
result = agent.read("./data/input/document.txt")
print(f"Content: {result['content']}")
print(f"Size: {result['size']} bytes")

# Write file
agent.write("./data/output/result.txt", "Analysis complete")

# List directory
files = agent.list("./data/input")
print(f"Files: {files['files']}")

# Get file info
info = agent.stat("./data/input/document.txt")
print(f"Modified: {info['modified']}")
```

#### Methods

**`read(path, encoding='utf-8')`**
- Read file contents
- Returns: Dict with content, size, encoding, file_type

**`write(path, content, encoding='utf-8', mode='w')`**
- Write content to file
- Modes: 'w' (write), 'a' (append)

**`list(path, pattern=None)`**
- List directory contents
- `pattern`: Optional glob pattern
- Returns: Dict with files and directories arrays

**`stat(path)`**
- Get file/directory metadata
- Returns: Dict with size, modified, permissions, is_file, is_directory

**`exists(path)`**
- Check if path exists
- Returns: Dict with exists, is_file, is_directory

### HTTP Agent

Secure HTTP requests with domain whitelisting and automatic PII redaction. Outbound requests are restricted to configured `allowed_domains`; LLM provider APIs bypass the whitelist. Also available as a standalone CLI command: `akios http <METHOD> <URL>`.

```python
from akios.core.runtime.agents.http import HttpAgent

agent = HttpAgent()

# GET request
response = agent.get(
    "https://api.example.com/data",
    headers={"Authorization": "Bearer token"},
    params={"limit": 10}
)

if response["status_code"] == 200:
    data = response["json"]  # Parsed JSON
    print(f"Data: {data}")

# POST request
result = agent.post(
    "https://api.example.com/submit",
    json={"name": "John", "data": "value"}
)

# PUT request
agent.put("https://api.example.com/item/123", json={"status": "updated"})

# DELETE request
agent.delete("https://api.example.com/item/123")
```

#### Methods

**`get(url, headers=None, params=None, timeout=30, allow_redirects=True)`**
- HTTP GET request

**`post(url, headers=None, data=None, json=None, timeout=30)`**
- HTTP POST request

**`put(url, headers=None, data=None, json=None, timeout=30)`**
- HTTP PUT request

**`delete(url, headers=None, timeout=30)`**
- HTTP DELETE request

All methods return: Dict with status_code, headers, content, json (if applicable)

### LLM Agent

AI language model integration with cost tracking.

```python
from akios.core.runtime.agents.llm import LlmAgent

agent = LlmAgent()

# Text completion
result = agent.complete(
    prompt="Analyze this document: {{document_content}}",
    model="grok-3",
    max_tokens=500,
    temperature=0.7
)

print(f"Response: {result['content']}")
print(f"Tokens used: {result['usage']['total_tokens']}")
print(f"Cost: ${result['cost']:.4f}")

# Chat completion
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
]

chat_result = agent.chat(
    messages=messages,
    model="grok-3",
    max_tokens=200
)
```

#### Methods

**`complete(prompt, model='gpt-3.5-turbo', max_tokens=1000, temperature=0.7, ...)`**
- Generate text completion
- Returns: Dict with content, usage, cost, model, finish_reason

**`chat(messages, model='gpt-3.5-turbo', max_tokens=1000, ...)`**
- Have conversation with context
- Returns: Same as complete()

### Tool Executor Agent

Run external commands in sandboxed environment.

```python
from akios.core.runtime.agents.tool_executor import ToolExecutorAgent

agent = ToolExecutorAgent()

# Execute command
result = agent.run(
    command="ls",
    args=["-la", "/tmp"],
    timeout=10,
    env={"CUSTOM_VAR": "value"}
)

if result["returncode"] == 0:
    print(f"Output: {result['stdout']}")
else:
    print(f"Error: {result['stderr']}")

# Execute with working directory
result = agent.run(
    command="python",
    args=["script.py"],
    working_dir="/path/to/scripts",
    timeout=30
)
```

#### Methods

**`run(command, args=None, timeout=30, env=None, working_dir=None)`**
- Execute external command
- Returns: Dict with stdout, stderr, returncode, duration

## Configuration

### Settings Management

```python
from akios.config import get_settings, Settings

# Get current settings
settings = get_settings()
print(f"Audit path: {settings.audit_storage_path}")
print(f"Mock mode: {settings.mock_llm}")

# Access settings (flat structure)
print(f"Sandbox enabled: {settings.sandbox_enabled}")
print(f"Network access: {settings.network_access_allowed}")
print(f"Max tokens: {settings.max_tokens_per_call}")
print(f"PII redaction: {settings.pii_redaction_enabled}")

# Create custom settings (for testing)
custom_settings = Settings(
    mock_llm=True,
    audit_storage_path="./custom_audit"
)
```

### Environment Variables

```python
# LLM Configuration
os.environ["AKIOS_LLM_PROVIDER"] = "grok"  # openai, anthropic, grok
os.environ["AKIOS_LLM_MODEL"] = "grok-3"
os.environ["GROK_API_KEY"] = "your-key-here"

# Security Settings
os.environ["AKIOS_MOCK_LLM"] = "false"  # true/false
os.environ["AKIOS_NETWORK_ACCESS"] = "true"  # true/false

# Path Configuration
os.environ["AKIOS_AUDIT_PATH"] = "./data/audit"
os.environ["AKIOS_WORKFLOW_TIMEOUT"] = "300"  # seconds
```

## Workflow Management

### Parsing Workflows

```python
from akios.core.runtime.workflow.parser import parse_workflow, parse_workflow_string

# Parse from file
workflow = parse_workflow("workflow.yml")

# Parse from string
yaml_content = """
name: "Test Workflow"
steps:
  - step: "test"
    agent: "filesystem"
    action: "read"
    parameters:
      path: "./test.txt"
"""

workflow = parse_workflow_string(yaml_content)

# Access workflow properties
print(f"Name: {workflow.name}")
print(f"Steps: {len(workflow.steps)}")
```

### Template Management

Use CLI commands to manage templates:

```bash
# List available templates
akios templates list

# Create workflow from template
akios templates copy hello-workflow ./my-workflow.yml
```

## Error Handling

### Error Classification

```python
from akios.core.error.classifier import classify_error

try:
    result = engine.run("invalid-workflow.yml")
except Exception as e:
    fingerprint = classify_error(str(e), type(e).__name__)

    print(f"Error category: {fingerprint.category}")
    print(f"Severity: {fingerprint.severity}")
    print(f"User message: {fingerprint.get_user_friendly_message()}")

    if fingerprint.recovery_suggestions:
        print("Suggestions:")
        for suggestion in fingerprint.recovery_suggestions:
            print(f"  - {suggestion}")
```

## Audit and Logging

### Audit Management

```python
from akios.core.audit import (
    append_audit_event,
    get_audit_log_path,
    export_audit
)

# Manually append audit event
append_audit_event({
    "workflow_id": "custom_workflow_123",
    "step": "custom_step",
    "agent": "custom_agent",
    "action": "custom_action",
    "result": {"status": "success"},
    "timestamp": "2026-01-15T10:30:00Z"
})

# Get audit log path
log_path = get_audit_log_path()
print(f"Audit log: {log_path}")

# Export audit trail (task_id currently ignored; exports latest audit data)
export_path = export_audit("latest", "json", "./audit_export.json")
print(f"Exported to: {export_path}")
```

### Audit Verification

```python
from akios.core.audit.verifier import verify_audit_integrity

# Verify audit log integrity
is_valid, root_hash = verify_audit_integrity()
if is_valid:
    print(f"Audit integrity verified. Merkle root: {root_hash}")
else:
    print("Audit integrity compromised!")
```

## Performance Monitoring

### Performance Tracking

```python
from akios.core.performance.monitor import (
    get_performance_monitor,
    measure_performance
)

monitor = get_performance_monitor()

# Manual timing
with monitor.measure_time("custom_operation"):
    # Your code here
    import time
    time.sleep(1.0)

# Get performance report
report = monitor.get_performance_report()
print(f"Memory usage: {report['memory_usage']['rss_mb']:.1f} MB")
print(f"Recommendations: {report['recommendations']}")

# Decorator for automatic timing
@measure_performance("my_function")
def my_function():
    # Function code
    pass
```

## Security Validation

### Runtime Security Checks

```python
from akios.security.validation import (
    validate_startup_security,
    validate_all_security
)

# Validate security at startup
try:
    validate_startup_security()
    print("Security validation passed")
except Exception as e:
    print(f"Security validation failed: {e}")

# Comprehensive security validation
security_status = validate_all_security()
print(f"Security status: {security_status}")
```

## Advanced Usage

### Custom Agents

```python
from akios.core.runtime.agents.base import BaseAgent
from typing import Dict, Any

class CustomAgent(BaseAgent):
    """Custom agent example"""

    def execute(self, action: str, config: Dict[str, Any],
                parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action == "custom_action":
            # Your custom logic here
            result = {"status": "success", "data": "custom result"}
            return result
        else:
            raise AgentError(f"Unknown action: {action}")

# Note: Custom agent registration is not supported in v1.0
# Use built-in agents: filesystem, http, llm, tool_executor
```

### Workflow Templates

```python
from akios.core.runtime.workflow import Workflow, WorkflowStep

# Create workflow programmatically
workflow = Workflow(
    name="Programmatic Workflow",
    description="Created via API",
    steps=[
        WorkflowStep(
            step_id="read_file",
            agent="filesystem",
            action="read",
            config={"allowed_paths": ["./data"]},
            parameters={"path": "./data/input.txt"}
        ),
        WorkflowStep(
            step_id="process_data",
            agent="llm",
            action="complete",
            config={},
            parameters={"prompt": "Process: {{read_file.content}}"}
        )
    ]
)

# Execute programmatic workflow
engine = WorkflowEngine(workflow)
result = engine.run()
```

### Event Callbacks

```python
from akios.core.runtime.engine import WorkflowEngine

def on_step_complete(step_result, workflow_context):
    """Callback for step completion"""
    print(f"Step {step_result['step']} completed")
    print(f"Duration: {step_result.get('duration', 0):.2f}s")

engine = WorkflowEngine()

# Execute with callback
result = engine.run(
    "workflow.yml",
    context={"on_step_complete": on_step_complete}
)
```

## Migration Guide

### From v0.x to v1.0

**Breaking Changes:**
- `WorkflowEngine` renamed to `RuntimeEngine` (alias maintained)
- Security validation now mandatory at startup
- PII redaction enabled by default
- Configuration format changed

**Migration Steps:**
```python
# Old code (v0.x)
from akios.engine import WorkflowEngine

```python
from akios.core.runtime.engine import WorkflowEngine  # or RuntimeEngine
```

# Configuration
The `config.yaml` file provides flat structure configuration for agent settings:
```

## Best Practices

### Performance
- Use lazy loading for large datasets
- Cache expensive operations
- Monitor memory usage with large files
- Use appropriate timeouts

### Security
- Always validate inputs
- Use allowed_paths restrictions
- Enable audit logging
- Keep API keys secure

### Error Handling
- Implement comprehensive error handling
- Use appropriate exception types
- Log errors for debugging
- Provide meaningful error messages

### Testing
- Use mock mode for testing
- Test with various input sizes
- Verify audit trail integrity
- Test error conditions

## Troubleshooting

### Common Issues

**Import Errors**
```python
# Ensure proper Python path
import sys
sys.path.insert(0, '/path/to/akios')

from akios.core.runtime.engine import WorkflowEngine
```

**Configuration Errors**
```python
# Validate configuration
from akios.config import validate_config
try:
    validate_config()
except Exception as e:
    print(f"Configuration error: {e}")
```

**Memory Issues**
```python
# Monitor memory usage
from akios.core.performance.monitor import get_performance_monitor
monitor = get_performance_monitor()
report = monitor.get_performance_report()
print(f"Memory: {report['memory_usage']}")
```

**Security Validation Failures**
```python
# Check security status
from akios.security.validation import validate_startup_security
try:
    validate_startup_security()
except Exception as e:
    print(f"Security issue: {e}")
    # Check Linux environment, seccomp, etc.
```
