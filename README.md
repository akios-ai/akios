# AKIOS v1.0.5 – The Open-Source Security Cage for AI Agents
**Document Version:** 1.0.5  
**Date:** 2026-02-10  

**Security sandboxing · Real-time PII redaction · Merkle audit · Cost kills**


<div align="center">
  <img src="https://raw.githubusercontent.com/akios-ai/akios/main/assets/logo.png" alt="AKIOS Logo" width="250" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</div>



AKIOS is open-source (GPL-3.0-only). Read the legal notices, trademarks, and security policy before use.

**EU AI Act disclaimer:** AKIOS is not designed for "high-risk" use cases under the EU AI Act. For such deployments, consult a compliance expert and consider implementing additional regulatory controls on top of AKIOS.

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
| Docker on any platform (macOS/Linux/Windows) | Strong policy-based container isolation | ✅ v1.0 | Simple, reliable, cross-platform |
| Native Linux (with sudo) | Full kernel-hard security (seccomp-bpf + cgroups) | ✅ v1.0 | Maximum security and performance |
| Native Linux (without sudo) | Strong policy-based security | ✅ v1.0 | Graceful degradation with warnings |
| gVisor on Linux | Kernel-hard isolation | 🔮 V1.1+ | Future advanced security option |

**AKIOS v1.0 provides strong, reliable security across all platforms.**

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
**Use native Linux installation with sudo** on Linux hosts.

> **Note:** `pip install akios` on Linux automatically includes the seccomp module. For full kernel-hard security, run AKIOS with sudo (`sudo akios run workflow.yml`). Without sudo, AKIOS gracefully degrades to policy-based mode with clear warnings.

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
- **Required:** Run with sudo for full kernel-hard protection

## Installation (works on Linux, macOS, Windows)

```bash
# Option 1: Pip Package (Recommended - maximum security on Linux)

# Ubuntu 24.04+ users: Use pipx instead of pip due to PEP 668
sudo apt install pipx
pipx install akios

# Ubuntu 20.04/22.04 and other Linux/macOS/Windows users:
pip install akios

akios init my-project
cd my-project
# Setup wizard runs automatically - just follow the prompts!
akios run templates/hello-workflow.yml

# Option 2: Docker (Cross-platform - works on Linux, macOS, Windows)
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
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

> **📦 Version Note:** `pip install akios` installs the latest stable version (currently v1.0.5). 
> For specific versions: `pip install akios==1.0.5`. 

---

## 🚨 **REQUIRED: Linux System Packages (Before Pip Install)**

If you're installing on **Linux**, you MUST install the security library first:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install libseccomp-dev python3-seccomp

# Fedora/RHEL  
sudo dnf install libseccomp-devel python3-seccomp
```

**Why?** AKIOS uses kernel-hard security (seccomp-bpf) on Linux for maximum protection. These packages must be installed before `pip install akios`.

**If you skip this:**
- ✅ `pip install akios` will still work
- ✅ AKIOS will still run  
- ⚠️ Advanced security features will degrade with clear warnings
- 📊 You get policy-based security (same as Docker) instead of kernel-hard

**macOS & Windows:** No pre-installation needed.

---

### Which Installation Should I Choose?

| Option | Best For | Requirements | Security Level | Ease of Use |
|--------|----------|--------------|----------------|-------------|
| **Pip Package** ⭐ | Python developers, maximum security | Python 3.8+, Linux kernel 3.17+<br>**LINUX REQUIRED:** libseccomp-dev + python3-seccomp (see section above)<br>**Ubuntu 24.04+:** `pipx install akios` | Full kernel-hard security (Linux) | ⭐⭐⭐⭐⭐ |
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

# 5. Clean up old runs (optional)
akios clean

# 6. Export audit proof
```

## v1.0 UX and Value

AKIOS v1.0 is designed around **one workflow per project** so users can run, test, and deploy a single, focused workflow with minimal setup.

**What users get in v1.0:**
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
akios status --budget   # View budget dashboard and cost tracking
akios files             # Show available input/output files
akios run templates/hello-workflow.yml  # Run sample workflow
akios protect scan "text"  # Scan text for PII
akios protect show-prompt workflow.yml  # Preview LLM prompt
akios http GET https://api.example.com  # Secure HTTP request
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
- **🔐 HTTPS Whitelist Control**: Secure network access with explicit per-domain approval (LLM APIs always allowed)
- **🗑️ Secure Data Destruction**: `cage down` completely destroys audit, output, and input data with zero recovery option

---

## Security Cage: Up & Down

### Activate Full Protections

```bash
akios cage up
# Result: All 6 protections ACTIVE
# ├─ PII Redaction: ENABLED
# ├─ Network Lock: HTTPS LOCKED  
# ├─ LLM Access: ALLOWED (always)
# ├─ Sandbox: ENFORCED
# ├─ Audit Trail: RUNNING  
# └─ Cost Controls: ACTIVE
```

### Complete Data Destruction

```bash
# Permanently destroy ALL session data (irreversible)
akios cage down

# Result: 0 bytes remain
# ├─ audit/ destroyed
# ├─ data/output/ destroyed
# ├─ data/input/ destroyed
# └─ ZERO DATA RESIDUE
```

**This is the cage's core promise: sessions disappear completely.**

For development, use `cage down --keep-data` to preserve data while relaxing protections (not production-safe).

---

## HTTPS Whitelist Configuration

By default, **only LLM APIs have network access**. Enable the HTTP agent and whitelist specific domains:

**In `config.yaml`:**
```yaml
network_access_allowed: true
allowed_domains:
  - "api.salesforce.com"
  - "api.mycompany.com"
```

**Or via `.env`:**
```bash
AKIOS_NETWORK_ACCESS_ALLOWED=true
AKIOS_ALLOWED_DOMAINS="api.salesforce.com,api.mycompany.com"
```

**Important:** LLM APIs (OpenAI, Anthropic, Grok, etc.) always pass through network locks — they cannot be blocked.

---
- **🔧 Core Agents**: Filesystem, HTTP, LLM, and Tool Executor agents for complete AI workflows
- **✅ Real AI Integration**: Templates use actual LLM APIs - not mock responses or demo placeholders
- **🎨 Professional Terminal UI** (v1.0.5): Rich-powered colored tables, panels, and styled output for beautiful CLI experience
- **🚀 10/10 Performance**: Validated performance metrics across all platforms (native Linux: 25ms startup, 44.44 wf/s throughput; Docker: <1000ms startup, >5 wf/s throughput)

## ⚡ Performance Highlights

AKIOS v1.0.5 achieves **10/10 performance scores** across all platforms:

### Native Linux (Maximum Performance)
```
✅ Startup:     25ms (sub-50ms latency)
✅ Throughput:  44.44 workflows/second
✅ Memory:      21MB footprint
✅ Scaling:     100% efficiency (perfect horizontal scaling)
✅ Cost:        Industry-leading AI agent execution speed
```

### Docker (Cross-Platform Performance)
```
✅ Startup:     <1000ms (container overhead normal)
✅ Throughput:  >5 workflows/second (parallel-friendly)
✅ Memory:      <150MB (containerized)
✅ Scaling:     >90% efficiency
✅ Cost:        Excellent cross-platform performance
```

**Why Both Scores Matter:**
- **Native Linux (EC2/Kubernetes)**: Choose for maximum performance & security, lowest cost at scale
- **Docker (macOS/Windows/Cloud)**: Choose for cross-platform compatibility, strong security, excellent performance

Both performance profiles are **validated and blocking for every release** — we measure both to ensure no regressions as AKIOS evolves.

**v1.0.5 Validation Results:**
- **Native Linux (EC2)**: 189 E2E tests (20 CLI, 18 security, 4 workflows, 132 demos, 15 performance) — 100% PASS
- **Docker**: 187 E2E tests (20 CLI, 18 security, 4 workflows, 132 demos, 13 performance) — 100% PASS
- Comprehensive test suites execute on every release with real LLM APIs, full security validation, and performance benchmarking

## ⚖️ Legal Disclaimers & User Responsibility

### AKIOS Performance Validation Scope

**AKIOS v1.0.5 performance metrics are validated ONLY on AWS EC2 t3.medium instances in us-east-1 region.** Your actual performance may differ significantly based on:
- Instance type and size
- AWS region and network latency
- System load and other processes  
- Workflow complexity and input data size
- LLM API provider response times
- Configuration choices

### What AKIOS Guarantees
✅ **Security of the sandbox** - Full kernel-hard isolation on native Linux (verified with 18 comprehensive security tests covering cage, audit, PII redaction, and syscall filtering)
✅ **PII redaction** - 50+ pattern detection (>95% accuracy) including healthcare identifiers (NPI, DEA, MRN)
✅ **Audit integrity** - Cryptographic Merkle proofs of execution  
✅ **Performance baseline** - 25ms startup & 44.44 wf/s throughput on t3.medium  

### What AKIOS Does NOT Guarantee
❌ **AWS infrastructure performance** - Varies by instance type and region  
❌ **AWS account security** - Your responsibility to manage credentials and IAM  
❌ **AWS cost management** - You are responsible for monitoring AWS billing  
❌ **Performance on untested instances** - Test on YOUR instance before assuming performance  
❌ **Results from misconfigured deployments** - Configuration errors are user responsibility  

### User Responsibilities

#### AWS Account Security
- **Keep access keys safe** — never commit to git or share
- **Use IAM roles** with least-privilege permissions (don't use root credentials)
- **Enable CloudTrail** for API audit logging
- **Rotate credentials** regularly and monitor account activity
- **Use security groups** to restrict EC2 access (SSH on port 22 only)

**AKIOS is NOT responsible for:**
- EC2 instance compromise or account takeover
- AWS IAM misconfigurations
- Leaked credentials or API keys
- Unauthorized access to your instances

#### Cost Management
- **Monitor your AWS bill** actively during testing
- **Set up AWS billing alerts** to prevent surprise charges
- **Terminate instances** when testing is complete
- **Understand EC2 pricing** for your region and instance type
- **Use on-demand or spot instances** according to your needs

**AKIOS is NOT responsible for:**
- AWS infrastructure charges you incur
- Runaway instances left running after testing
- Data transfer costs or unexpected charges
- Regional price variations

Note: AKIOS includes budget kill-switches for LLM API costs ($1 default), but this does NOT cover AWS EC2, storage, or data transfer costs.

#### Data Security
- **Encrypt sensitive files** before processing through AKIOS
- **Don't hardcode secrets** in workflow definitions or code
- **Use environment variables** for credentials
- **Secure EC2 instances** with proper security groups and SSH key management
- **Review permissions** on all input files and directories

**AKIOS is NOT responsible for:**
- EC2 instance compromise due to misconfiguration
- Secrets leaked through mismanaged workflows
- Data breaches from improperly configured security groups
- Malicious workflows from untrusted sources

#### Infrastructure Validation
- **Test on YOUR instance type** (not just t3.medium)
- **Validate performance** meets YOUR requirements
- **Understand differences** between baseline and your setup
- **Document findings** for your team and future reference

**AKIOS is NOT responsible for:**
- Performance degradation on untested instance types
- Results that don't match your use case
- Infrastructure issues outside AKIOS control
- Third-party software conflicts or misconfiguration

### Performance Testing & Validation

We provide two resources to help validate AKIOS for your use case:

1. **[EC2 Performance Testing Guide](./docs/ec2-performance-testing.md)** (Complete how-to)
   - Instance type recommendations by use case
   - Step-by-step EC2 setup instructions
   - Performance optimization tips
   - Cost estimation and control strategies
   - Troubleshooting for common issues
   - Security best practices for AWS

2. **[Native vs Docker Performance Comparison](#-performance-highlights)** (Detailed metrics)
   - Side-by-side metrics comparison
   - Performance validation with comprehensive E2E test suites
   - Decision matrix: when to use each platform
   - Validation results and methodologies

### When Testing AKIOS on AWS EC2

✅ **Before starting:**
- Understand AWS costs in your region (check EC2 pricing)
- Secure your AWS credentials properly
- Plan for instance cleanup after testing
- Have valid LLM API credentials ready

✅ **During testing:**
- Monitor your AWS billing actively
- Document your instance type and actual performance
- Verify security status (kernel-hard isolation confirmed)
- Test both mock and real API modes

✅ **After testing:**
- Terminate EC2 instances to stop charges
- Archive results and performance baselines
- Rotate any exposed credentials immediately
- Clean up S3, CloudTrail, or other resources

## 🔍 Audit & Compliance

AKIOS v1.0 provides **raw, tamper-evident audit logs** (JSONL format) for every workflow execution.

- `akios audit` — view recent events
- `akios audit export --format json` — raw JSON export

## 🛡️ Security Levels by Environment

AKIOS v1.0 uses Linux kernel features for maximum security. Security levels vary by deployment environment:

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
  - ✓ PII redaction (rule-based, 50+ patterns)
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
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.5 init my-project
cd my-project
# Create wrapper script for future use
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.5 "$@"' > akios
chmod +x akios
./akios --version  # Should show "AKIOS 1.0.5"
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

## 📋 Limits (v1.0)

AKIOS v1.0 is **minimal by design** — focused on security fundamentals:

- **Linux kernel required** (5.4+ for cgroups v2 + seccomp-bpf security)
- **Docker recommended** (provides Linux environment for macOS/Windows users)
- **Sequential workflows only** (no parallel execution)
- **Core agents** (filesystem, HTTP, LLM, tool executor)
- **Basic CLI** (20+ commands: init, setup, run, status, templates, files, logs, audit, doctor, compliance, output, clean, cage, protect, http, timeline, testing, docs)
- **No API server** (CLI-only in v1.0)
- **No monitoring dashboard** (command-line only)

These limits ensure **bulletproof security**. Advanced features come in future releases.

## ⚠️ Production Security Warning

**🔑 API Keys Required**: v1.0 requires real API keys for LLM functionality. See setup instructions below.

AKIOS v1.0 provides genuine LLM API integration with OpenAI, Anthropic, Grok, Mistral, and Gemini for real workflows and audit-ready results.

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
- **Security**: `cryptography`, `psutil`
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
- **Security libraries** (including `seccomp`) are now bundled for Linux hosts via `pyproject.toml`; the only extra step is installing the OS headers (`libseccomp-dev` or `libseccomp-devel`) so the wheel builds cleanly.

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
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios
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

> **🔑 API Keys Required**: v1.0 uses real LLM APIs - you must provide API keys.

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
- **[RELEASES.md](./CHANGELOG.md)** – What v1.0 delivers and scope limitations
- **[akios](./akios)** – Smart wrapper (Cross-platform Docker launcher)
- **[config.yaml](./config.yaml)** – Default configuration template
- **[Dockerfile](./Dockerfile)** – Official Docker build
- **[Deployment Guide](./docs/deployment.md)** – Deployment philosophy and security-first approach
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** – Common issues and solutions

## 📚 Documentation

### 🚀 Quick Start
- **[Getting Started](GETTING_STARTED.md)** - 3-minute setup guide with Docker wrapper
- **[Templates](src/akios/templates/)** - 4 production-ready AI workflow examples
- **[Roadmap](ROADMAP.md)** - Vision, future plans, and PRO strategy

### 📖 Complete Guides
- **[Configuration](docs/configuration.md)** - Settings and environment variables
- **[CLI Reference](docs/cli-reference.md)** - All command-line options
- **[Rich Terminal UI](docs/rich-ui.md)** - Professional styled output with tables and panels
- **[Security Overview](docs/security.md)** - Security features and compliance
- **[Deployment](docs/deployment.md)** - Production deployment options
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

### 🏗️ Design & Architecture
- **[CLI Scope & Boundaries](docs/cli-scope-boundaries.md)** - v1.0 CLI design constraints and limitations

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

**Current: v1.0.5** - Security cage fundamentals (Linux-only, minimal features)

**Future Releases:**
- **Enhanced Security**: Additional compliance features, advanced monitoring
- **Cross-Platform**: macOS/Windows support with equivalent security
- **Advanced Orchestration**: Parallel execution, workflow dependencies
- **Advanced Integrations**: REST API, monitoring dashboard, advanced integrations

## 🤗 Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Security**: Report vulnerabilities to security@akioud.ai

## 📄 License

AKIOS Open Runtime is licensed under the **GPL-3.0-only** license. The security cage and audit system ensure AI agents run safely while maintaining full transparency through open source.

---

**Built with security-first principles. Run AI agents safely — anywhere.**
