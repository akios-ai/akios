# AKIOS v1.0 CLI Reference
**Document Version:** 1.0  
**Date:** 2026-01-25  

## 🚀 Three Ways to Run AKIOS

AKIOS V1.0.O supports three deployment methods:

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
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/akios
chmod +x akios
./akios init my-project
cd my-project
./akios run templates/hello-workflow.yml
```
**Requirements**: Docker Desktop (works on Linux, macOS, Windows)
**Benefits**: Smart caching, progress feedback, optimized for performance

### Direct Docker (Emergency Fallback)
```bash
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.3 init my-project
cd my-project
# Create wrapper script
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.3 "$@"' > akios
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
```

This creates:
- `config.yaml` - Configuration file
- `templates/` - Directory with example workflow templates
- `.env` - Environment variables file with real API keys (NEVER commit)
- `.env.example` - Template file with placeholder keys (safe to commit)
- `data/` - Input/output directories with sample data for testing
- `audit/` - Security audit logs

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

### `akios templates list` - List Available Templates

Show all available workflow templates with descriptions.

```bash
akios templates list
```

Displays:
```
Available Templates
===================
🌐 hello-workflow.yml      Hello World Example - Basic AI workflow demonstration with LLM interaction (requires network)
🌐 document_ingestion.yml  Document Analysis Pipeline - Processes documents with PII redaction and AI summarization (requires network)
💾 batch_processing.yml    Secure Batch Processing - Multi-file AI analysis with cost tracking and PII protection (local only)
💾 file_analysis.yml       File Security Scanner - Analyzes files with security-focused AI insights (local only)
```

**Network Requirements:**
- 🌐 Templates marked with this icon require internet access for AI API calls
- 💾 Templates marked with this icon work offline with local processing only

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

# Dry run (validate without executing)
akios run workflow.yml --dry-run
```

**Options:**
- `--verbose, -v`: Enable detailed execution logging
- `--quiet, -q`: Suppress informational banners and non-error output
- `--real-api`: Enable real API mode with interactive API key setup (sets AKIOS_MOCK_LLM=0, network_access_allowed=true, prompts for missing keys)
- `--dry-run, -d`: Validate workflow without executing it
- `--force, -f`: Skip confirmation prompts for template switches
- `--debug`: Enable debug logging for troubleshooting

### `akios audit export` - Export Audit Reports

Export cryptographic audit reports in JSON format with Merkle root integrity verification.

**Requires:** `audit_export_enabled: true` in `config.yaml`.

```bash
# Export latest audit as JSON (auto-generated filename)
akios audit export

# Export with custom filename
akios audit export --output audit-report.json

# Export specific task
akios audit export --task workflow-123 --output audit.json
```

**Options:**
- `--task, -t`: Specific task ID to export (default: latest)
- `--format, -f`: Export format: json (default: json)
- `--output, -o`: Output file path (default: auto-generated timestamp filename)

### `akios logs` - View Execution Logs

Show recent workflow execution logs.

```bash
# Show recent logs
akios logs

# Show logs for specific task
akios logs --task workflow-123

# Filter by log level
akios logs --level ERROR
```

**Options:**
- `--task, -t`: Filter by specific task ID
- `--level, -l`: Filter by log level (INFO, ERROR, etc.)

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
- `--budget, -b`: Show detailed budget tracking and spending breakdown
- `--json, -j`: Output in machine-readable JSON format
- `--verbose, -v`: Show detailed technical information and metrics
- `--security, -s`: Show detailed security status and active protections
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
- `--json, -j`: Output in machine-readable JSON format
- `--verbose, -v`: Show detailed technical information and metrics

### `akios clean` - Clean Project Data

Remove old workflow runs and free up disk space while preserving recent data.

```bash
# Clean runs older than 7 days (default)
akios clean --old-runs

# Clean runs older than 30 days
akios clean --old-runs 30

# See what would be cleaned without deleting
akios clean --old-runs 7 --dry-run

# Get JSON output for scripting
akios clean --old-runs 7 --json
```

**Options:**
- `--old-runs DAYS`: Remove runs older than DAYS (default: 7)
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
- `--type, -t`: Report type (basic, detailed, executive) - default: basic
- `--format, -f`: Export format (json, txt) - default: json
- `--output, -o`: Output file path (default: auto-generated filename)

**Report Types:**
- `basic`: Security validation summary and compliance status
- `detailed`: Includes technical details and audit events
- `executive`: High-level summary for management reporting

### `akios output` - Manage Workflow Outputs

Manage and organize workflow outputs with advanced file operations.

```bash
# Show all output files and directories
akios output

# List outputs for specific workflow
akios output --workflow hello-workflow.yml

# Clean old outputs (keep last 10 runs)
akios output clean --keep 10

# Archive outputs to compressed file
akios output archive --output archive-2026-01-24.tar.gz

# Export outputs in structured format
akios output export --format json --output outputs.json
```

**Options:**
- `--workflow, -w`: Filter by specific workflow name
- `--clean, -c`: Clean old outputs (specify --keep to set retention)
- `--keep, -k`: Number of recent runs to keep (default: 10)
- `--archive, -a`: Create compressed archive of outputs
- `--export, -e`: Export output metadata in specified format
- `--format, -f`: Export format (json, csv, txt)
- `--output, -o`: Output file path for export/archive operations

**Features:**
- **Automatic Organization**: Outputs organized in timestamped directories
- **Retention Management**: Configurable cleanup of old runs
- **Archive Support**: Compress and backup workflow outputs
- **Metadata Export**: Structured data about all workflow executions

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
akios clean --old-runs

# 6. Export audit proof
akios audit export --format json --output proof.json
```

### Docker Installation (Cross-Platform)
```bash
# Download wrapper
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/akios
ls -la akios && file akios  # Verify download (shell script)
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
./akios clean --old-runs

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

For detailed design constraints and scope limitations, see [CLI Scope & Boundaries](cli-scope-boundaries.md).

---

For more information, see the [AKIOS Documentation](../README.md#documentation) or run:
- `akios --help` (native installation)
- `./akios --help` (Docker installation)

