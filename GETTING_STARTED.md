# 🚀 AKIOS v1.0 - Get Started in 3 Minutes
**Document Version:** 1.0  
**Date:** 2026-01-25  

**Secure AI workflows made simple.**

## 🎯 Choose Your Installation

**AKIOS supports four deployment methods - pick what's best for you:**

### 🚀 **Standalone Binary** (Recommended - Zero Setup)
**Download and run immediately - no Python or Docker required!**
```bash
# Download from https://github.com/akios-ai/akios/releases
# Linux: akios-linux-x64 | macOS: akios-macos-universal | Windows: akios-windows-x64.exe

# Make executable and run
chmod +x akios-linux-x64  # Skip on Windows
./akios-linux-x64 init my-project
```

**Perfect for:** Quick evaluation, air-gapped environments, non-technical users

### 🐧 **Pip Package** (Python Developers)
**Full Python ecosystem integration with maximum security**
```bash
pip install akios
akios init my-project
```

**Perfect for:** Custom extensions, CI/CD pipelines, Python development

### 🐳 **Docker** (Cross-Platform Teams)
**Containerized deployment works everywhere**
```bash
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/akios
ls -la akios && file akios  # Verify download (~3.4KB shell script)
chmod +x akios
./akios init my-project
```

**Perfect for:** Teams using containers, development environments
**Optimized for:** Fast subsequent runs with smart caching

**Refresh the image on demand:**
```bash
AKIOS_FORCE_PULL=1 ./akios status
```

### 🚨 **Direct Docker** (Emergency Fallback)
**Use Docker directly when wrapper script download fails**
```bash
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.3 init my-project
cd my-project
# Create wrapper script for future use
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.3 "$@"' > akios
chmod +x akios
./akios run templates/hello-workflow.yml
```

**Perfect for:** Network issues, GitHub unavailable, emergency recovery

**This guide shows Binary installation** - see [README.md](README.md) for all options.

---

## ⚡ Quick Start (Binary)

### 1. Download & Setup
```bash
# Visit https://github.com/akios-ai/akios/releases
# Download your platform's binary:
# - Linux x64: akios-linux-x64
# - Linux ARM64: akios-linux-arm64
# - macOS: akios-macos-universal
# - Windows: akios-windows-x64.exe

# Make executable (skip on Windows)
chmod +x akios-linux-x64
```

### 2. Create Your Project
```bash
# Initialize a new project
./akios-linux-x64 init my-project
cd my-project
```

### 3. Configure API Access

AKIOS includes an interactive setup wizard that makes configuration effortless.

```bash
# The setup wizard runs automatically on your first workflow
./akios-linux-x64 run templates/hello-workflow.yml

# Or run it manually anytime
./akios-linux-x64 setup
# Use --force to re-run setup: ./akios-linux-x64 setup --force
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
../akios-linux-x64 templates list

# Run a pre-built AI workflow
../akios-linux-x64 run templates/hello-workflow.yml
```

**🎉 Success!** You'll see real AI output and security features in action.

### 5. Explore More (Optional)
```bash
# Check project status anytime
../akios-linux-x64 status

# View detailed security information
../akios-linux-x64 status --security

# Clean up old runs when disk space gets low
../akios-linux-x64 clean --old-runs
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
