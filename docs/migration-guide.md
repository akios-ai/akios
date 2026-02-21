# AKIOS Migration Guide
**Document Version:** 1.0  
**Date:** 2026-01-25  

**Upgrading from Previous Versions to v1.0 Hybrid Distribution**

AKIOS v1.0 features **hybrid distribution** - standalone binaries + pip packages. This guide helps you migrate from older versions while maintaining your existing workflows and configurations.

---

## Installation Options

### Option 1: Upgrade to Pip Package (Recommended)
```bash
# 1. Upgrade your existing installation
pip install --upgrade akios

# 2. Verify the upgrade
akios --version

# 3. Your existing workflows work unchanged
akios run workflow.yml
```

**Benefits:** Full kernel-hard security (Linux), Python ecosystem integration, easiest upgrade path.

### Option 2: Switch to Docker (Cross-Platform)
```bash
# 1. Download wrapper script
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios

# 2. Verify installation
./akios --version

# 3. Your existing workflows work unchanged
./akios run workflow.yml
```

**Benefits:** Cross-platform consistency, works on macOS/Windows, easy containerization.

---

## Table of Contents

1. [Quick Migration Checklist](#-quick-migration-checklist)
2. [Choosing Your Installation Method](#-choosing-your-installation-method)
3. [Migrating from Pip-Only](#-migrating-from-pip-only)
4. [Migrating from Docker-Only](#-migrating-from-docker-only)
5. [Configuration Changes](#-configuration-changes)
6. [Workflow Compatibility](#-workflow-compatibility)
7. [Troubleshooting Migration](#-troubleshooting-migration)

---

## 🚀 Quick Migration Checklist

### ✅ **Immediate Actions (Required)**
- [ ] Choose your preferred installation method (Pip/Docker)
- [ ] Backup your existing `.env` and `config.yaml` files
- [ ] Test migration in a non-production environment first
- [ ] Update your deployment scripts/playbooks
- [ ] Verify API keys and configurations work

### ✅ **Post-Migration Verification**
- [ ] Run `akios status` to verify security settings
- [ ] Execute test workflows: `akios run templates/hello-workflow.yml`
- [ ] Check audit logs: `akios audit export --format json`
- [ ] Validate PII redaction: run a workflow with sensitive test data

---

## 🎯 Choosing Your Installation Method

### For **Most Users** (Recommended)
```bash
# Pip Package - Maximum security on Linux
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

akios init my-project
```

**Benefits:** Full kernel-hard security, Python ecosystem integration.

### For **Python Developers**
```bash
# Pip Package - Full ecosystem integration
# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

akios init my-project
```

**Benefits:** Maximum security on Linux, Python package management.

### For **Cross-Platform Teams**
```bash
# Docker - Consistent environment everywhere
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios
./akios init my-project
```

**Benefits:** Same experience on macOS, Windows, Linux.

### For **Emergency Recovery**
```bash
# Direct Docker - When wrapper download fails
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.8 init my-project
cd my-project
# Create wrapper for future use
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.8 "$@"' > akios
chmod +x akios
```

**Benefits:** Works without network access, recovery when GitHub is unavailable.

---

## 📦 Migrating from Pip-Only

### Current Setup (Pip Only)
```bash
pip install akios  # Your current setup
akios run workflow.yml
```

### Migration Options

#### Option 1: Upgrade to Pip Package (Recommended)
```bash
# 1. Upgrade your existing installation
pip install --upgrade akios

# 2. Your existing workflows work unchanged
akios run workflow.yml
```

#### Option 2: Keep Pip (No Changes Needed)
```bash
# Your existing setup continues to work
pip install --upgrade akios  # Get latest v1.0 features
akios run workflow.yml       # Same commands, enhanced security
```

**What's Different in v1.0:**
- ✅ **Better security**: Enhanced PII redaction, improved sandboxing
- ✅ **Performance**: Faster startup, optimized resource usage
- ✅ **Audit**: More detailed logging, better compliance reports
- ✅ **Compatibility**: All your existing workflows work unchanged

---

## 🐳 Migrating from Docker-Only

### Current Setup (Docker Only)
```bash
# Your current Docker wrapper
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios
./akios run workflow.yml
```

### Migration Options

#### Option 1: Upgrade Docker Wrapper (Recommended)
```bash
# Your existing wrapper continues to work
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios

# Enhanced v1.0 features automatically available
./akios run workflow.yml  # Better security, performance
```

#### Option 2: Switch to Pip Package
```bash
# 1. Install pip package
pip install akios

# 2. Your projects work the same way
cd my-project
akios run workflow.yml  # Direct execution, full security
```

**Benefits:** Maximum security, Python ecosystem integration.

#### Option 3: Keep Docker for Development, Use Pip for Production
```bash
# Development (familiar Docker environment)
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
chmod +x akios
./akios run workflow.yml

# Production (pip package deployment)
pip install akios
akios run workflow.yml
```

**Docker Security in v1.0:**
- ✅ **Enhanced isolation**: Better container policies
- ✅ **Improved performance**: Optimized for containerized environments
- ✅ **Cross-platform consistency**: Same security on macOS/Windows
- ✅ **Audit durability**: Improved logging in containerized environments

---

## ⚙️ Configuration Changes

### Environment Variables (No Changes Required)

Your existing `.env` configurations work unchanged:

```bash
# These remain exactly the same
OPENAI_API_KEY=sk-your-key
AKIOS_LLM_PROVIDER=openai
AKIOS_MOCK_LLM=0
```

### Config.yaml Updates (Optional)

v1.0 includes additional security and performance options. Your existing config continues to work, but you can add:

```yaml
# Enhanced security (optional additions)
pii_redaction_outputs: true     # Redact AI responses (default: true)
audit_export_format: "json"     # Export format (default: json)

# Performance optimizations (optional)
cpu_limit: 0.8                  # CPU usage limit (default: 0.8)
memory_limit_mb: 256           # Memory limit (default: 256)

# Network controls (if using HTTP agent)
network_access_allowed: true    # Allow external API calls
```

### Security Defaults in v1.0

| Setting | V0.x Default | v1.0 Default | Change |
|---------|--------------|--------------|--------|
| `sandbox_enabled` | `true` | `true` | No change |
| `pii_redaction_enabled` | `true` | `true` | No change |
| `cost_kill_enabled` | `true` | `true` | No change |
| `audit_enabled` | `true` | `true` | No change |
| `pii_redaction_outputs` | N/A | `true` | Enhanced in v1.0 |
| `max_tokens_per_call` | `1000` | `500` | **More conservative** |
| `budget_limit_per_run` | `1.0` | `1.0` | No change |

---

## 🔄 Workflow Compatibility

### ✅ **Fully Compatible Workflows**

All your existing YAML workflows work without changes:

```yaml
# Your existing workflows work unchanged
name: "My Existing Workflow"
description: "Migrates automatically to v1.0"

steps:
  - step: 1
    agent: llm
    action: complete
    parameters:
      prompt: "Your existing prompt"
      # All parameters work the same
```

### ✅ **Enhanced Features Available**

v1.0 provides additional capabilities you can optionally use:

```yaml
# Optional v1.0 features
steps:
  - step: 1
    agent: llm
    config:
      provider: "anthropic"  # Additional provider support
      model: "claude-3-sonnet-20240229"
    action: complete
    parameters:
      prompt: "Enhanced with better PII protection"
    # Output redaction automatically applied
```

### ✅ **Agent Compatibility**

| Agent | Status | Changes |
|-------|--------|---------|
| **LLM** | ✅ Compatible | Enhanced PII redaction, additional providers |
| **Filesystem** | ✅ Compatible | Improved security validation |
| **HTTP** | ✅ Compatible | Better network controls |
| **Tool Executor** | ✅ Compatible | Enhanced command validation |

---

## 🐛 Troubleshooting Migration

### Issue: "Command not found: akios"

**Pip Installation:**
```bash
# Ensure PATH includes pip install location
export PATH="$HOME/.local/bin:$PATH"
which akios

# Or reinstall
pip install --force-reinstall akios
```

### Issue: "Configuration validation failed"

**Check your .env file:**
```bash
# Validate environment variables
akios setup  # Interactive configuration wizard

# Or check manually
cat .env | grep -E "(API_KEY|PROVIDER)"
```

**Reset configuration:**
```bash
# Backup and recreate
cp .env .env.backup
rm .env
akios init $(basename $(pwd))  # Reinitialize
```

### Issue: "Security validation failed"

**Different platforms have different security capabilities:**

```bash
# Check your security level
akios status

# Linux (pip): Full kernel-hard security
# macOS/Windows (docker): Strong policy-based security
# Docker (all platforms): Strong container security
```

### Issue: "Workflow fails with API errors"

**API keys may need updating:**
```bash
# Test API connectivity
akios setup  # Reconfigure API keys

# Check API key format for your provider
# OpenAI: sk-...
# Anthropic: sk-ant-...
# Grok: xai-...
```

### Issue: "PII redaction too aggressive"

**Adjust redaction settings:**
```yaml
# In config.yaml
pii_redaction_aggressive: false  # Less aggressive (default)
redaction_strategy: "mask"       # Use [REDACTED] instead of removal
```

### Performance Issues

**Pip vs Docker Performance:**
- **Pip**: Faster startup on Linux, full kernel security
- **Docker**: Cross-platform compatibility, containerized security

**Optimize for your use case:**
```yaml
# For speed
cpu_limit: 1.0
memory_limit_mb: 512

# For security (Linux pip only)
environment: "production"
sandbox_enabled: true
```

---

## 📊 Migration Success Metrics

After migration, verify these indicators:

### ✅ **Security Health**
```bash
akios status | grep -E "(PII|Sandbox|Audit)"
# Should show all protections active
```

### ✅ **Workflow Success**
```bash
akios run templates/hello-workflow.yml
echo $?  # Should be 0 (success)
```

### ✅ **Performance**
```bash
time akios --version  # Should be < 1 second
```

### ✅ **Audit Integrity**
```bash
akios audit export --format json | jq length  # Should show events
```

---

## 🎯 Post-Migration Checklist

- [ ] **Backup completed** (`.env`, `config.yaml`, workflows)
- [ ] **Installation method chosen** (Pip/Docker)
- [ ] **Test environment validated** (non-production first)
- [ ] **Security settings verified** (`akios status`)
- [ ] **Workflows tested** (existing + new)
- [ ] **API connectivity confirmed** (real LLM calls work)
- [ ] **Audit logging functional** (events recorded)
- [ ] **Performance acceptable** (startup < 2s, workflows complete)
- [ ] **Team documentation updated** (new installation method)

---

## 📞 Need Help?

**Documentation:**
- [Quick Start Guide](quickstart.md) - Step-by-step tutorial
- [Configuration Reference](configuration.md) - All settings explained
- [Troubleshooting Guide](troubleshooting.md) - Common issues & solutions

**Community Support:**
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and migration help

**Migration verified?** Your AKIOS v1.0 hybrid deployment is ready for production! 🛡️🤖

---

*AKIOS v1.0 Migration Guide - Zero-downtime upgrades, maximum compatibility*