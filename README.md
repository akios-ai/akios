# AKIOS – The Open-Source Security Cage for AI Agents
**Document Version: 1.0**  
**Date: January 24, 2026**  

**Security sandboxing · Real-time PII redaction · Merkle audit · Cost kills**

[![GitHub stars](https://img.shields.io/github/stars/akios-ai/akios?style=social)](https://github.com/akios-ai/akios)

AKIOS is the **strongest open-source cage** you can put around any AI agent. Run AI workflows with military-grade security, automatic cost controls, and cryptographic audit trails.

## 🚀 Quick Start (5 minutes – Docker Works on All Platforms)

**Security Levels:**
- **Native Linux**: Full security feature set (automatic - no setup required)
- **Standard Docker**: Strong policy-based security across all platforms (macOS, Linux, Windows)
- **Future**: Enhanced security options in upcoming versions

**✅ Docker provides reliable security across all platforms** - simple setup, strong protection, and optimized performance with smart caching for fast subsequent runs.

**Most users start with Docker for cross-platform compatibility and excellent security.**

### Platform Security Overview

| Environment | Security Level | Status | Notes |
|-------------|----------------|--------|-------|
| Docker on any platform (macOS/Linux/Windows) | Strong policy-based container isolation | ✅ V1.0 | Simple, reliable, cross-platform |
| Native Linux (AWS EC2) | Full security feature set | ✅ V1.0 | Maximum security and performance |
| gVisor on Linux | Kernel-hard isolation | 🔮 V1.1+ | Future advanced security option |

**AKIOS V1.0 provides strong, reliable security across all platforms.**

#### ⚠️ **Docker Security Limitations**
**Important Security Trade-off:** Docker mode provides **strong policy-based security** but **does NOT** enforce host filesystem permissions. This is a **known limitation** of containerized deployment.

**What Docker CANNOT do:**
- ❌ **Host filesystem permission enforcement** (`chmod 444` is bypassed - containers run as root internally)
- ❌ **Full kernel-hard security** (no seccomp-bpf on macOS/Windows - reduced to policy-based only)

**What Docker DOES provide:**
- ✅ **Strong container isolation** (network restrictions, resource limits)
- ✅ **PII redaction** (application-level data protection)
- ✅ **Audit logging** (comprehensive security tracking)
- ✅ **Cost kill-switches** (automatic budget enforcement)
- ✅ **Input validation** (automatic size limits and safety checks)
- ✅ **Rate limiting protection** (automatic retry with backoff)
- ✅ **Performance optimizations** (automatic container-aware resource management)

**For maximum security** (full kernel-hard seccomp-bpf + strict filesystem permissions):
**Use native Linux installation** on Linux hosts.

### macOS & Windows / Docker Users – Important Note on Audit Logging

**Full audit trail is preserved** in normal operation thanks to:

- Memory buffering (events held in RAM, flushed every 100 events)
- tmpfs mount for `/app/audit` (writes happen in ultra-fast in-memory filesystem)

**Extremely rare edge case:**
If the container is **violently killed** (e.g. via Task Manager "End task" on Windows or `docker kill --signal=SIGKILL` / force-quit Docker Desktop) exactly during a flush window, up to the last ~100 audit events could be lost.

**Real-world impact:**
This requires forceful termination at a precise moment — it is **extremely unlikely** in normal use and almost impossible without someone deliberately attacking the Docker runtime itself.

**Recommendation for maximum paranoia / compliance environments:**
Use **native Linux installation** (kernel-level cgroups + seccomp + direct filesystem writes) for absolute audit durability with zero possibility of loss.

All other security guarantees (PII redaction, sandboxing, path/command restrictions, network controls, cost/loop kill-switches) remain **fully active** in Docker on macOS and Windows.

**Choose Docker for:**
- Cross-platform convenience (macOS, Windows, Linux)
- Development & testing scenarios
- Most production use cases

**Choose Native Linux for:**
- Regulated/high-security environments
- Strict filesystem permission enforcement
- Maximum security guarantees

## Installation (works on Linux, macOS, Windows)

```bash
# Option 1: Pip Package (Recommended - maximum security on Linux)
pip install akios
akios init my-project
cd my-project
# Setup wizard runs automatically - just follow the prompts!
akios run templates/hello-workflow.yml

# Option 2: Docker (Cross-platform - works on Linux, macOS, Windows)
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/akios
ls -la akios && file -b akios  # Verify download (shell script)
chmod +x akios
./akios init my-project
cd my-project

# What is this wrapper script?
# - Zero-dependency Docker wrapper for AKIOS
# - Manages Docker image pulls and container execution
# - Provides consistent CLI experience across platforms
# - Handles security sandboxing and resource limits

# Setup wizard runs automatically - just follow the prompts!
./akios run templates/hello-workflow.yml

# Optional: refresh the Docker image on the next run
AKIOS_FORCE_PULL=1 ./akios status
```

### Which Installation Should I Choose?

| Option | Best For | Requirements | Security Level | Ease of Use |
|--------|----------|--------------|----------------|-------------|
| **Pip Package** ⭐ | Python developers, maximum security | Python 3.8+, Linux kernel 3.17+ | Full kernel-hard security | ⭐⭐⭐⭐⭐ |
| **Docker** | Cross-platform teams, development environments | Docker installed | Strong policy-based security | ⭐⭐⭐⭐ |
| **Direct Docker** | Emergency fallback when wrapper fails | Docker installed | Strong policy-based security | ⭐⭐⭐ |

**Choose Pip if:**
- You're a Python developer
- You need maximum security (Linux kernel features)
- You want to integrate AKIOS into Python applications

**Choose Docker if:**
- You need cross-platform compatibility
- You already use Docker in your workflow
- You want containerized deployment

**Choose Direct Docker if:**
- The wrapper script download fails (curl issues, network problems)
- You prefer direct Docker commands over wrapper scripts
- You need emergency access when GitHub is unavailable

### Get Started

```bash
# 1. Create your first project
akios init my-project
cd my-project

# 2. Configure your AI provider (guided setup)
akios setup  # Interactive wizard for API keys and settings
# Use --force to re-run setup: akios setup --force

# 3. Run your first workflow
akios run templates/hello-workflow.yml

# 4. Check results and status
akios status
cat data/output/run_*/hello-ai.txt
```

## V1.0 UX and Value

AKIOS V1.0 is designed around **one workflow per project** so users can run, test, and deploy a single, focused workflow with minimal setup.

**What users get in V1.0:**
- **Security-first execution** in Docker and native Linux (Linux provides the strongest guarantees).
- **Ready-to-run templates** to learn fast, then adapt for real use cases.
- **Clear outputs** in timestamped run folders under `data/output/run_*/`.
- **Audit trails** for every workflow, with export support for compliance reporting.

### Verify Your Installation

```bash
# All installation methods support the same commands:
akios --version          # Show version
akios --help            # Show help
akios init my-project   # Create new project
cd my-project
akios setup             # Configure API keys and settings
akios status            # Check system status
akios files             # Show available input/output files
akios run templates/hello-workflow.yml  # Run sample workflow
```

AKIOS includes a guided setup wizard that makes configuration effortless:
- Interactive provider selection (OpenAI, Anthropic, Grok, Mistral, Gemini)
- Model selection (gpt-4o, claude-3.5-sonnet, grok-3, etc.)
- Real API key validation with test calls
- Budget and token limit configuration
- Secure storage in .env file

```bash
akios setup  # Run the guided setup wizard
```

Manual configuration is also available:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## ⚠️ **IMPORTANT: Project Context**

**All project commands (run, status, audit, clean, etc.) expect to be run from INSIDE your project directory** (after `cd my-project`).

**❌ Wrong (unexpected results):**
```bash
./akios init my-project
./akios run templates/hello-workflow.yml  # Uses current dir as context!
./akios status                           # Shows wrong project data!
```

**✅ Correct (intended experience):**
```bash
./akios init my-project
cd my-project                    # ← REQUIRED STEP
./akios run templates/hello-workflow.yml
./akios status
```

**Running project commands from outside uses the current directory as context — this may cause unexpected results** (wrong outputs, wrong audit data, etc.).

**Always `cd` into your project folder for the intended experience.**

**What this gives you**:
- ✅ **Standalone Binaries**: Zero-dependency deployment with full security
- ✅ **Pip Package**: Maximum security on Linux (kernel-hard features)
- ✅ **Docker**: Strong cross-platform security (all operating systems)
- ✅ **Cross-platform support** (Linux, macOS, Windows)
- ✅ **Compliance-ready** for regulated environments
- ✅ **Real LLM integration** with audit trails
- ✅ **Cryptographic verification** (SHA256 hashes for all downloads)

## ✨ Key Features

- **🔒 Security Sandboxing**: Kernel-hard isolation on native Linux (seccomp-bpf + cgroups) or strong policy-based security in Docker — agents cannot escape
- **🛡️ Comprehensive PII Redaction**: 50+ pattern detection covering personal, financial, health, and location data before LLM processing
- **📊 Merkle Audit Trails**: Cryptographic proof of execution integrity — tamper-evident JSON exports
- **💰 Cost Kill-Switches**: Hard budget limits ($1 default) with automatic termination on violations
- **⚡ Zero-Dependency Deployment**: Standalone binaries for air-gapped environments, plus pip packages for Python integration
- **🔧 Core Agents**: Filesystem, HTTP, LLM, and Tool Executor agents for complete AI workflows
- **✅ Real AI Integration**: Templates use actual LLM APIs - not mock responses or demo placeholders

## 🔍 Audit & Compliance

AKIOS V1.0 provides **raw, tamper-evident audit logs** (JSONL format) for every workflow execution.

- `akios audit` — view recent events
- `akios audit export --format json` — raw JSON export

## 🛡️ Security Levels by Environment

AKIOS V1.0 uses Linux kernel features for maximum security. Security levels vary by deployment environment:

### Native Linux (Recommended for Production)
- **Security Level**: Full (kernel-hard)
- **Features**:
  - ✓ cgroups v2 resource isolation
  - ✓ seccomp-bpf syscall filtering
  - ✓ Unbreakable containment
- **Requirements**: Linux kernel 3.17+ with cgroups v2 support, `libseccomp-dev` installed
- **Benefit**: Provides the highest level of process isolation and syscall control, preventing even sophisticated attacks

### Docker (All Platforms)
- **Security Level**: Strong (policy-based)
- **Features**:
  - ✓ Command/path allowlisting
  - ✓ PII redaction (ML-based)
  - ✓ Audit logging
  - ✓ Container isolation
  - ✓ Cross-platform compatibility
- **Requirements**: Docker installed and running
- **Benefit**: Provides reliable security across macOS, Linux, and Windows

### macOS/Windows (Via Docker Only)
- **Security Level**: Strong (policy-based)
- **Features**: Command allowlisting, PII redaction, audit logging, container isolation
- **Requirements**: Docker Desktop installed and running
- **Benefit**: Provides reliable security across all platforms

**For maximum security: run on native Linux.**  
**Docker provides strong security — but not the absolute maximum.**

## 🔧 Docker Troubleshooting

### Installation Issues

#### Wrapper Script Download Issues
```bash
# Verify the wrapper script downloaded correctly
ls -la akios && file akios

# Expected output:
# -rw-r--r--  1 user  group  3426 Jan 17 17:56 akios
# akios: Bourne-Again shell script text executable, Unicode text, UTF-8 text

# If download failed, use Direct Docker fallback:
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.0 init my-project
cd my-project
# Create wrapper script for future use
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.0 "$@"' > akios
chmod +x akios
./akios --version  # Should show "AKIOS 1.0.0"
```

#### Docker Installation Issues
```bash
# Check Docker installation
docker --version
docker system info

# Restart Docker if needed
# On macOS: Restart Docker Desktop
# On Linux: sudo systemctl restart docker
# On Windows: Restart Docker Desktop
```

### Performance Issues
- **Expected behavior**: Optimized Docker performance with automatic container-aware optimizations
- **If slow**: Check Docker resource limits, restart Docker
- **Network issues**: Ensure stable internet connection
- **File operations**: AKIOS automatically optimizes I/O operations for containerized environments

### Compatibility Issues
- **Platform support**: Works on macOS, Linux, Windows
- **Resource requirements**: 2GB RAM minimum, 4GB recommended
- **Permission issues**: Ensure Docker has proper access to project directories

### Runtime Errors
```bash
# Check Docker daemon logs
docker system info

# Test Docker directly
docker run hello-world

# Check AKIOS logs
akios logs --limit 10
```

### Security Expectations
AKIOS provides strong policy-based security in Docker:
- Command allowlisting active
- PII redaction works
- Audit trails maintained
- Container isolation provided
- **Memory usage**: ~50MB additional per container
- **Disk space**: ~500MB for Docker images

### Known Limitations
- **Large workflows**: May require increased Docker resource limits
- **Network timeouts**: AI API calls may need longer timeouts in containers
- **File permissions**: Ensure proper volume mounting permissions

### Performance Expectations
Typical performance with AI workflows:

| Metric | Docker (All Platforms) | Native Linux (AWS EC2) |
|--------|----------------------|----------------------|
| **Startup time** | 0.5-0.8s | **0.4-0.5s** (10-20% faster) |
| **Runtime overhead** | 0% (optimized) | **-5-10%** (more efficient) |
| **Memory usage** | 60-80MB | **40-60MB** (25-33% less) |
| **Security level** | Policy-based | Full kernel-hard features |
| **Compatibility** | Full | Full |

**✅ Validated Results**: Native Linux performance exceeds Docker baselines with superior efficiency and security.

**Recommendation**: Use native Linux for maximum performance and security, Docker for cross-platform compatibility.

## 🎯 What AKIOS Solves

**The AI Security Crisis**: AI agents can leak sensitive data, run up massive bills, and execute dangerous code — all while being impossible to audit.

**AKIOS Solution**: Every AI workflow runs inside a hardened security cage with:
- **Zero data leakage** through automatic PII redaction
- **Predictable costs** through hard budget enforcement
- **Complete auditability** through cryptographic logging
- **Unbreakable containment** through kernel-level isolation
- **Real AI functionality** - templates produce actual AI-generated content using OpenAI/Anthropic/Grok/Mistral/Gemini

## 📋 Limits (V1.0)

AKIOS V1.0 is **minimal by design** — focused on security fundamentals:

- **Linux kernel required** (5.4+ for cgroups v2 + seccomp-bpf security)
- **Docker recommended** (provides Linux environment for macOS/Windows users)
- **Sequential workflows only** (no parallel execution)
- **Core agents** (filesystem, HTTP, LLM, tool executor)
- **Basic CLI** (10 commands: init, setup, run, workflow, audit export, logs, status, templates, testing, clean)
- **No API server** (CLI-only in V1.0)
- **No monitoring dashboard** (command-line only)

These limits ensure **bulletproof security**. Advanced features come in future releases.

## ⚠️ Production Security Warning

**🔑 API Keys Required**: V1.0 requires real API keys for LLM functionality. See setup instructions below.

AKIOS V1.0 provides genuine LLM API integration with OpenAI, Anthropic, Grok, Mistral, and Gemini for real workflows and audit-ready results.

## 🛠️ Installation

### Requirements
- **Linux kernel 3.17+** with cgroups v2 and seccomp support
- **Python 3.8+**
- **pip** for installation

### Install from PyPI
```bash
pip install akios
```

### Verify Installation
```bash
akios --version
```

## 📦 Dependencies

AKIOS uses a structured dependency management system for different use cases:

### Core Dependencies (`requirements.txt`)
Runtime dependencies required to run AKIOS workflows:
- **Core functionality**: `pydantic`, `click`, `pyyaml`, `jsonschema`
- **LLM providers**: `openai`, `anthropic` (for AI agent functionality)
- **Security & PII**: `presidio-analyzer`, `presidio-anonymizer`, `cryptography`
- **System monitoring**: `psutil`, `httpx`

### Build Dependencies (`requirements-build.txt`)
Development and build-time tools:
- **Testing**: `pytest`, `pytest-cov` (comprehensive test coverage)
- **Code quality**: `black`, `flake8`, `mypy` (linting and type checking)
- **Documentation**: `sphinx` (docs generation)

### Installation Options

| Option | Command | Includes | Use Case |
|--------|---------|----------|----------|
| **Minimal** | `pip install akios` | Core runtime only | Basic workflows, no AI |
| **With AI** | `pip install akios[agents]` | + LLM providers | Full AI functionality |
| **Development** | `pip install akios[dev]` | + Testing tools | Contributing to AKIOS |
| **API Server** | `pip install akios[api]` | + FastAPI, uvicorn | REST API deployment |
| **Docker Build** | N/A | Both files | Container deployment |

### Docker vs PyPI Dependencies

- **PyPI installs** use `pyproject.toml` dependencies (modern Python packaging)
- **Docker builds** use both `requirements.txt` + `requirements-build.txt` for complete environments
- **Security libraries** (`seccomp`) are platform-specific and handled via optional dependencies

## 🐧 Advanced Installation Options

**Choose the best deployment method for your use case:**

### Option 1: Native Linux (Maximum Security)
**For Linux users who prefer native performance** (no Docker overhead) or need **maximum security isolation**:

**Requirements**:
- **Linux kernel 3.17+** (for cgroups v2 + seccomp security features)
- **Python 3.8+**
- **GCC/make** for optional agent dependencies

**Install with full security**:
```bash
# Full installation with LLM support
pip install akios[agents]

# Or minimal install (no LLM support)
pip install akios
```

### Verify Security Features
```bash
# Check if kernel security features are available
akios status | grep -E "(Sandbox|Audit|seccomp)"
```

### Option 2: Docker (All Platforms - Strong Security)
**For cross-platform compatibility**:

**Requirements**:
- **Docker installed** and running
- **Cross-platform support** (macOS, Linux, Windows)

**Setup**:
```bash
# Download the wrapper script
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/akios
ls -la akios && file -b akios  # Verify download (shell script)
chmod +x akios

# Run (provides strong cross-platform security)
./akios run templates/hello-workflow.yml
```

**Benefits**: Reliable security across all platforms with simple setup.

**⚠️ Docker is strongly recommended** for cross-platform users — it provides consistent Linux environment and automatic dependency management.

## 🤖 LLM Provider Setup

AKIOS supports **5 LLM providers** for maximum flexibility. Use the guided setup wizard for easy configuration:

### Guided Setup (Recommended)
```bash
# After creating your project:
cd my-project

# Run the interactive setup wizard
akios setup
```

The wizard guides you through:
- Provider selection (OpenAI, Anthropic, Grok, Mistral, Gemini)
- Model selection for your chosen provider
- API key entry with validation
- Budget and security settings

### Manual Setup
```bash
# Alternative: Manual configuration
cd my-project
cp .env.example .env
# Edit .env with your real API keys (NEVER commit .env to version control)
```

### OpenAI (Default)
```bash
# Add to .env file:
OPENAI_API_KEY=sk-your-key-here
AKIOS_LLM_PROVIDER=openai
```

### Anthropic (Claude)
```bash
# Add to .env file:
ANTHROPIC_API_KEY=sk-ant-your-key-here
AKIOS_LLM_PROVIDER=anthropic
```

### Grok (xAI)
```bash
# Add to .env file:
GROK_API_KEY=xai-your-grok-key-here
AKIOS_LLM_PROVIDER=grok
```

### Using Different Providers in Templates

Specify your preferred provider in workflow configurations:

```yaml
steps:
  - agent: llm
    config:
      provider: anthropic  # openai, anthropic, or grok
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-3.5-sonnet"
    action: complete
    parameters:
      prompt: "Analyze this data..."
```

**Supported Models:**
- **OpenAI**: gpt-3.5-turbo, gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini
- **Anthropic**: claude-3.5-haiku, claude-3.5-sonnet
- **Grok**: grok-3, grok-3-turbo

> **🔑 API Keys Required**: V1.0 uses real LLM APIs - you must provide API keys.

Set `AKIOS_MOCK_LLM=1` to use mock responses (for testing/CI without API keys).

## 🛡️ Security Safeguards

**Provider Allowlist**: Only explicitly allowed providers can be used. Configure in `config.yaml`:
```yaml
allowed_providers: ["openai", "anthropic", "grok"]  # Restrict to specific providers
```

**Mock Mode for Testing Only**: Use fake responses for development/testing without API keys:
```bash
# Enable mock mode via environment variable
export AKIOS_MOCK_LLM=1

# Or via config.yaml
mock_llm_fallback: true
```

### **When to Use Mock vs Real Mode**

| Use Case | Recommended Mode | Why |
|----------|------------------|-----|
| **Learning AKIOS** | Mock Mode | Instant setup, explore features without API keys |
| **Developing Workflows** | Mock Mode | Test logic and templates without API costs |
| **CI/CD Testing** | Mock Mode | Fast, reliable automated testing |
| **Production Workflows** | Real Mode | Full AI capabilities with real providers |
| **Cost-Sensitive Tasks** | Real Mode | Actual AI responses (with budget controls) |
| **High-Quality Output** | Real Mode | Best results from GPT-4, Claude, Grok, etc. |

Both safeguards ensure **100% bulletproof operation** in all environments.

## 🛡️ Security Levels by Environment

AKIOS adapts its security approach based on the deployment environment:

### **Native Linux (Recommended for Production)**
- **Security Level**: Full (kernel-hard)
- **Features**: cgroups v2 + seccomp-bpf + comprehensive audit
- **Requirements**: Linux kernel 3.17+, root access for security setup
- **Use Case**: Production, high-security environments

### **Docker Containers (Recommended for Development/Testing)**
- **Security Level**: Partial (policy-based)
- **Features**: Command allowlist + path restrictions + PII redaction + audit
- **Limitations**: Cannot use kernel-level seccomp-bpf (container restrictions)
- **Use Case**: Development, CI/CD, cross-platform deployment

### **macOS/Windows (Via Docker Only)**
- **Security Level**: Partial (policy-based)
- **Features**: Same as Docker containers
- **Requirements**: Docker Desktop installed
- **Use Case**: Local development on non-Linux platforms

### **Check Your Security Level**
```bash
akios status
```
Look for the **🛡️ Security Status** section to see your current security level and capabilities (Full kernel-hard or Strong policy-based).

## 📋 Quick Start & Core Files

The essential files you'll need to get started:

- **[GETTING_STARTED.md](./GETTING_STARTED.md)** – 3-minute try-it-now guide
- **[AGENTS.md](./AGENTS.md)** – Core agents (LLM, HTTP, Filesystem, Tool Executor)
- **[RELEASES.md](./RELEASES.md)** – What V1.0 delivers and scope limitations
- **[akios](./akios)** – Smart wrapper (Cross-platform Docker launcher)
- **[config.yaml](./config.yaml)** – Default configuration template
- **[Dockerfile](./Dockerfile)** – Official Docker build
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** – Deployment philosophy and security-first approach
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** – Common issues and solutions

## 📚 Documentation

### 🚀 Quick Start
- **[Getting Started](GETTING_STARTED.md)** - 3-minute setup guide with Docker wrapper
- **[Templates](src/akios/templates/)** - 4 production-ready AI workflow examples
- **[Roadmap](ROADMAP.md)** - Vision, future plans, and PRO strategy

### 📖 Complete Guides
- **[Configuration](docs/configuration.md)** - Settings and environment variables
- **[CLI Reference](docs/cli-reference.md)** - All command-line options
- **[Security Overview](docs/security.md)** - Security features and compliance
- **[Deployment](docs/deployment.md)** - Production deployment options
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

### 🏗️ Design & Architecture
- **[CLI Scope & Boundaries](docs/cli-scope-boundaries.md)** - V1.0 CLI design constraints and limitations

### 📋 [Documentation Index](docs/README.md) - All guides in one place

## 🔒 Security First

AKIOS is built around **unbreakable security**:

### Process Isolation
- **Kernel-level sandboxing** using cgroups v2 + seccomp-bpf
- **Syscall interception** blocks dangerous operations
- **Process containment** prevents escape attempts

### Data Protection
- **Comprehensive PII redaction** (50+ pattern coverage)
- **No sensitive data** reaches LLM processing
- **Cryptographic audit trails** prove compliance

### Cost Control
- **Hard budget limits** ($1.00 default per workflow)
- **Token restrictions** prevent runaway LLM costs
- **Automatic kill-switches** on violations

### Audit Integrity
- **Merkle tree verification** ensures tamper-evident logs
- **JSON exports** for regulatory compliance
- **Cryptographic proof** of execution integrity

## 🚀 Production AI Workflows

AKIOS ships with **4 production-ready AI applications** (not demo placeholders):

### Hello World
```bash
akios run templates/hello-workflow.yml
```
Basic file operations - proves the security cage works.

### Real AI Document Analysis
```bash
# Create sample document
echo "Contact john.doe@example.com for project details. Phone: 555-123-4567" > data/input/document.txt

# Get real AI summary with automatic PII redaction
akios run templates/hello-workflow.yml

# Verify AI output was generated
cat data/output/run_*/summary.txt
```

### AI-Powered File Analysis
```bash
# Create file to analyze
echo "Sample data for AI analysis" > data/input/analysis_target.txt

# Get real AI insights with syscall sandboxing
akios run templates/file_analysis.yml

# Check AI-generated analysis
cat audit/analysis_integrity.txt
```

### Cost-Controlled AI Data Enrichment
```bash
# Create input data
echo "Sample files for batch processing" > data/input/batch/sample1.txt
echo "More content for analysis" > data/input/batch/sample2.txt

# Process multiple files with AI aggregation
akios run templates/batch_processing.yml

# Verify AI output
cat data/output/run_*/batch-summary.json
```

**Note:** The `batch_processing.yml` template processes multiple local files with AI analysis; all LLM outputs are real when `AKIOS_MOCK_LLM=0`.

**All templates produce real AI-generated content using your chosen LLM provider (OpenAI/Anthropic/Grok/Mistral/Gemini) - not placeholder text.**

## 📈 Roadmap

**Current: V1.0** - Security cage fundamentals (Linux-only, minimal features)

**Future Releases:**
- **Enhanced Security**: Additional compliance features, advanced monitoring
- **Cross-Platform**: macOS/Windows support with equivalent security
- **Advanced Orchestration**: Parallel execution, workflow dependencies
- **Advanced Integrations**: REST API, monitoring dashboard, advanced integrations

## 🤗 Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Security**: Report vulnerabilities to hello@akios.ai

## 📄 License

AKIOS Open Runtime is licensed under the **GPL-3.0** license. The security cage and audit system ensure AI agents run safely while maintaining full transparency through open source.

---

**Built with security-first principles. Run AI agents safely — anywhere.**
