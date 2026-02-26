# 🚀 AKIOS v1.2.1 - Get Started in 3 Minutes
**Document Version:** 1.2.1  
**Date:** 2026-02-23  

**Secure AI workflows made simple.**

## 🎯 Choose Your Installation

**AKIOS supports two deployment methods - pick what's best for you:**

### 🐧 **Pip Package** (Recommended - Python Developers)
**Native Python installation with full ecosystem integration**

⚠️ **LINUX USERS: Pre-install system packages BEFORE `pip install`**
```bash
# Ubuntu/Debian - REQUIRED for kernel-hard security
sudo apt-get update
sudo apt-get install libseccomp-dev python3-seccomp

# Fedora/RHEL - REQUIRED for kernel-hard security
sudo dnf install libseccomp-devel python3-seccomp
```

```bash
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Other users (Ubuntu 20.04/22.04, macOS, Windows):
pip install akios

# Or install a specific version:
pip install akios==1.2.1

# Verify installation
akios --version
akios init my-project
```

**Perfect for:** Developers, CI/CD pipelines, custom extensions, full Python ecosystem access

### 🐳 **Docker** (Recommended - Teams & Cross-Platform)
**Containerized deployment works everywhere - no Python/dependencies needed**
```bash
# Pull the Docker image
docker pull akiosai/akios:v1.2.1

# Initialize a new project
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.2.1 init my-project

# Run workflows
cd my-project
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.2.1 run templates/hello-workflow.yml
```

**OR use the wrapper script for easier commands:**
```bash
# Create wrapper script (one-time setup)
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios

# Now use ./akios like native installation
./akios init my-project
cd my-project
./akios run templates/hello-workflow.yml

# Force refresh image (pull latest)
AKIOS_FORCE_PULL=1 ./akios status
```

**Perfect for:** Teams using containers, cloud deployments, CI/CD, zero-setup environments

---

## ⚡ Quick Start (Pip)

### 1. Install System Dependencies (Linux Only)
⚠️ **This is required for full security. Skip if using Docker.**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install libseccomp-dev python3-seccomp

# Fedora/RHEL
sudo dnf install libseccomp-devel python3-seccomp
```

### 2. Install AKIOS
```bash
# Using pip (most systems)
pip install akios

# OR using pipx (Ubuntu 24.04+ recommended)
sudo apt install pipx
pipx install akios

# For maximum security on Linux, run workflows with sudo:
# sudo akios run templates/hello-workflow.yml
```

### 3. Security Cage Quick Start

**AKIOS provides a security cage for AI workflows:**

```bash
# Activate security cage (PII redaction, network lock, audit)
akios cage up

# Check security status
akios cage status

# Run your workflow
akios run workflow.yml

# Deactivate cage and destroy all session data
akios cage down

# Secure overwrite with multiple passes (GDPR Art. 17)
akios cage down --passes 3

# Fast mode — skip secure overwrite (dev only)
akios cage down --fast

# OR keep data for debugging (dev mode only)
akios cage down --keep-data

# Ablation mode — disable specific protections for benchmarking
akios cage up --no-pii --no-audit --no-budget
```

**⚠️ WARNING:** `cage down` permanently destroys:
- `audit/` — All audit logs and Merkle proofs
- `data/output/` — All workflow outputs

**Input data (`data/input/`) is preserved.**

### 4. HTTPS Domain Whitelist (Optional)

**Allow HTTP agent to access specific domains while maintaining security:**

```yaml
# config.yaml
network_access_allowed: true
allowed_domains:
  - api.salesforce.com
  - api.mycompany.com
```

**Or via environment variable:**
```bash
export AKIOS_ALLOWED_DOMAINS="api.salesforce.com,api.example.com"
```

**Note:** LLM APIs (OpenAI, Anthropic, Grok, Mistral, Gemini) always bypass the whitelist.

### 3. Create Your Project
```bash
# Initialize a new project
akios init my-project
cd my-project
```

### 4. Configure API Access

AKIOS includes an interactive setup wizard that makes configuration effortless.

```bash
# The setup wizard runs automatically on your first workflow
akios run templates/hello-workflow.yml

# Or run it manually anytime
akios setup
# Use --force to re-run setup: akios setup --force
```

The wizard guides you through:
- Choosing your AI provider (OpenAI, Anthropic, Grok, Mistral, or Gemini)
- Selecting your preferred model (gpt-4o, claude-3-sonnet, grok-3, etc.)
- Entering your API key with real validation
- Setting budget and token limits
- Configuring security and network settings
- Testing that everything works with a real API call

For manual configuration, copy and edit the environment file:
```bash
cp .env.example .env
# Edit .env and add your API key
```

### 5. Run Your First Workflow
```bash
# See available templates
akios templates list

# Run a pre-built AI workflow
akios run templates/hello-workflow.yml
```

**🎉 Success!** You'll see real AI output and security features in action.

### 6. Explore More (Optional)
```bash
# Check project status anytime
akios status

# View detailed security information
akios status --security

# View budget dashboard and cost tracking
akios status --budget

# Validate a workflow file before running
akios workflow validate workflow.yml

# View audit ledger statistics
akios audit stats

# Rotate audit log (archive + fresh start)
akios audit rotate

# Scan a file for PII
akios protect scan data/input/document_example.txt

# Scan inline text for PII (auto-detected or use --text flag)
akios protect scan --text "Patient John Smith, NPI 1234567893"

# Preview the exact prompt sent to the LLM
akios protect show-prompt workflow.yml

# Make secure HTTP requests (requires cage up + domain whitelist)
akios http GET https://api.example.com/data

# Clean up old runs when disk space gets low
akios clean
```

---

## 🔑 Get API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Grok**: https://console.x.ai/
- **Mistral**: https://console.mistral.ai/
- **Gemini**: https://makersuite.google.com/app/apikey

**Free tiers available for testing!**

---

## 📚 Learn More

**Ready to master AKIOS?**
- 📖 **[Complete Tutorial](docs/quickstart.md)** - Step-by-step learning guide
- 📋 **[Project README](README.md)** - Your project documentation
- 🛠️ **[CLI Reference](docs/cli-reference.md)** - All commands and options

**Need help?** Check the audit logs in `audit/audit_events.jsonl` or create a GitHub issue.

---

*AKIOS v1.2.1 - Where AI meets unbreakable security* 🛡️🤖
