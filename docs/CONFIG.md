# AKIOS v1.1.0 – Configuration Reference
**Document Version:** 1.0.13  
**Date:** 2026-02-22  

**Complete configuration guide for the AKIOS security cage.**

AKIOS uses a single `config.yaml` file for all settings. Configuration is loaded at startup and cannot be changed during execution for security. All settings have security-first defaults.

## First-Time Setup & Configuration Management

AKIOS includes an interactive setup wizard that makes initial configuration effortless.

### Interactive Setup Wizard

The setup wizard guides you through:
- Provider selection (OpenAI, Anthropic, Grok, Mistral, or Gemini)
- API key setup with format validation
- Configuration generation and validation

```bash
# Setup wizard runs automatically on first command
akios run templates/hello-workflow.yml

# Or run manually
akios setup

# Force re-run if needed
akios setup --force
```

### Environment Variables (`.env` file)

AKIOS uses environment variables for sensitive configuration:

```bash
# API Keys (choose your provider)
AKIOS_LLM_PROVIDER=grok
GROK_API_KEY=xai-your-key-here
AKIOS_LLM_MODEL=grok-3

# Mode Settings
AKIOS_MOCK_LLM=0              # 0=real LLM calls, 1=mock LLM output
AKIOS_NETWORK_ACCESS_ALLOWED=1 # Allow external API calls

# Docker Wrapper Controls
AKIOS_FORCE_PULL=1            # Always pull the latest image before running

# Optional: Provider-specific keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROK_API_KEY=xai-...
MISTRAL_API_KEY=your-mistral-key...
GEMINI_API_KEY=your-gemini-key...
```

### Configuration Corruption Detection

AKIOS automatically detects and helps fix common `.env` file corruption:

- **Concatenated provider names**: `grokopenai` → suggests `grok`
- **Invalid API key formats**: Real-time validation with provider-specific checks
- **Malformed booleans**: `tru` → suggests `true`
- **Missing required fields**: Clear guidance on what's needed

**Example error with fix suggestion:**
```
CONFIGURATION VALIDATION FAILED: .env corruption detected
Line 3: AKIOS_LLM_PROVIDER=grokopenai
Suggestion: Concatenated provider names: 'grok' + 'openai' = 'grokopenai'
Fix: Change to AKIOS_LLM_PROVIDER=grok
```

### Configuration Loading Priority

1. **Environment Variables** (highest priority - override everything)
2. **`.env` file** (loaded automatically if present)
3. **`config.yaml`** (base configuration file)
4. **Built-in defaults** (secure fallbacks)

## 📁 Configuration File Location

AKIOS looks for `config.yaml` in the current working directory:

```
project/
├── config.yaml          # Main configuration file
├── workflows/           # Workflow definitions
├── templates/           # Workflow templates
├── data/               # Input/output data
└── audit/              # Audit logs
```

## ⚙️ Configuration Structure

```yaml
# Security cage essentials
sandbox_enabled: true
cpu_limit: 0.8
memory_limit_mb: 256
max_open_files: 100
max_file_size_mb: 10
network_access_allowed: false

# PII & compliance
pii_redaction_enabled: true
redaction_strategy: "mask"

# Cost & loop protection
cost_kill_enabled: true
max_tokens_per_call: 500
budget_limit_per_run: 1.0

# Audit & paths
audit_enabled: true
audit_storage_path: "./audit/"
audit_export_format: "json"

# General
environment: "development"
log_level: "INFO"
```

## 🔒 Security Cage Settings

### `sandbox_enabled`
**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable security sandboxing (kernel-level on native Linux with seccomp-bpf, policy-based in Docker)

When enabled:
- Processes run in isolated kernel namespaces
- Dangerous system calls are blocked
- Filesystem access is restricted
- Network access is controlled

**Security Impact:** Critical - provides the core isolation guarantee

```yaml
sandbox_enabled: true  # Recommended: always true
```

### `cpu_limit`
**Type:** `float` (0.1 - 1.0)  
**Default:** `0.8`  
**Description:** CPU usage limit as fraction of total CPU cores

Limits the CPU resources available to the entire workflow. Prevents runaway processes from consuming all system CPU.

```yaml
cpu_limit: 0.8  # Use 80% of available CPU cores
```

### `memory_limit_mb`
**Type:** `integer` (> 0)  
**Default:** `256`  
**Description:** Memory limit in megabytes for the entire workflow

Automatically terminates workflows that exceed memory limits. Prevents memory exhaustion attacks.

```yaml
memory_limit_mb: 256  # 256MB limit per workflow
```

### `max_open_files`
**Type:** `integer` (> 10)  
**Default:** `100`  
**Description:** Maximum number of open file descriptors

Prevents file descriptor exhaustion attacks and limits concurrent file operations.

```yaml
max_open_files: 100  # Maximum 100 open files
```

### `max_file_size_mb`
**Type:** `integer` (> 0)  
**Default:** `10`  
**Description:** Maximum file size in megabytes for write operations

Limits the size of files that can be written to prevent disk space exhaustion.

```yaml
max_file_size_mb: 10  # 10MB max file size
```

### `network_access_allowed`
**Type:** `boolean`  
**Default:** `false`  
**Description:** Allow network access for HTTP agent operations

When disabled, HTTP agent requests are blocked. When enabled, rate-limited network access is allowed.

```yaml
network_access_allowed: false  # Block all network access (secure)
network_access_allowed: true   # Allow HTTP agent network calls
```

## 🛡️ PII & Compliance Settings

### `pii_redaction_enabled`
**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable real-time PII redaction on all agent inputs/outputs

Automatically detects and redacts:
- Email addresses
- Phone numbers
- Social security numbers
- Credit card numbers
- IP addresses
- API keys and passwords
- **NPI numbers** (National Provider Identifier — healthcare)
- **DEA registration numbers** (Drug Enforcement Administration — healthcare)
- **Medical record numbers (MRN)** (healthcare)
- Insurance policy, group, claim, and prior-authorization numbers

```yaml
pii_redaction_enabled: true  # Recommended: always true
```

### `redaction_strategy`
**Type:** `string` ("mask" | "hash" | "remove")  
**Default:** `"mask"`  
**Description:** How to handle detected PII data

- `"mask"`: Replace with `[REDACTED]` placeholder
- `"hash"`: Replace with SHA-256 hash
- `"remove"`: Completely remove the data

```yaml
redaction_strategy: "mask"  # Safe, preserves data structure
```

## 💰 Cost & Resource Protection

### `cost_kill_enabled`
**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable automatic termination when budget limits are exceeded

Provides financial protection against runaway AI costs and infinite loops.

```yaml
cost_kill_enabled: true  # Recommended: always true
```

### `max_tokens_per_call`
**Type:** `integer` (> 0)  
**Default:** `500`  
**Description:** Maximum tokens per LLM API call

Limits individual LLM requests to prevent excessive API costs.

```yaml
max_tokens_per_call: 500  # Conservative limit
max_tokens_per_call: 1000 # Higher limit for complex tasks
```

### `budget_limit_per_run`
**Type:** `float` (> 0.0)  
**Default:** `1.0`  
**Description:** Maximum budget in USD per workflow execution

Automatically terminates workflows that exceed cost limits.

```yaml
budget_limit_per_run: 1.0   # $1.00 per workflow (recommended)
budget_limit_per_run: 5.0   # $5.00 for complex workflows
```

## 📊 Audit & Logging Settings

### `audit_enabled`
**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable comprehensive audit logging

Records every agent action with cryptographic integrity proof.

```yaml
audit_enabled: true  # Recommended: always true
```

### `audit_storage_path`
**Type:** `string`  
**Default:** `"./audit/"`  
**Description:** Directory path for storing audit logs

Audit logs are stored as tamper-evident JSON Lines files.

```yaml
audit_storage_path: "./audit/"  # Default audit directory
audit_storage_path: "/var/log/akios/"  # Custom path
```

### `audit_export_format`
**Type:** `string` ("json")
**Default:** `"json"`
**Description:** Default format for audit exports

- `"json"`: Machine-readable JSON format for audit data

```yaml
audit_export_format: "json"  # Machine-readable audit data
```

## 🧪 Ablation Flags (Benchmarking)

AKIOS supports ablation flags for controlled performance benchmarking. These flags
disable specific security features to measure their overhead. **Use only for testing.**

### CLI Usage

```bash
# Disable PII redaction (measure PII overhead)
akios cage up --no-pii

# Disable audit logging (measure audit overhead)
akios cage up --no-audit

# Disable cost kill-switch (measure budget enforcement overhead)
akios cage up --no-budget

# Combine flags for full ablation study
akios cage up --no-pii --no-audit --no-budget
```

### How It Works

Each flag sets the corresponding `.env` variable:

| Flag | Environment Variable | Config Key | Default |
|------|---------------------|------------|---------|
| `--no-pii` | `AKIOS_PII_REDACTION_ENABLED=false` | `pii_redaction_enabled` | `true` |
| `--no-audit` | `AKIOS_AUDIT_ENABLED=false` | `audit_enabled` | `true` |
| `--no-budget` | `AKIOS_COST_KILL_ENABLED=false` | `cost_kill_enabled` | `true` |

### Engine Enforcement

When ablation flags are active:
- **`audit_enabled=false`**: Engine skips all audit event emission (startup health checks, per-step logs, workflow completion/failure events). No ledger writes occur.
- **`cost_kill_enabled=false`**: Engine skips cost budget enforcement. Cost overspend will not halt workflow execution.
- **`pii_redaction_enabled=false`**: Agents skip PII redaction on inputs/outputs. Data flows unmasked.

### Restoring Defaults

```bash
# Restore full security (resets all ablation flags)
akios cage up
```


## ⚙️ General Settings

### `environment`
**Type:** `string` ("development" | "testing" | "production")  
**Default:** `"development"`  
**Description:** Runtime environment identifier

Affects logging verbosity and security strictness.

```yaml
environment: "development"  # More verbose logging
environment: "production"   # Stricter security, less logging
```

### `log_level`
**Type:** `string` ("DEBUG" | "INFO" | "WARNING" | "ERROR")  
**Default:** `"INFO"`  
**Description:** Logging verbosity level

Controls the detail level of console and file logging.

```yaml
log_level: "DEBUG"    # Maximum verbosity (development)
log_level: "INFO"     # Standard verbosity (recommended)
log_level: "WARNING"  # Only warnings and errors
```

## 🔧 Environment Variables

AKIOS supports environment variable configuration with the `AKIOS_` prefix:

```bash
# Override config values
export AKIOS_CPU_LIMIT=0.5
export AKIOS_MEMORY_LIMIT_MB=128
export AKIOS_BUDGET_LIMIT_PER_RUN=0.5
export AKIOS_LOG_LEVEL=DEBUG
```

## 📋 Complete Example Configuration

```yaml
# AKIOS V1.0.O Production Configuration
# Security-maximized settings for production workloads

# Security cage - maximum protection
sandbox_enabled: true
cpu_limit: 0.5
memory_limit_mb: 128
max_open_files: 50
max_file_size_mb: 5
network_access_allowed: false

# PII protection - always enabled
pii_redaction_enabled: true
redaction_strategy: "mask"

# Cost control - strict limits
cost_kill_enabled: true
max_tokens_per_call: 250
budget_limit_per_run: 0.5

# Audit - comprehensive
audit_enabled: true
audit_storage_path: "./audit/"
audit_export_format: "json"

# Environment
environment: "production"
log_level: "WARNING"
```

## ⚠️ Configuration Security Notes

- **Configuration is read-only** after AKIOS startup
- **No runtime configuration changes** for security
- **Validate config files** before deployment
- **Use restrictive permissions** on config files (`600`)
- **Never commit secrets** to version control

## 🔍 Configuration Validation

AKIOS validates configuration at startup:

```bash
# Test configuration without running workflows
akios --help  # Validates config during initialization

# Check for configuration errors
akios status  # Shows current configuration status
```

Invalid configurations will fail immediately with clear error messages.

## 🚀 Quick Start Configurations

### Development (Relaxed)
```yaml
sandbox_enabled: true
cpu_limit: 0.8
memory_limit_mb: 512
network_access_allowed: true
budget_limit_per_run: 5.0
log_level: "DEBUG"
```

### Production (Secure)
```yaml
sandbox_enabled: true
cpu_limit: 0.5
memory_limit_mb: 128
network_access_allowed: false
budget_limit_per_run: 1.0
log_level: "WARNING"
```

### Testing (Minimal)
```yaml
sandbox_enabled: false  # Disable for faster testing
cpu_limit: 0.9
memory_limit_mb: 1024
network_access_allowed: true
budget_limit_per_run: 10.0
log_level: "DEBUG"
```

**Remember:** Configuration cannot be changed during workflow execution. Plan your settings carefully for the security and performance profile you need.
