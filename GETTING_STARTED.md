# 🚀 AKIOS v1.0 - Get Started in 3 Minutes
**Document Version:** 1.0  
**Date:** 2026-01-25  

**Secure AI workflows made simple.**

## 🎯 Choose Your Installation

**AKIOS supports two deployment methods - pick what's best for you:**

### 🐧 **Pip Package** (Recommended - Python Developers)
**Native Python installation with full ecosystem integration**
```bash
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Other users (Ubuntu 20.04/22.04, macOS, Windows):
pip install akios

# Or install a specific version:
pip install akios==1.0.4

# Verify installation
akios --version
akios init my-project
```

**Perfect for:** Developers, CI/CD pipelines, custom extensions, full Python ecosystem access

### 🐳 **Docker** (Recommended - Teams & Cross-Platform)
**Containerized deployment works everywhere - no Python/dependencies needed**
```bash
# Pull the Docker image
docker pull akiosai/akios:v1.0.4

# Initialize a new project
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.4 init my-project

# Run workflows
cd my-project
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.4 run templates/hello-workflow.yml
```

**OR use the wrapper script for easier commands:**
```bash
# Create wrapper script (one-time setup)
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/akios
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

### 1. Install AKIOS
```bash
# Using pip (most systems)
pip install akios

# OR using pipx (Ubuntu 24.04+ recommended)
sudo apt install pipx
pipx install akios
```

### 2. Create Your Project
```bash
# Initialize a new project
akios init my-project
cd my-project
```

### 3. Configure API Access

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

### 4. Run Your First Workflow
```bash
# See available templates
akios templates list

# Run a pre-built AI workflow
akios run templates/hello-workflow.yml
```

**🎉 Success!** You'll see real AI output and security features in action.

### 5. Explore More (Optional)
```bash
# Check project status anytime
akios status

# View detailed security information
akios status --security

# Clean up old runs when disk space gets low
akios clean --old-runs
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

*AKIOS v1.0 - Where AI meets unbreakable security* 🛡️🤖
