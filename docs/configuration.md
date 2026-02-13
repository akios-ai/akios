# AKIOS v1.0.6 – Configuration Reference
**Document Version:** 1.0.6  
**Date:** 2026-02-13  

**Complete configuration guide for the AKIOS security cage.**

AKIOS uses a single `config.yaml` file for all settings. Configuration is loaded at startup and cannot be changed during execution for security. All settings have security-first defaults.

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

# Network Configuration
AKIOS_NETWORK_ACCESS_ALLOWED=false     # Allow external HTTP API calls
AKIOS_ALLOWED_DOMAINS="api.salesforce.com,api.mycompany.com"  # HTTPS whitelist for HTTP agent

# Mode Settings
AKIOS_MOCK_LLM=0              # 0=real LLM calls, 1=mock LLM output

# Docker Wrapper Controls
AKIOS_FORCE_PULL=1            # Always pull the latest image before running

# Optional: Provider-specific keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROK_API_KEY=xai-...
MISTRAL_API_KEY=your-mistral-key...
GEMINI_API_KEY=your-gemini-key...
```

**Network whitelist environment variable:**
- `AKIOS_NETWORK_ACCESS_ALLOWED=true` to enable HTTP agent
- `AKIOS_ALLOWED_DOMAINS="api.salesforce.com,api.example.com"` to whitelist domains (comma-separated)

### Real API Mode Flag

For convenience, you can enable real API mode directly from the command line:

```bash
# Enable real API mode with interactive setup
akios run workflow.yml --real-api

# This automatically:
# - Sets AKIOS_MOCK_LLM=0
# - Enables network access
# - Prompts for missing API keys interactively
# - Validates configuration
```

**The `--real-api` flag provides a seamless transition from mock testing to real API usage without manual configuration changes.**

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
max_tokens_per_call: 1000
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

### `allowed_domains`
**Type:** `list of strings`  
**Default:** `[]` (empty — only LLM APIs allowed)  
**Description:** HTTPS domains whitelist for HTTP agent requests

**Important:** LLM APIs (OpenAI, Anthropic, Grok, Mistral, Gemini) **always pass through** regardless of this setting — they are core to AKIOS functionality and never blocked.

This setting controls only the **HTTP agent** for custom API calls (CRM, data services, 3rd-party APIs).

**Example: Allow Salesforce and Custom API:**
```yaml
network_access_allowed: true
allowed_domains:
  - "api.salesforce.com"
  - "api.mycompany.com"
  - "data.example.org"
```

**All requests to domains NOT in this list will be blocked** (except LLM APIs).

**Via Environment Variable:**
```bash
# Single domain
AKIOS_ALLOWED_DOMAINS="api.salesforce.com"

# Multiple domains (comma-separated)
AKIOS_ALLOWED_DOMAINS="api.salesforce.com,api.mycompany.com,data.example.org"
```

**Security Note:** Each domain is checked against the whitelist. Subdomains are NOT automatically allowed — add them explicitly:
```yaml
allowed_domains:
  - "api.salesforce.com"
  - "analytics.salesforce.com"  # Must add separately
```

## 🛡️ PII & Compliance Settings

### `pii_redaction_enabled`
**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable real-time PII redaction on agent inputs

Automatically detects and redacts sensitive data in prompts and messages:
- Email addresses
- Phone numbers
- Social security numbers
- Credit card numbers
- IP addresses
- API keys and passwords
- NPI (National Provider Identifier)
- DEA Registration Numbers
- Medical Record Numbers (MRN-prefixed)

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

### `pii_redaction_outputs`
**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable PII redaction on LLM outputs

Applies additional PII filtering to AI-generated responses to prevent accidental data leakage. Uses conservative patterns suitable for generated content.

**Security Impact:** Prevents PII exposure in AI responses  
**Performance Impact:** Minimal (<1ms per response)

```yaml
pii_redaction_outputs: true  # Recommended: always true for security
```

### `pii_redaction_aggressive`
**Type:** `boolean`  
**Default:** `false`  
**Description:** Use aggressive PII redaction rules

When enabled, applies stricter patterns including:
- Generic address detection
- Extended phone number formats
- Additional sensitive pattern matching

**Use Case:** High-security environments requiring maximum protection  
**Trade-off:** May have false positives on legitimate content

```yaml
pii_redaction_aggressive: false  # Use only when maximum security required
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
**Default:** `1000`  
**Description:** Maximum tokens per LLM API call

Limits individual LLM requests to prevent excessive API costs.

```yaml
max_tokens_per_call: 500   # Conservative limit
max_tokens_per_call: 1000  # Default limit for complex tasks
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

> **Tip:** Run `akios status --budget` to view current spend vs. configured limit in real time.

##  Audit & Logging Settings

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
**Description:** Export format for audit reports

- `"json"`: Machine-readable JSON format with cryptographic integrity verification

```yaml
audit_export_format: "json"   # JSON format with integrity verification
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
# AKIOS v1.0 Production Configuration
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

## 🛠️ Installation Method Impact on Configuration

The way you install AKIOS affects available security features and default configurations:

### Pip Package Deployment
**Platforms:** Linux only (recommended)
**Security Level:** Full kernel-hard security
**Configuration Notes:**
- Maximum security features available
- Kernel-level sandboxing (seccomp-bpf, cgroups)
- Native filesystem permissions
- Best performance and security

### Docker Deployment
**Platforms:** Linux, macOS, Windows
**Security Level:** Strong policy-based security
**Configuration Notes:**
- Consistent behavior across platforms
- Container isolation instead of kernel sandboxing
- Network controls via container policies
- Memory and CPU limits via Docker

### Choosing the Right Installation

| Use Case | Recommended Method | Why |
|----------|-------------------|-----|
| **Maximum security, Linux production** | Pip Package | Kernel-hard security features |
| **Cross-platform development team** | Docker | Consistent environment everywhere |
| **Python ecosystem integration** | Pip Package | Full Python compatibility |

### Platform-Specific Configuration

#### Linux (All Methods)
```yaml
# Maximum security available
sandbox_enabled: true  # seccomp-bpf + cgroups
environment: "production"
```

#### macOS/Windows (Docker)
```yaml
# Strong policy-based security
sandbox_enabled: true  # Container policies + allowlisting
environment: "production"
# Note: No kernel-hard seccomp-bpf available
```

#### Docker (All Platforms)
```yaml
# Container-aware settings
sandbox_enabled: true
network_access_allowed: true  # For HTTP agent
# Docker handles resource isolation
```

### Configuration Validation by Method

AKIOS validates configuration compatibility with your deployment method:

```bash
# Pip package - validates Linux kernel features
akios status  # Shows kernel-hard security status

# Docker - validates container environment
akios status  # Shows policy-based security status
```

**Tip:** Run `akios status` after installation to see your security capabilities and configuration status.
