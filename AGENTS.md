# AKIOS v1.5.2 – Core Agents Reference
**Document Version:** 1.5.2  
**Date:** 2026-03-14  

**The 6 core agents that power AKIOS workflows with military-grade security.**

AKIOS provides 6 specialized agents, each running inside the security cage with full audit logging, syscall sandboxing, and automatic PII redaction. These agents form the foundation of secure AI workflows.

## 🔒 Security Guarantees (All Agents)

Every agent execution includes:
- **Process isolation** via cgroups v2 + seccomp-bpf
- **Syscall filtering** blocking dangerous operations
- **PII redaction** on all inputs/outputs (>95% accuracy)
- **Cryptographic audit logging** of every action
- **Cost/resource limits** with automatic kill-switches
- **Sandbox enforcement** preventing system access

## 📁 Filesystem Agent

**Secure file operations with path whitelisting and read-only defaults.**

### Purpose
Provides controlled access to the filesystem while preventing directory traversal attacks, unauthorized file access, and data exfiltration.

### Actions

#### `read`
Read file contents with automatic PII redaction.
```yaml
- name: "read_document"
  agent: "filesystem"
  action: "read"
  parameters:
    path: "data/input/document.txt"
```

**Parameters:**
- `path` (string): File path to read (must be in allowed paths)
- `encoding` (string, optional): Text encoding (default: "utf-8")

**Returns:**
- `content` (string): File contents with PII redacted
- `size` (int): File size in bytes
- `encoding` (string): Text encoding used

#### `write`
Write content to file (disabled by default for security).
```yaml
- name: "write_output"
  agent: "filesystem"
  action: "write"
  parameters:
    path: "data/output/result.txt"
    content: "Analysis complete"
```

**Parameters:**
- `path` (string): File path to write (must be in allowed paths)
- `content` (string): Content to write
- `encoding` (string, optional): Text encoding (default: "utf-8")
- `mode` (string, optional): Write mode ("w", "a") (default: "w")

#### `list`
List directory contents.
```yaml
- name: "list_files"
  agent: "filesystem"
  action: "list"
  parameters:
    path: "data/input"
```

**Parameters:**
- `path` (string): Directory path to list (must be in allowed paths)
- `pattern` (string, optional): Glob pattern to filter files

**Returns:**
- `files` (array): List of file/directory names
- `directories` (array): List of subdirectory names

#### `exists`
Check if file/directory exists.
```yaml
- name: "check_file"
  agent: "filesystem"
  action: "exists"
  parameters:
    path: "data/input/document.txt"
```

**Parameters:**
- `path` (string): Path to check

**Returns:**
- `exists` (boolean): Whether path exists
- `is_file` (boolean): Whether path is a file
- `is_directory` (boolean): Whether path is a directory

#### `stat`
Get file/directory metadata.
```yaml
- name: "file_info"
  agent: "filesystem"
  action: "stat"
  parameters:
    path: "data/input/document.txt"
```

**Parameters:**
- `path` (string): Path to stat

**Returns:**
- `size` (int): File size in bytes
- `modified` (string): Last modification timestamp
- `permissions` (string): File permissions string
- `is_file` (boolean): Whether path is a file
- `is_directory` (boolean): Whether path is a directory

### Security Controls

- **Path whitelisting**: Only allowed directories can be accessed
- **Default read-only**: Write operations require explicit enabling
- **PII redaction**: All file contents automatically redacted
- **Audit logging**: Every file access logged with Merkle proof

### Allowed Paths (Default)
- `./workflows` - Workflow definitions
- `./templates` - Workflow templates
- `./data/input` - Input data files
- `./data/output` - Output data files

## 🌐 HTTP Agent

**Secure web service calls with domain whitelisting, rate limiting, and automatic PII redaction.**

Also available as a standalone CLI command: `akios http <METHOD> <URL>`.

### Purpose
Makes HTTP requests while enforcing domain whitelisting, security boundaries, rate limits, and data protection. Outbound requests are restricted to configured `allowed_domains`; LLM provider APIs always bypass the whitelist.

### Actions

#### `get`
Make HTTP GET request.
```yaml
- name: "fetch_data"
  agent: "http"
  action: "get"
  parameters:
    url: "https://api.example.com/data"
    headers:
      Authorization: "Bearer token123"
```

#### `post`
Make HTTP POST request.
```yaml
- name: "submit_data"
  agent: "http"
  action: "post"
  parameters:
    url: "https://api.example.com/submit"
    data:
      name: "John Doe"
      email: "john@example.com"  # Will be redacted in logs
```

#### `put`
Make HTTP PUT request.
```yaml
- name: "update_record"
  agent: "http"
  action: "put"
  parameters:
    url: "https://api.example.com/record/123"
    json:
      status: "completed"
```

#### `delete`
Make HTTP DELETE request.
```yaml
- name: "delete_record"
  agent: "http"
  action: "delete"
  parameters:
    url: "https://api.example.com/record/123"
```

### Common Parameters

- `url` (string): Target URL (must be HTTP/HTTPS and in allowed_domains whitelist)
- `headers` (object, optional): HTTP headers
- `data` (string/object, optional): Request body data
- `json` (object, optional): JSON request body
- `params` (object, optional): URL query parameters
- `timeout` (int, optional): Request timeout in seconds (default: 30)
- `allow_redirects` (boolean, optional): Follow redirects (default: true)

### Returns

- `status_code` (int): HTTP status code
- `headers` (object): Response headers
- `content` (string): Response body (PII redacted)
- `json` (object): Parsed JSON response (if applicable)
- `url` (string): Final URL after redirects

### Security Controls

- **Domain whitelisting**: Only configured `allowed_domains` permitted
- **Rate limiting**: 10 requests per minute maximum
- **PII redaction**: All request/response data automatically redacted
- **HTTPS enforcement**: Only HTTPS URLs permitted when sandbox is active — plain `http://` blocked
- **Timeout enforcement**: 30-second default timeout
- **Audit logging**: Every HTTP request logged with redacted data

## 🤖 LLM Agent

**Secure language model API calls with token tracking and cost kill-switches.**

### Purpose
Makes calls to language model APIs (OpenAI, Anthropic, Grok, Mistral, Gemini, AWS Bedrock, Ollama) while tracking token usage, enforcing cost limits, and ensuring data protection.

### Actions

#### `complete`
Generate text completion.
```yaml
- name: "analyze_text"
  agent: "llm"
  action: "complete"
  parameters:
    prompt: "Analyze this document and summarize key points"
    model: "gpt-4o-mini"
    max_tokens: 500
```

#### `chat`
Have a conversation with context.
```yaml
- name: "chat_completion"
  agent: "llm"
  action: "chat"
  parameters:
    messages:
      - role: "system"
        content: "You are a helpful assistant"
      - role: "user"
        content: "Hello, how are you?"
    model: "gpt-4o-mini"
```

### Parameters

- `prompt` (string): Text prompt for completion
- `messages` (array): Chat messages for conversation
- `model` (string, optional): Model to use (default: "gpt-4o-mini")
- `provider` (string, optional): LLM provider — `openai`, `anthropic`, `grok`, `mistral`, `gemini`, `bedrock`, or `ollama`
- `max_tokens` (int, optional): Maximum tokens to generate (default: 1000)
- `temperature` (float, optional): Randomness (0.0-2.0, default: 0.7)
- `top_p` (float, optional): Nucleus sampling (default: 1.0)
- `frequency_penalty` (float, optional): Repetition penalty (default: 0.0)
- `presence_penalty` (float, optional): Topic diversity (default: 0.0)

### Returns

- `content` (string): Generated text (PII redacted)
- `usage` (object): Token usage statistics
  - `prompt_tokens` (int): Tokens in prompt
  - `completion_tokens` (int): Tokens generated
  - `total_tokens` (int): Total tokens used
- `cost` (float): Estimated cost in USD
- `model` (string): Model used
- `finish_reason` (string): Why generation stopped
- `pii_redactions_applied` (int): Number of PII instances redacted in output
- `pii_patterns_found` (array): PII types detected in output, e.g. `["email", "ssn"]`

### Security Controls

- **Cost kill-switches**: Automatic termination if budget exceeded
- **Token limits**: Hard caps on token usage (default: 1000)
- **PII redaction**: All prompts and responses automatically redacted
- **API key protection**: Keys never logged or exposed
- **IAM authentication**: AWS Bedrock uses IAM credentials — no API key needed
- **Rate limiting**: Built-in API rate limit handling

### Cost Controls

- **Session tracking**: Cumulative cost and token tracking
- **Budget limits**: $1.00 default per workflow
- **Kill switches**: Automatic termination on budget violations
- **Cost logging**: Every API call logged with cost data
- **Dashboard**: Run `akios status --budget` to view real-time cost breakdown per workflow

## 🛠️ Tool Executor Agent

**Secure external command execution in sandboxed subprocess.**

### Purpose
Runs external commands and tools while enforcing strict security boundaries, syscall filtering, and resource limits.

### Actions

#### `run`
Execute external command.
```yaml
- name: "run_command"
  agent: "tool_executor"
  action: "run"
  parameters:
    command: "ls -la"
    args: ["data/input"]
    timeout: 10
```

### Parameters

- `command` (string): Command to execute (must be in allowed list)
- `args` (array, optional): Command arguments
- `timeout` (int, optional): Execution timeout in seconds (default: 30)
- `env` (object, optional): Environment variables
- `working_dir` (string, optional): Working directory

### Returns

- `stdout` (string): Standard output (PII redacted)
- `stderr` (string): Standard error (PII redacted)
- `returncode` (int): Command exit code
- `duration` (float): Execution time in seconds
- `command` (string): Command executed (logged for audit)

### Security Controls

- **Command whitelisting**: Only pre-approved commands allowed
- **Syscall sandboxing**: Dangerous system calls blocked
- **Resource limits**: CPU, memory, and time restrictions
- **PII redaction**: All command output automatically redacted
- **Path restrictions**: Limited filesystem access
- **`--exec` rejection**: The hidden `--exec` flag on `akios run` is a security trap that blocks shell-injection attempts

### Allowed Commands (Default)

Safe, commonly needed commands:
- `echo`, `cat`, `grep`, `head`, `tail`
- `wc`, `sort`, `uniq`, `cut`, `tr`
- `date`, `pwd`, `ls`
- `find`, `ps`, `df`, `free`
- `sh`, `true`, `false`, `sleep`
- `env`, `file`

### Resource Limits

- **Timeout**: 30 seconds default, 300 seconds maximum
- **Output size**: 1MB maximum per command
- **Process isolation**: Each command in separate sandboxed process
- **Memory limits**: Automatic termination on excessive memory usage

---

## 🔔 Webhook Agent

**Secure notification delivery to Slack, Discord, Teams, or any HTTP endpoint.**

### Purpose
Sends workflow notifications and alerts to external platforms with full PII redaction on message content and HTTPS enforcement.

### Actions

#### `notify` / `send`
Send a notification to a platform or generic endpoint.
```yaml
- name: "alert_team"
  agent: "webhook"
  action: "notify"
  parameters:
    url: "https://hooks.slack.com/services/..."
    message: "Workflow complete: {{ output }}"
    platform: "slack"  # slack | discord | teams | generic
```

**Parameters:**
- `url` (string): Webhook URL (HTTPS required)
- `message` (string): Message content (PII automatically redacted)
- `platform` (string, optional): `slack`, `discord`, `teams`, `generic` (default: `generic`)
- `headers` (object, optional): Additional HTTP headers
- `timeout` (int, optional): Request timeout in seconds (default: 30)

**Returns:**
- `status_code` (int): HTTP response status
- `success` (boolean): Whether delivery was confirmed
- `pii_redactions_applied` (int): PII items redacted from message

### Security Controls
- **HTTPS enforcement**: Plain `http://` blocked
- **PII redaction**: All message content automatically redacted
- **Rate limiting**: 10 requests per minute
- **Retry policy**: 3 attempts with exponential backoff
- **Audit logging**: Every notification logged

---

## 🗄️ Database Agent

**Secure SQL queries against PostgreSQL or SQLite with injection prevention.**

### Purpose
Runs SQL queries against configured databases while enforcing parameterized-query-only execution, DDL blocking, row limits, and PII redaction on results.

### Actions

#### `query`
Run a SELECT query and return results.
```yaml
- name: "fetch_records"
  agent: "database"
  action: "query"
  parameters:
    query: "SELECT id, status FROM orders WHERE created_at > ?"
    params: ["2026-01-01"]
    database: "orders.db"
```

#### `execute`
Run a write statement (requires `allow_write: true` in config).
```yaml
- name: "update_status"
  agent: "database"
  action: "execute"
  parameters:
    query: "UPDATE orders SET status = ? WHERE id = ?"
    params: ["processed", 42]
```

#### `count`
Count rows matching a condition.
```yaml
- name: "count_pending"
  agent: "database"
  action: "count"
  parameters:
    table: "orders"
    where: "status = 'pending'"
```

**Common Parameters:**
- `query` (string): SQL query string (parameterized only — no string concatenation)
- `params` (array, optional): Positional query parameters
- `database` (string): SQLite file path or PostgreSQL DSN
- `timeout` (int, optional): Query timeout seconds (default: 60)

**Returns:**
- `rows` (array): Query result rows (PII redacted)
- `row_count` (int): Number of rows returned
- `columns` (array): Column names

### Security Controls
- **Parameterized queries only**: No raw SQL string building
- **SELECT only by default**: `allow_write: false` in config
- **DDL always blocked**: CREATE, DROP, ALTER, TRUNCATE — no override possible
- **Row limits**: Maximum 10,000 rows per query
- **PII redaction**: All result data automatically redacted
- **Audit logging**: Every query logged with redacted parameters

### Backends
- **SQLite**: Built-in, no extra dependencies
- **PostgreSQL**: Requires `psycopg2` (`pip install psycopg2-binary`)

---

## ⚙️ Agent Configuration

All agents respect `config.yaml` settings:

```yaml
# Cost limits (LLM Agent)
budget_limit_per_run: 1.0      # $1 per workflow
max_tokens_per_call: 500       # LLM token limits

# Security controls (All Agents)
sandbox_enabled: true          # Syscall restrictions
pii_redaction_enabled: true    # Auto PII masking (SSN, email, credit card, etc.)
network_access_allowed: false  # HTTP agent control
allowed_domains:               # Domain whitelist for HTTP agent
  - api.example.com

# Audit (All Agents)
audit_enabled: true           # Full logging
audit_export_format: "json"    # Compliance exports

# Resource limits (Tool Executor)
max_command_timeout: 30       # seconds
max_output_size: 1048576      # 1MB
```

## 🔍 Agent Selection Guide

| Use Case | Recommended Agent | Why |
|----------|-------------------|-----|
| File processing | **Filesystem** | Secure file I/O with path controls |
| API integration | **HTTP** | Rate-limited, domain-whitelisted web service calls |
| Text generation | **LLM** | Token-tracked AI completions |
| Data processing | **Tool Executor** | Safe command-line tools |
| Document analysis | **Filesystem** + **LLM** | Read files, then analyze |
| Web scraping | **HTTP** + **Filesystem** | Fetch data, save results |
| System monitoring | **Tool Executor** | Safe system commands |
| Prompt inspection | **CLI** (`protect show-prompt`) | Preview interpolated + redacted LLM prompts |
| Team notifications | **Webhook** | Slack/Discord/Teams delivery with PII redaction |
| Structured data queries | **Database** | Safe SQL with injection prevention |
| Workflow alerts | **Webhook** + **LLM** | Generate alert text, then notify |

## 🚨 Security Notes

- **All agents run sandboxed** with kernel-level isolation
- **PII redaction applied** to all inputs and outputs. If PII module is unavailable, data is blocked (never passed through raw).
- **Cost limits enforced** with automatic kill-switches
- **Full audit trail** maintained for compliance
- **Network access controlled** via domain whitelisting per agent capabilities
- **Shell injection blocked** via `--exec` rejection trap

**Agents cannot escape the security cage — guaranteed by kernel primitives.**
