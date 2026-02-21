# AKIOS v1.0.8 CLI Reference
**Document Version:** 1.0.8  
**Date:** 2026-02-19  

## 🚀 Three Ways to Run AKIOS

AKIOS v1.0.8 supports three deployment methods:

### Native Linux (Maximum Security)
```bash
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

akios init
akios run templates/hello-workflow.yml
```
**Requirements**: Linux kernel 5.4+ with cgroups v2 and seccomp-bpf

### Docker (Cross-Platform)
```bash
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios
./akios init my-project
cd my-project
./akios run templates/hello-workflow.yml
```
**Requirements**: Docker Desktop (works on Linux, macOS, Windows)
**Benefits**: Smart caching, progress feedback, optimized for performance

### Direct Docker (Emergency Fallback)
```bash
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.8 init my-project
cd my-project
# Create wrapper script
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.8 "$@"' > akios
chmod +x akios
```
**Requirements**: Docker (works when wrapper download fails)

## Overview

AKIOS provides a simple, secure command-line interface for running AI agent workflows with military-grade security. The CLI focuses on essential operations: project management, workflow execution and management, templates, audit, logging, and cleanup.

**Philosophy**: Simple, secure, and cage-enforced — no bloat, just the gateway to the security cage.

## Core Commands

### `akios --help` / `akios -h` - Show Usage

Display help information and list available commands.

```bash
akios --help
akios -h
akios --debug status  # Enable debug logging for troubleshooting
```

**Global Options:**
- `--debug`: Enable debug logging for troubleshooting
- `--help, -h`: Show help information
- `--version`: Show version information

### `akios --version` - Show Version

Display the AKIOS version with build information.

```bash
akios --version
```

Shows version number, build date, and git commit information when available for debugging and support.

### `akios init` - Initialize Project

Create a minimal AKIOS project skeleton with configuration and templates.

```bash
# Initialize project with welcome messages
akios init

# Initialize project quietly (suppress welcome messages)
akios init --quiet

# Initialize in specific subdirectory
akios init my-project

# Initialize and run setup wizard immediately
akios init --wizard
```

This creates:
- `config.yaml` - Configuration file
- `templates/` - Directory with example workflow templates
- `.env` - Environment variables file with real API keys (NEVER commit)
- `.env.example` - Template file with placeholder keys (safe to commit)
- `data/` - Input/output directories with sample data for testing
- `audit/` - Security audit logs

**Options:**
- `--force`: Overwrite existing files
- `--quiet`: Suppress welcome message and success output
- `--json`: Output in JSON format
- `--wizard`: Run the setup wizard after project initialization

**API Key Setup:**
```bash
# Copy template to create your working environment file
cp .env.example .env

# Edit .env with your real API keys
# The .env.example file is safe to commit to version control
```

### `akios setup` - Interactive Setup Wizard

Guided setup wizard for configuration management.

Run the interactive setup wizard to configure AKIOS with your API keys and preferences. The wizard guides you through provider selection, API key setup, and configuration validation.

```bash
# Run the setup wizard (first-time users see this automatically)
akios setup

# Force re-run the setup wizard
akios setup --force

# Non-interactive setup (for automated environments)
akios setup --non-interactive

# Automated setup with recommended defaults (CI/CD ready)
akios setup --defaults

# Pre-select AI provider (enables automated setup)
akios setup --provider grok

# Enable mock mode setup (no API keys needed)
akios setup --mock-mode
```

**Features:**
- **Provider Selection**: Choose from 5 AI providers (OpenAI, Anthropic, Grok, Mistral, Gemini)
- **Model Selection**: Pick specific models (gpt-4o, claude-3-sonnet, grok-3, etc.)
- **API Key Validation**: Real-time format checking and test API calls
- **Advanced Settings**: Configure budget limits and token controls
- **Secure Storage**: API keys stored securely in `.env` file
- **Error Recovery**: Detects and fixes common configuration issues
- **Container Compatible**: Works in Docker containers and native terminals
- **CI/CD Automation**: Non-interactive flags for automated deployments

**What it configures:**
- AI provider and specific model selection
- API key setup with validation
- Budget limits per workflow ($1.00 default)
- Token limits per API call (1000 default)
- Network access for API calls
- Mock vs real LLM mode settings
- Security and audit preferences

**Automation Options:**
- `--defaults`: Uses recommended defaults for instant setup
- `--provider {openai,anthropic,grok,mistral,google}`: Pre-selects AI provider
- `--mock-mode`: Enables mock mode without API keys
- `--non-interactive`: Skips setup wizard entirely

## 🔍 LLM Provider/Model Validation

AKIOS validates LLM provider and model compatibility at startup to prevent API failures and provide clear error messages.

### Supported Providers & Models

| Provider | Models |
|----------|--------|
| **OpenAI** | `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`, `gpt-4o`, `gpt-4o-mini` |
| **Anthropic** | `claude-3.5-haiku`, `claude-3.5-sonnet` |
| **Grok** | `grok-3` |
| **Mistral** | `mistral-small`, `mistral-medium`, `mistral-large` |
| **Gemini** | `gemini-1.0-pro`, `gemini-1.5-pro`, `gemini-1.5-flash` |

### Validation Rules

- **Provider Check**: Must be one of the 5 supported providers
- **Model Check**: Model must be compatible with selected provider
- **Case Insensitive**: Model names are matched case-insensitively (e.g., `GPT-4` works)
- **Early Failure**: Invalid combinations are caught during configuration loading, not during workflow execution

### Configuration Examples

**Valid combinations:**
```bash
# OpenAI GPT-4
AKIOS_LLM_PROVIDER=openai AKIOS_LLM_MODEL=gpt-4 ./akios status

# Anthropic Claude
AKIOS_LLM_PROVIDER=anthropic AKIOS_LLM_MODEL=claude-3-sonnet-20240229 ./akios status

# xAI Grok
AKIOS_LLM_PROVIDER=grok AKIOS_LLM_MODEL=grok-3 ./akios status
```

**Invalid combinations (will fail with clear error):**
```bash
# Wrong provider for model
AKIOS_LLM_PROVIDER=openai AKIOS_LLM_MODEL=grok-3 ./akios status
# Error: "Model 'grok-3' is not valid for provider 'openai'"

# Invalid provider
AKIOS_LLM_PROVIDER=invalid AKIOS_LLM_MODEL=gpt-4 ./akios status
# Error: "Unknown LLM provider 'invalid'"
```

### Automation-Friendly Errors

For CI/CD and automation, use JSON mode for structured error output:
```bash
AKIOS_JSON_MODE=1 AKIOS_LLM_PROVIDER=openai AKIOS_LLM_MODEL=grok-3 ./akios status
# Output: {"error": true, "message": "Model 'grok-3' is not valid...", "type": "configuration_error"}
```

### `akios templates` - Manage Templates

Manage and list workflow templates.

```bash
# List available templates
akios templates list

# Select a template interactively (with fuzzy search)
akios templates select

# Select a template without fuzzy search
akios templates select --no-search
```

**Subcommands:**

#### `list`
List available templates with descriptions.

**Options:**
- `--json`: Output in JSON format

#### `select`
Interactively select a template.

**Options:**
- `--no-search`: Disable fuzzy search
- `--json`: Output selected template in JSON format

### `akios files` - Show Available Files

Display available input and output files for easy workflow management.

```bash
# Show all files (input and output)
akios files

# Show only input files
akios files input

# Show only output files
akios files output
```

**Input Files Display:**
```
📁 Input Files
=============
  analysis_target.docx               10KB  just now
  analysis_target.pdf                36KB  just now
  analysis_target.txt                 1KB  just now
  api_input.json                     260B  just now
```

**Output Files Display:**
```
📤 Recent Output Runs
====================
  run_2026-01-24_13-26-51      1 files  just now
  run_2026-01-24_13-18-58      1 files  1h ago
```

**Usage Tips:**
- Use this command to see what files are available for your workflows
- Input files can be referenced in YAML templates with `./data/input/filename`
- Output files are automatically organized in timestamped directories

### `akios run <workflow.yml>` - Execute Workflow

Execute an AKIOS workflow with full security sandboxing and audit logging.

```bash
# Run a workflow
akios run templates/hello-workflow.yml

# Run with verbose logging
akios run workflow.yml --verbose

# Enable real API mode with interactive setup
akios run workflow.yml --real-api

# Run with force flag (skip confirmation prompts)
akios run workflow.yml --force
```

**Options:**
- `--verbose`: Enable detailed execution logging
- `--quiet`: Suppress informational banners and non-error output
- `--real-api`: Enable real API mode with interactive API key setup (sets AKIOS_MOCK_LLM=0, network_access_allowed=true, prompts for missing keys)
- `--force`: Skip confirmation prompts for template switches
- `--debug`: Enable debug logging for troubleshooting
- `--exec`: **Security trap** — hidden flag that rejects with error "Direct shell execution is not permitted inside the security cage". Exists to block shell-injection attempts.

### `akios audit export` - Export Audit Reports

Export cryptographic audit reports in JSON format with Merkle root integrity verification.

**Requires:** `audit_export_enabled: true` in `config.yaml`.

```bash
# Export latest audit as JSON (auto-generated filename)
akios audit export

# Export with custom filename
akios audit export --output audit-report.json
```

**Options:**
- `--format`: Export format: json (default: json)
- `--output`: Output file path (default: auto-generated timestamp filename)

### `akios audit verify` - Verify Audit Log Integrity

Reconstruct the Merkle tree from raw events and verify the cryptographic chain of custody.

```bash
# Verify audit log integrity
akios audit verify

# Get verification proof as JSON
akios audit verify --json
```

**Options:**
- `--json`: Output structured verification proof as JSON

**Output includes:** integrity status (VERIFIED/TAMPERED), event count, Merkle root hash, stored root comparison, time range.

### `akios audit rotate` - Rotate Audit Log

Manually trigger audit log rotation. Archives the current ledger with Merkle chain linkage and starts a fresh ledger.

```bash
# Rotate audit log
akios audit rotate

# Get rotation result as JSON
akios audit rotate --json
```

**Options:**
- `--json`: Output rotation result as JSON

**How it works:** The current `audit_events.jsonl` is moved to `audit/archive/ledger_<timestamp>.jsonl`. A chain metadata entry is appended to `audit/archive/chain.jsonl` with the Merkle root of the archived segment.

### `akios audit stats` - Show Audit Statistics

Display audit ledger statistics: event count, ledger size, archive segments, Merkle root hash, and rotation threshold.

```bash
# Show audit stats
akios audit stats

# Get stats as JSON
akios audit stats --json
```

**Options:**
- `--json`: Output statistics as JSON

**Output includes:** current ledger events/size, total event count (all-time), rotation threshold (50,000), Merkle root hash, archive segment count/size.

### `akios workflow validate` - Validate Workflow YAML

Validate a workflow YAML file against the AKIOS schema without executing it.

```bash
# Validate a workflow file
akios workflow validate templates/hello-workflow.yml

# Get validation result as JSON
akios workflow validate workflow.yml --json
```

**Options:**
- `--json`: Output validation result as JSON

**Checks performed:**
- YAML syntax validation
- Required fields: `name`, `steps`
- Agent existence (filesystem, http, llm, tool_executor)
- Action validity per agent
- Step schema (integer step numbers, sequential numbering)
- File path existence for filesystem read/stat steps (warning)

### `akios logs` - View Execution Logs

Show recent workflow execution logs.

```bash
# Show recent logs (default: 10)
akios logs

# Show logs for specific task
akios logs --task workflow-123

# Show 50 log entries
akios logs --limit 50
```

**Options:**
- `--task, -t`: Filter by specific task ID
- `--limit, -n`: Number of log entries to show (default: 10)

### `akios status` - Show System Status

Display comprehensive runtime status, recent workflow execution summary, and budget information.

```bash
# Show current status (user-friendly format)
akios status

# Show detailed budget information
akios status --budget

# Show detailed security dashboard
akios status --security

# Show technical details for advanced users
akios status --verbose

# Show status in JSON format (for scripts)
akios status --json

# Show security information in JSON format
akios status --security --json
```

**Options:**
- `--budget`: Show detailed budget tracking and spending breakdown
- `--json`: Output in machine-readable JSON format
- `--verbose`: Show detailed technical information and metrics
- `--security`: Show detailed security status and active protections
- `--debug`: Enable debug logging for troubleshooting

### `akios doctor` - Run Diagnostics

Run a focused diagnostics report using the same checks as the security dashboard.

```bash
# Show diagnostics (user-friendly format)
akios doctor

# Show diagnostics in JSON format
akios doctor --json
```

**Options:**
- `--json`: Output in machine-readable JSON format
- `--verbose`: Show detailed technical information and metrics

### `akios clean` - Clean Project Data

Remove old workflow runs and free up disk space while preserving recent data.

```bash
# Clean runs older than 7 days (default behavior)
akios clean

# Clean runs older than 30 days
akios clean --old-runs 30

# Clean ALL runs
akios clean --all

# See what would be cleaned without deleting
akios clean --dry-run

# Get JSON output for scripting
akios clean --json
```

**Options:**
- `--old-runs`: Remove runs older than N days (default: 7)
- `--all`: Clean all runs regardless of age
- `--dry-run`: Show what would be cleaned without actually deleting
- `--yes`: Run without confirmation prompts
- `--json`: Output in JSON format

**Safety:** Only removes `data/output/run_*` directories. Audit logs are never touched.

### `akios compliance report` - Generate Compliance Reports

Generate compliance reports for workflow execution and security validation.

```bash
# Generate compliance report for a workflow
akios compliance report hello-workflow.yml

# Generate detailed compliance report
akios compliance report workflow.yml --type detailed

# Export compliance report to file
akios compliance report workflow.yml --output compliance-report.json

# Generate executive summary report
akios compliance report workflow.yml --type executive --format txt
```

**Options:**
- `--type`: Report type (basic, detailed, executive) - default: basic
- `--format`: Export format (json, txt) - default: json
- `--output`: Output file path (default: auto-generated filename)

**Report Types:**
- `basic`: Security validation summary and compliance status
- `detailed`: Includes technical details and audit events
- `executive`: High-level summary for management reporting

### `akios output` - Manage Workflow Outputs

Manage and organize workflow outputs with advanced file operations.

```bash
# Get the latest workflow output as deployable JSON
akios output latest

# List all workflow outputs
akios output list

# List outputs for specific workflow
akios output list hello-workflow.yml

# Clean old outputs for a workflow
akios output clean hello-workflow.yml --max-age 7

# Archive outputs for a workflow
akios output archive hello-workflow.yml --name archive.tar.gz
```

**Subcommands:**

#### `latest`
Retrieve the most recent workflow execution result as structured JSON — designed for CI/CD pipeline integration.

The output includes:
- **Metadata**: `akios_version`, `workflow_name`, `workflow_id`, `timestamp`
- **Execution**: `status`, `steps_executed`, `execution_time_seconds`
- **Security**: `pii_redaction`, `audit_enabled`, `sandbox_enabled`
- **Cost**: `total_cost`, `budget_limit`, `remaining_budget`, `over_budget`
- **Results**: Per-step array with `agent`, `action`, `status`, `execution_time`, `output`
- **Path**: `output_directory`

Example output:
```json
{
  "akios_version": "1.0.8",
  "workflow_name": "Hello World Workflow",
  "status": "completed",
  "steps_executed": 3,
  "execution_time_seconds": 2.68,
  "cost": { "total_cost": 0.00083, "budget_limit": 1.0, "over_budget": false },
  "results": [
    { "step": 1, "agent": "llm", "action": "complete", "output": "Hello from AKIOS..." },
    { "step": 2, "agent": "filesystem", "action": "write", "output": "Written to hello-ai.txt (324 bytes)" }
  ]
}
```

#### `list`
List workflow outputs.

**Arguments:**
- `workflow` (optional): Workflow name to filter by

**Options:**
- `--json`: Output in JSON format

#### `clean`
Clean old workflow outputs.

**Arguments:**
- `workflow` (required): Workflow name to clean

**Options:**
- `--max-age`: Maximum age in days (default: 30)
- `--max-count`: Maximum executions to keep (default: 50)
- `--dry-run`: Show what would be cleaned without actually cleaning
- `--json`: Output in JSON format

#### `archive`
Archive workflow outputs.

**Arguments:**
- `workflow` (required): Workflow name to archive

**Options:**
- `--name`: Archive filename (optional - auto-generated if not specified)
- `--json`: Output in JSON format

### `akios cage` / `akios security` - Security Cage Management

Manage the AKIOS security cage — control PII redaction, network access, sandboxing, and audit logging. `cage` and `security` are interchangeable aliases.

```bash
# Activate full security (PII redaction, HTTPS lock, sandbox, audit)
akios cage up

# Relax security for development (sandbox stays on)
akios cage down

# Show current cage posture and protection status
akios cage status

# Same commands via 'security' alias
akios security up
akios security down
akios security status
```

**Subcommands:**

#### `up`
Activate the full security cage. Sets:
- PII Redaction: **ENABLED**
- HTTPS Network: **LOCKED** (LLM APIs and user-defined `allowed_domains` pass through)
- Sandbox: **ENFORCED**
- Audit Logging: **ENABLED**

#### `down`
Deactivate the security cage and **destroy all session data**. This is the cage's core promise: when the cage goes down, nothing is left.

**Data destroyed:**
- `audit/` — All Merkle-chained audit logs
- `data/output/` — All workflow execution outputs (including `output.json`)
- `data/input/` — All user-provided input files

The `.env` file is reset to relaxed defaults (PII off, network open).

**Options:**
- `--keep-data`: Relax protections without wiping data (development convenience)
- `--passes N`: Number of overwrite passes for secure erasure (default: 1). More passes increase security. On SSDs, extra passes have limited benefit due to wear-leveling.
- `--fast`: Skip secure overwrite — files deleted without shredding. **WARNING**: data may be recoverable with forensic tools.

```bash
# Full cage down — destroy all data (default)
akios cage down

# Dev mode — relax protections, keep data for debugging
akios cage down --keep-data

# 3-pass DoD-style overwrite for maximum security
akios cage down --passes 3

# Fast wipe — just delete, no overwrite (CI/CD cleanup)
akios cage down --fast
```

> **Security guarantee**: Default `cage down` ensures zero data residue. Use `--keep-data` only during active development when you need to inspect outputs.

#### `status`
Show current cage posture (ACTIVE / RELAXED / CUSTOM) and protection table.

**How it works:** `cage up/down` writes to your project's `.env` file. The AKIOS engine reads these values at workflow runtime via `dotenv.load_dotenv()`. In Docker, restart the container for changes to take effect.

**Data lifecycle:** `cage up` → protections active → workflows generate data → `cage down` → all data destroyed. This guarantees no sensitive artifacts survive a cage session.

### `akios protect` - PII Protection Analysis

Analyze workflows and files for PII exposure before execution.

```bash
# Preview PII detection on a workflow (default: workflow.yml)
akios protect preview

# Preview on a specific workflow file
akios protect preview templates/hello-workflow.yml

# Scan a file for PII and show redaction results
akios protect scan data/input/document.txt

# JSON output for scripting
akios protect preview --json
akios protect scan data/input/document.txt --json
```

**Subcommands:**

#### `preview`
Scan workflow inputs for PII and show safe prompt construction.

**Arguments:**
- `workflow` (optional): Workflow file to analyze (default: `workflow.yml`)

**Options:**
- `--json`: Output in JSON format

#### `scan`
Scan a file for PII and display detected sensitive data categories.

**Arguments:**
- `file` (required): File to scan for PII

**Options:**
- `--json`: Output in JSON format

#### `show-prompt`
Display the fully interpolated and PII-redacted prompt that would be sent to the LLM.

```bash
# Show the exact prompt the LLM will receive
akios protect show-prompt workflow.yml

# Show prompt for a healthcare template
akios protect show-prompt templates/healthcare.yml
```

**Arguments:**
- `workflow` (required): Workflow file to inspect

**What it shows:**
- Template variables resolved with actual input data
- PII automatically redacted with typed markers
- The exact text that would be sent to the LLM provider

### `akios http` - Secure HTTP Requests

Make HTTP requests through the security cage with domain whitelisting and automatic PII redaction.

```bash
# GET request
akios http GET https://api.example.com/status

# POST with body and headers
akios http POST https://api.example.com/data \
  --body '{"key": "value"}' \
  --header "Authorization: Bearer $TOKEN" \
  --header "Content-Type: application/json"

# With timeout and JSON output
akios http GET https://api.example.com/report --timeout 60 --json-output
```

**Arguments:**
- `method` (required): HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- `url` (required): Target URL (must be in HTTPS whitelist when cage is active)

**Options:**
- `--body`: Request body for POST/PUT/PATCH
- `--header`: HTTP header (repeatable)
- `--timeout`: Request timeout in seconds (default: 30)
- `--json-output`: Format response as structured JSON

**Security:**
- All requests pass through domain whitelist enforcement
- Request/response bodies scanned for PII and redacted in audit logs
- Only HTTPS URLs permitted when sandbox is active — plain `http://` URLs blocked automatically
- Full audit trail of all HTTP activity

### `akios audit verify` - Verify Audit Integrity

Verify the Merkle-chain integrity of the cryptographic audit trail.

```bash
# Verify audit trail integrity
akios audit verify

# Verify with JSON output
akios audit verify --json
```

**Options:**
- `--json`: Output in machine-readable JSON format

**Returns:** Chain integrity status with stored vs recomputed Merkle root comparison. Shows **VERIFIED** (roots match, no tampering) or **TAMPERED** (mismatch detected). Returns exit code 1 on tampering.

### `akios audit log` - View Audit Log

View recent entries from the cryptographic audit log.

```bash
# View recent audit log entries
akios audit log

# View last 20 entries
akios audit log --limit 20
```

**Options:**
- `--limit, -n`: Number of entries to show (default: 10)
- `--json`: Output in JSON format

### `akios docs` - View Documentation

View AKIOS documentation with beautiful Markdown rendering directly in the terminal.

```bash
# Open documentation viewer
akios docs

# View specific documentation topic
akios docs security
akios docs workflows
```

### `akios timeline` - Workflow Timeline

View workflow execution timeline with performance analysis and step-by-step timing.

```bash
# Show execution timeline for last run
akios timeline

# Show timeline with detailed performance metrics
akios timeline --verbose

# JSON output for scripting
akios timeline --json
```

**Options:**
- `--verbose`: Show detailed performance metrics
- `--json`: Output in JSON format

### `akios testing` - Testing Context

View environment notes and testing context for the current project.

```bash
# Show testing context and environment info
akios testing

# Show testing notes recorded during workflow execution
akios testing show-notes

# Clear all testing notes
akios testing clear-notes

# Log a manual testing issue
akios testing log-issue "Description of the issue"
```

**Subcommands:**
- `show-notes` — Display all testing notes recorded during workflow execution
- `clear-notes` — Remove all stored testing notes
- `log-issue` — Manually log a testing issue for tracking

Displays mock mode status, API key availability, and testing recommendations.

## Quick Start Examples

### Native Linux Installation
```bash
# Install AKIOS
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

# 1. Initialize a new project
akios init

# 2. List available templates
akios templates list

# 3. Run an example workflow
akios run templates/hello-workflow.yml

# 4. Check system status
akios status

# 5. Clean up old runs (optional)
akios clean

# 6. Export audit proof
akios audit export --format json --output proof.json
```

### Docker Installation (Cross-Platform)
```bash
# Download wrapper
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios

# 1. Initialize a new project
./akios init my-project
cd my-project

# 2. List available templates
./akios templates list

# 3. Run an example workflow
./akios run templates/hello-workflow.yml

# 4. Check system status
./akios status

# 5. Clean up old runs (optional)
./akios clean

# 6. Export audit proof
./akios audit export --format json --output proof.json
```

## Getting Help

### Native Installation
```bash
# Show all available commands
akios --help

# Show command-specific help
akios status --help
akios templates --help
akios clean --help

# Show version
akios --version
```

### Docker Installation
```bash
# Show wrapper help
./akios --help

# Show CLI help (same as native)
./akios --help  # (after cd into project)
```

## Security & Design

### Native Linux (Maximum Security)
All commands execute within the AKIOS security cage:
- **Kernel-level sandboxing** with cgroups v2 and seccomp-bpf
- **Cryptographic audit logging** of all operations
- **Automatic PII redaction** in outputs
- **Cost controls** and resource limits

### Docker (Strong Security)
Commands run inside Docker containers with:
- **Container isolation** and security policies
- **Same cryptographic audit logging**
- **Same automatic PII redaction**
- **Same cost controls and resource limits**

**Both deployment methods provide strong security** - Native offers maximum security, Docker offers reliable cross-platform security.

---

For more information, see the [AKIOS Documentation](../README.md#documentation) or run:
- `akios --help` (native installation)
- `./akios --help` (Docker installation)

