# AKIOS Comprehensive Quick Start Guide
**Document Version:** 1.6  
**Date:** 2026-02-21  

**Master AKIOS v1.0.8 - From Beginner to Advanced User**

*Complete tutorial: 15-30 minutes*

---

## 📋 Table of Contents

1. [What is AKIOS?](#-what-is-akios)
2. [Installation & Setup](#-installation--setup)
3. [Your First Workflow](#-your-first-workflow)
4. [Understanding Project Structure](#-understanding-project-structure)
5. [Managing Templates & Cleanup](#️-managing-templates--cleanup)
6. [Workflows vs Templates Deep Dive](#-workflows-vs-templates-deep-dive)
7. [Creating Custom Workflows](#-creating-custom-workflows)
8. [Advanced Configuration](#-advanced-configuration)
9. [Security & Audit System](#-security--audit-system)
10. [Troubleshooting & Best Practices](#-troubleshooting--best-practices)
11. [Next Steps & Resources](#-next-steps--resources)

---

## 🎯 What is AKIOS?

AKIOS (AI Knowledge & Intelligence Operating System) is a **security-first runtime** for AI agent workflows that provides:

### 🛡️ **Kernel-Level Security**
- **Sandboxing**: Complete process isolation (kernel-hard on native Linux, strong policy-based in Docker)
- **PII Protection**: Automatic sensitive data redaction
- **Audit Trails**: Cryptographic logging of all operations
- **Resource Controls**: CPU, memory, and cost limits

### 🤖 **Multi-Provider AI Support**
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3.5-haiku, Claude-3.5-sonnet
- **Grok**: Real-time knowledge and reasoning
- **Mistral**: Efficient inference, strong reasoning
- **Gemini**: Multimodal capabilities, strong coding
- **Automatic switching** based on your configuration

### ⚡ **Production-Ready Features**
- **Real AI outputs** (not placeholder text)
- **Error handling** and retry logic
- **YAML-based workflows** (human-readable)
- **Docker deployment** (cross-platform)

**Perfect for**: AI developers, data scientists, researchers, and organizations requiring secure, auditable AI execution.

---

## 🛠️ Installation & Setup

### Choose Your Installation Method

AKIOS supports three deployment methods - choose the best one for your use case:

| Method | Best For | Setup Time | Security Level |
|--------|----------|------------|----------------|
| **Pip Package** ⭐ | Python developers | 2 minutes | Full kernel-hard security (with sudo on Linux) |
| **Docker** | Cross-platform teams | 1 minute | Strong policy-based security |
| **Direct Docker** | Emergency fallback when wrapper fails | 1 minute | Strong policy-based security |

#### � **Pip Package** (Recommended for Most Users)
**Maximum security on native Linux:**
**IMPORTANT: Linux Users Must Install System Packages First**
```bash
# Ubuntu/Debian - REQUIRED BEFORE pip install
sudo apt-get update
sudo apt-get install libseccomp-dev python3-seccomp

# Fedora/RHEL - REQUIRED BEFORE pip install
sudo dnf install libseccomp-devel python3-seccomp
```

Then install AKIOS:```bash
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

akios --version
akios init my-project
cd my-project
akios run templates/hello-workflow.yml
```

> **📦 Version Note:** `pip install akios` installs the latest stable version (currently v1.0.8). 
> For specific versions: `pip install akios==1.0.8`.

**Benefits:** Full kernel-hard security, Python ecosystem integration.

> *Note: The "Pip Package" section below provides equivalent instructions with additional detail.*

#### 🐧 **Pip Package** (For Python Developers)
**Maximum security on native Linux:**
```bash
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

akios --version
akios init my-project
cd my-project

# For maximum security on Linux, run with sudo for kernel-hard protection:
# sudo akios run templates/hello-workflow.yml
# Without sudo, AKIOS gracefully falls back to policy-based mode with warnings

akios run templates/hello-workflow.yml
```

> **📦 Version Note:** `pip install akios` installs the latest stable version (currently v1.0.8). 
> For specific versions: `pip install akios==1.0.8`.
> **🛡️ Security Note:** On Linux, `pip install akios` includes the seccomp module for kernel-hard security. Run with `sudo` for full protection.

**Benefits:** Full kernel-hard security (with sudo), Python ecosystem integration.

#### 🐳 **Docker** (Cross-Platform Teams)
**Works on Linux, macOS, and Windows:**
```bash
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios
./akios --help
```

**Benefits:** Cross-platform consistency, containerized deployment, smart caching for fast subsequent runs.

**Refresh the image when needed:**
```bash
AKIOS_FORCE_PULL=1 ./akios status
```

#### 🚨 **Direct Docker** (If Wrapper Script Fails)
**Emergency fallback when the wrapper script download fails:**
```bash
# Use Docker directly (works even if curl/network fails)
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.8 init my-project
cd my-project
# Create wrapper script for future use
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.8 "$@"' > akios
chmod +x akios
./akios run templates/hello-workflow.yml
```

**Benefits:** Works without network access, emergency recovery when wrapper download fails.

**This tutorial uses Docker for cross-platform compatibility** - see [CLI Reference](cli-reference.md) for all installation methods.

### Prerequisites
- **Docker Desktop** (for macOS/Windows) or Docker Engine (Linux)
- **API key** from one AI provider (OpenAI, Anthropic, Grok, Mistral, or Gemini)

### Step 1: Download AKIOS Wrapper

```bash
# Download the cross-platform wrapper script
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios

# Verify it works
./akios --help
```

### Step 2: Initialize Your Project

```bash
# Create a new AKIOS project
./akios init my-first-project

# Navigate to your project
cd my-first-project

# Check what was created
ls -la
```

**Note:** The first run can take longer due to image pull and dependency setup. Later runs are faster.

**What you'll see:**
```
drwxr-xr-x  my-first-project/
├── README.md           # Project documentation
├── .env                 # Configuration (API keys)
├── config.yaml         # AKIOS settings
├── .gitignore          # Git ignore rules
├── workflows/          # Your custom workflows (empty)
├── templates/          # Pre-built examples (4 templates)
├── data/               # Input/output data
│   ├── input/          # Data for workflows
│   └── output/         # Workflow results
└── audit/              # Security logs
```

### Step 3: Configure API Access

AKIOS includes an interactive setup wizard that makes configuration effortless.

#### Guided Setup (Recommended)

The setup wizard automatically detects first-time usage and guides you through configuration.

```bash
# The setup wizard runs automatically on your first command
./akios run templates/hello-workflow.yml

# Or run it manually anytime
./akios setup
# Use --force to re-run setup: ./akios setup --force
```

The wizard guides you through:
- Choosing your AI provider (OpenAI, Anthropic, Grok, Mistral, or Gemini)
- Selecting your preferred model (gpt-4o, claude-3.5-sonnet, grok-3, etc.)
- Entering your API key with real validation
- Setting budget and token limits
- Configuring security and network settings
- Testing that everything works with a real API call

**What you'll see:**
```
🎉 Welcome to AKIOS v1.0! Let's set up your first workflow.

🚀 How would you like to use AKIOS?
1. Try with mock data (no API key needed — instant setup)
2. Use real AI providers (requires API key — full AI power)
3. Skip setup (use mock mode by default — configure later)

Enter your choice (1-3) [default: 1]: 2

🤖 Choose your AI Provider:
1. OpenAI (GPT) — Most popular
2. Anthropic (Claude) — High safety
3. xAI (Grok) — Helpful & truthful
4. Mistral — Fast open-source
5. Google (Gemini) — Multimodal

Enter your choice (1-5): 3
[Wizard continues with API key setup, validation, and configuration...]
```

#### Manual Configuration

For manual setup or advanced configuration:

**Environment Setup:**
- `.env.example` - Template file with placeholder keys (safe to commit)
- `.env` - Your working file with real API keys (NEVER commit this!)

```bash
# Copy the template to create your working file
cp .env.example .env

# Then edit .env with your real API keys
```

**Edit `.env` file:**
```bash
# Choose ONE provider and uncomment the lines:

# For OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# For Anthropic
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# For Grok (recommended for getting started)
GROK_API_KEY=xai-your-grok-key-here

# For Mistral
# MISTRAL_API_KEY=your-mistral-key-here

# For Gemini
# GEMINI_API_KEY=your-gemini-key-here

# Optional: Set defaults
AKIOS_LLM_PROVIDER=grok
AKIOS_LLM_MODEL=grok-3
```

**💡 Tip:** The setup wizard is the easiest way to get started. It handles all the configuration details and validates your setup works correctly.

**Get API keys from:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Grok**: https://console.x.ai/

---

## 🎮 Your First Workflow

### Basic Hello World

```bash
# From inside your project directory
./akios run templates/hello-workflow.yml
```

**Expected Output:**
```
📄 Loading configuration from .env
🐳 Using Docker for cross-platform security
*** CRITICAL SECURITY DOWNGRADE ***
Container detected - NO KERNEL-HARD SECCOMP-BPF available!
Security: Policy-based isolation active
✓ PII detection available
🤖 Step 1 LLM Output: "Greetings, human! I'm an AI running in AKIOS's secure cage..."
Workflow completed
Executed 3 steps in 3.50s
```

**Check the results:**
```bash
# View the generated content
cat data/output/run_*/hello-ai.txt

# Check security audit logs
head -5 audit/audit_events.jsonl
```

### Understanding the Output

The workflow performed 3 steps:
1. **LLM Call**: Generated AI response using your configured provider
2. **File Write**: Saved the response to `data/output/run_*/hello-ai.txt`
3. **File Read**: Verified the file was created successfully

**Note**: AKIOS organizes outputs in timestamped directories (like `run_20240124_143022`) to keep each workflow run separate and prevent accidental overwrites. The `run_*` wildcard in commands lets you easily access the latest results.

---

## 📁 Understanding Project Structure

AKIOS projects follow a consistent structure:

```
your-project/
├── README.md           # 📖 This guide + project docs
├── .env                 # 🔑 API keys & configuration (edit this!)
├── .env.example         # 📋 Template with placeholder keys (copy to .env)
├── config.yaml         # ⚙️  AKIOS runtime settings
├── .gitignore          # 🚫 Git ignore rules
│
├── workflows/          # 🛠️  YOUR custom workflows (start empty)
├── templates/          # 📚 Pre-built workflow examples
│   ├── hello-workflow.yml
│   ├── document_ingestion.yml
│   └── ...
│
├── data/               # 📊 Workflow data
│   ├── input/          # 📥 Input files for workflows
│   └── output/         # 📤 Generated results
│
└── audit/              # 🔐 Security audit logs
    └── audit_events.jsonl
```

### Key Directories Explained

**`workflows/`** - Your development workspace
- Initially empty
- Place for custom workflows
- Safe to edit and version control

**`templates/`** - Reference examples
- Pre-built, working workflows
- Don't modify these files
- Use as starting points for custom workflows

**`data/`** - Input/Output management
- `input/`: Files your workflows can read
- `output/`: Results generated by workflows

**`audit/`** - Security compliance
- Complete log of all operations
- Cryptographic integrity
- Regulatory compliance (SOX/HIPAA/GDPR)

### Exploring Your Data

Use the `files` command to see what input and output files are available:

```bash
# See all available files
./akios files

# See only input files
./akios files input

# See only output files
./akios files output
```

This helps you understand what data is available for your workflows and track your results.

---

## 🗂️ Managing Templates & Cleanup

### Discovering Available Templates

AKIOS comes with several pre-built workflow templates. Use the `templates list` command to see what's available:

```bash
# See all available templates with descriptions
./akios templates list
```

**Output:**
```
Available Templates
===================
hello-workflow.yml        Hello World Example - Basic AI workflow demonstration with LLM interaction
document_ingestion.yml    Document Analysis Pipeline - Processes documents with PII redaction and AI summarization
batch_processing.yml      Secure Batch Processing - Multi-file AI analysis with cost tracking and PII protection
file_analysis.yml         File Security Scanner - Analyzes files with security-focused AI insights
```

### Keeping Your Project Clean

Over time, workflow runs accumulate in the `data/output/` directory. Use the `clean` command to remove old runs:

```bash
# Clean up old runs (older than 7 days by default)
akios clean

# Or specify a different age (e.g., 30 days)
akios clean --old-runs 30

# Remove runs older than 30 days
./akios clean --old-runs 30

# See what would be cleaned (dry run)
./akios clean --old-runs 7 --dry-run
```

**What gets cleaned:**
- ✅ Old `data/output/run_YYYY-MM-DD_HH-MM-SS/` directories
- ❌ **Never touches** audit logs or configuration

**Safety feature:** The `clean` command only works from inside a project directory, preventing accidental cleanup.

---

## 🔄 Workflows vs Templates Deep Dive

### The Philosophy

AKIOS separates **examples** from **your work** to maintain clean development practices:

| Aspect | `templates/` | `workflows/` |
|--------|-------------|-------------|
| **Purpose** | Reference examples | Your custom development |
| **Modify?** | ❌ No (breaks examples) | ✅ Yes (your code) |
| **Version Control** | Template updates | Your workflow versions |
| **Use Case** | Learning, testing | Production, customization |

### Practical Workflow Development

```bash
# 1. Find a suitable template
ls templates/
# hello-workflow.yml, document_ingestion.yml, batch_processing.yml

# 2. Copy to workflows directory
cp templates/hello-workflow.yml workflows/my-greeting-workflow.yml

# 3. Customize for your needs
nano workflows/my-greeting-workflow.yml

# 4. Test your custom workflow
./akios run workflows/my-greeting-workflow.yml

# 5. Iterate and improve
# Edit → Test → Repeat
```

### Template Categories

**Basic Workflows:**
- `hello-workflow.yml` - Simple AI chat with file output

**Document Processing:**
- `document_ingestion.yml` - Analyze documents with AI
- `file_analysis.yml` - Extract insights from files

**Batch Processing:**
- `batch_processing.yml` - Multi-file AI analysis with cost tracking

---

## 🛠️ Creating Custom Workflows

### Workflow Anatomy

AKIOS workflows are YAML files with this structure:

```yaml
name: "My Custom Workflow"
description: "What this workflow does"

steps:
  - step: 1
    agent: llm
    config:
      provider: "${AKIOS_LLM_PROVIDER:-grok}"
      model: "${AKIOS_LLM_MODEL:-grok-3}"
    action: complete
    parameters:
      prompt: |
        Your AI instructions here...
        Use variables: ${previous_output}

  - step: 2
    agent: filesystem
    action: write
    parameters:
      path: "data/output/my-result.txt"
      content: "${step_1_output}"

  - step: 3
    agent: filesystem
    action: read
    parameters:
      path: "data/output/my-result.txt"
```

### Step-by-Step Tutorial: Custom Greeting Workflow

**Step 1: Copy a template**
```bash
cp templates/hello-workflow.yml workflows/personal-greeting.yml
```

**Step 2: Edit the workflow**
```yaml
name: "Personal Greeting Workflow"
description: "Creates personalized greetings using AI"

steps:
  - step: 1
    agent: llm
    config:
      provider: "${AKIOS_LLM_PROVIDER:-grok}"
      model: "${AKIOS_LLM_MODEL:-grok-3}"
    action: complete
    parameters:
      prompt: |
        Create a personalized, creative greeting for a user named "Alex".
        Make it fun, welcoming, and mention that you're running in AKIOS.
        Keep it under 100 words.

  - step: 2
    agent: filesystem
    action: write
    parameters:
      path: "data/output/alex-greeting.txt"
      content: "${step_1_output}"

  - step: 3
    agent: filesystem
    action: read
    parameters:
      path: "data/output/alex-greeting.txt"
```

**Step 3: Run and test**
```bash
./akios run workflows/personal-greeting.yml
cat data/output/run_*/alex-greeting.txt
```

### Advanced Workflow Patterns

**Conditional Logic:**
```yaml
steps:
  - step: 1
    agent: llm
    action: complete
    parameters:
      prompt: "Analyze this text: ${input_text}"
    condition: "${input_text}"  # Only run if input_text is provided

  - step: 2
    agent: filesystem
    action: write
    parameters:
      path: "data/output/analysis.txt"
      content: "${step_1_output}"
```

**Multiple AI Calls:**
```yaml
steps:
  - step: 1
    agent: llm
    config:
      provider: "openai"
      model: "gpt-4"
    action: complete
    parameters:
      prompt: "Summarize this document"

  - step: 2
    agent: llm
    config:
      provider: "anthropic"
      model: "claude-3.5-sonnet"
    action: complete
    parameters:
      prompt: "Based on this summary: ${step_1_output}, generate recommendations"
```

---

## ⚙️ Advanced Configuration

### Environment Variables

**Core Settings:**
```bash
# AI Provider (required)
AKIOS_LLM_PROVIDER=grok          # openai, anthropic, grok
AKIOS_LLM_MODEL=grok-3          # Model name

# Security (optional)
AKIOS_MOCK_LLM=0                # 1 for testing without API calls
AKIOS_PII_REDACTION_ENABLED=1   # Enable/disable PII protection

# Performance (optional)
AKIOS_MAX_TOKENS_PER_CALL=1000  # Token limits
AKIOS_BUDGET_LIMIT_PER_RUN=1.0  # Cost limits in USD
```

### Config.yaml Settings

**Security Controls:**
```yaml
# Sandbox settings
sandbox_enabled: true
cpu_limit: 0.8          # 80% CPU limit
memory_limit_mb: 256    # Memory limit

# Audit settings
audit_enabled: true
audit_compression: true

# PII Protection
pii_redaction_enabled: true
redaction_strategy: "mask"  # mask, remove, hash
```

### Multi-Environment Setup

**Development:**
```bash
# .env.local (for development)
AKIOS_MOCK_LLM=1
AKIOS_LLM_PROVIDER=grok
```

**Production:**
```bash
# .env (for production)
AKIOS_MOCK_LLM=0
AKIOS_LLM_PROVIDER=openai
AKIOS_LLM_MODEL=gpt-4
AKIOS_BUDGET_LIMIT_PER_RUN=5.0
```

---

## Security & Audit System

### Security Cage

AKIOS v1.0.8 introduces the **Security Cage** — a controlled environment that activates all protections during workflow execution and destroys all data when deactivated.

**Activate the cage:**
```bash
# Turn on all protections
akios cage up

# Check security posture
akios cage status

# Run full diagnostics
akios doctor
```

**Cage bypass tests (all blocked):**
```bash
# Network: external calls blocked
curl https://httpbin.org/get  # → Connection blocked

# Budget: kill-switch enforced
AKIOS_BUDGET_LIMIT_PER_RUN=0.0001 akios run workflow.yml --force  # → Halted

# Commands: only approved agents can execute
# No arbitrary shell execution permitted inside the cage
```

**Deactivate the cage:**
```bash
# Full shutdown — destroys ALL session data (default)
akios cage down

# Dev mode — relax protections, keep data for debugging
akios cage down --keep-data
```

### PII Protection

**Scan files for sensitive data before processing:**
```bash
# Scan a file for PII (SSN, names, emails, NPI numbers, DEA numbers, medical record numbers, etc.)
akios protect scan data/input/patient.txt

# Preview the interpolated + redacted prompt the LLM will receive
akios protect show-prompt templates/healthcare.yml
```

PII markers appear in **magenta** in terminal output: `«SSN»`, `«NAME»`, `«EMAIL»`, `«US_NPI»`, `«US_DEA»`, `«MEDICAL_RECORD_NUMBER»`, etc. Original text appears in red for contrast.

### Workflow Output

**Retrieve structured results for CI/CD integration:**
```bash
# Get latest execution as deployable JSON
akios output latest

# List all outputs
akios output list

# View execution timeline
akios timeline
```

### Security Architecture

AKIOS provides **defense-in-depth security**:

**Container Level:**
- Docker isolation with restricted capabilities
- No privileged access
- Network controls and resource limits

**Application Level:**
- Command allowlisting
- Path restrictions
- PII automatic detection and masking (inputs + outputs)
- Output sanitization for AI-generated content

**Audit Level:**
- Complete operation logging
- Cryptographic integrity
- Tamper-evident records

### Understanding Audit Logs

**View recent activity:**
```bash
# Last 10 audit events
tail -10 audit/audit_events.jsonl | jq -r '.timestamp + " " + .action + " (" + .agent + ")"'

# Search for specific operations
grep "llm" audit/audit_events.jsonl | jq -r '.metadata.cost_incurred'

# Cost analysis
jq -r 'select(.metadata.cost_incurred) | .metadata.cost_incurred' audit/audit_events.jsonl | awk '{sum += $1} END {print "Total cost: $" sum}'
```

**Audit Event Structure:**
```json
{
  "action": "complete",           // What happened
  "agent": "llm",                // Which component
  "hash": "abc123...",           // Cryptographic integrity
  "metadata": {                  // Operation details
    "cost_incurred": 0.00083,
    "execution_time": 2.1,
    "model": "grok-3"
  },
  "result": "success",           // Outcome
  "step": 1,                     // Workflow step
  "timestamp": "2024-01-03T...", // When
  "workflow_id": "workflow-name" // Unique ID
}
```

### Compliance Features

**Regulatory Standards Met:**
- **SOX**: Financial transaction audit trails
- **HIPAA**: Protected health data logging
- **GDPR**: Personal data processing records
- **PCI DSS**: Payment data security monitoring

**Compliance Benefits:**
- **Chain of custody** - Every operation traceable
- **Non-repudiation** - Cryptographic proof of execution
- **Temporal accuracy** - Nanosecond-precision timestamps
- **Data integrity** - SHA hash tamper detection

---

## 🐛 Troubleshooting & Best Practices

### FAQ - Frequently Asked Questions

**Q: I'm new to AKIOS. Where should I start?**
- **A:** Follow this guide from top to bottom! Start with Docker installation, then run the hello-workflow template. Everything is designed to work step-by-step.

**Q: Do I need Docker knowledge to use AKIOS?**
- **A:** The wrapper handles Docker for you. If the wrapper is unavailable, you can run direct Docker commands (shown above).

**Q: Which AI provider should I choose?**
- **A:** All five (OpenAI, Anthropic, Grok, Mistral, Gemini) work equally well. Choose based on your preferences:
  - OpenAI: Most popular, good for general tasks
  - Anthropic: Best for safety and reasoning
  - Grok: Real-time knowledge and humor
  - Mistral: Cost-effective, strong reasoning
  - Gemini: Multimodal capabilities, strong coding

**Q: Is AKIOS secure for production use?**
- **A:** Yes! AKIOS provides military-grade security with PII redaction, audit trails, and sandboxing. See the Security section for details.

**Q: How do I check if AKIOS security is working?**
- **A:** Run `./akios status --security` to see a detailed security dashboard showing all active protections, or `./akios status` for a security summary.

**Q: How do I monitor API costs and budgets?**
- **A:** Run `./akios status --budget` to see detailed spending breakdown, remaining budget, and cost tracking across all workflows.

**Q: What's the difference between mock mode and real API mode?**
- **A:** Mock mode (default) uses sample responses for testing without API costs. You'll see 🎭 mock mode indicators in status and workflow outputs. Real API mode (`AKIOS_MOCK_LLM=0`) calls actual AI providers and incurs costs.

**Q: Can I switch between different AI providers?**
- **A:** Yes! Just change the provider in your workflow YAML or set the `AKIOS_LLM_PROVIDER` environment variable. No code changes needed.

### Common Issues & Solutions

**❌ "API key not found"**
```bash
# Check if variable is set
echo $GROK_API_KEY

# Reload environment
source .env

# Or export manually
export GROK_API_KEY="your-key-here"
```

**❌ "Permission denied"**
```bash
# Ensure Docker is running
docker ps

# On Linux, check user permissions
groups | grep docker

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Log out and back in
```

**❌ "Container detected" message**
- This is normal! It shows AKIOS detected Docker environment
- You're getting policy-based security (strong protection)
- For kernel-hard security, use native Linux installation

**❌ Workflow fails with errors**
```bash
# Check audit logs for details
tail -5 audit/audit_events.jsonl | jq '.metadata.error'

# Common fixes:
# 1. Check API key is valid
# 2. Verify network connectivity
# 3. Check workflow YAML syntax
# 4. Ensure input files exist
```

### Performance Optimization

**Speed up workflows:**
```bash
# Use faster models
AKIOS_LLM_MODEL=grok-3  # Usually faster than gpt-4

# Reduce token limits
AKIOS_MAX_TOKENS_PER_CALL=500

# Cache Docker layers
docker system prune  # Clean unused images
```

**Cost optimization:**
```bash
# Set budget limits
AKIOS_BUDGET_LIMIT_PER_RUN=1.0

# Use efficient models
AKIOS_LLM_MODEL=gpt-3.5-turbo  # Cheaper than gpt-4

# Monitor usage
jq -r 'select(.metadata.cost_incurred) | .metadata.cost_incurred' audit/audit_events.jsonl | awk '{sum += $1} END {print "Total: $" sum}'
```

### Development Best Practices

**Workflow Development:**
```bash
# Start with templates
cp templates/hello-workflow.yml workflows/my-workflow.yml

# Test incrementally
./akios run workflows/my-workflow.yml

# Use version control
git add workflows/
git commit -m "Add custom greeting workflow"
```

**Error Handling:**
```yaml
steps:
  - step: 1
    agent: llm
    action: complete
    parameters:
      prompt: "Process this: ${input}"
    retry_count: 3
    timeout: 30
```

**Security Best Practices:**
- Store API keys securely (not in git)
- Use environment variables, not hardcoded keys
- Regularly review audit logs
- Set appropriate budget limits
- Keep AKIOS updated

---

## 🎯 Next Steps & Resources

### Continue Learning

**📚 Official Documentation:**
- `README.md` - Project-specific usage
- `docs/cli-reference.md` - Complete command reference
- `docs/configuration.md` - Advanced configuration
- `docs/deployment.md` - Production deployment

**🎓 Advanced Tutorials:**
- Multi-step workflow patterns
- API integration workflows
- Custom agent development
- Performance optimization

**🤝 Community Resources:**
- GitHub Issues - Bug reports and feature requests
- GitHub Discussions - Q&A and best practices
- Example workflow repository

### Production Deployment

**Docker (Cross-platform):**
```bash
# Build production image
docker build -t my-akios-app .

# Run with security
docker run --security-opt=no-new-privileges my-akios-app
```

**Native Linux (Maximum Security):**
```bash
# Install with full security features
pip install akios[agents]

# Run with kernel isolation
akios run workflows/production-workflow.yml
```

### Contributing

**Help improve AKIOS:**
- Report bugs and issues
- Suggest new features
- Contribute workflow templates
- Improve documentation

**Development Setup:**
```bash
git clone https://github.com/akios-ai/akios.git
cd akios
pip install -e .[dev]
```

---

## 🎉 Congratulations!

You've completed the comprehensive AKIOS tutorial! You now understand:

✅ **AKIOS architecture** and security model
✅ **Project setup** and configuration
✅ **Workflow development** from templates to custom
✅ **Multi-provider AI integration**
✅ **Security Cage** — cage up/down, PII scanning, data lifecycle
✅ **Audit system** and compliance features
✅ **Output management** — deployable JSON, timeline, budget
✅ **Troubleshooting** and best practices
✅ **Production deployment** strategies

**You're ready to build secure, auditable AI workflows with AKIOS!**

---

*AKIOS v1.0.8 - Where AI meets unbreakable security*

**Need help?** Run `akios doctor`, check the audit logs, or create a GitHub issue.
