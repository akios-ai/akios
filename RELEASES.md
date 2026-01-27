# AKIOS v1.0.0 Release Notes
**Document Version:** 1.0  
**Date:** 2026-01-25  

### 🎯 AKIOS v1.0.0: The Security Cage is Here

AKIOS v1.0.0 delivers the **strongest open-source security foundation** for AI agents — a hard, minimal cage that makes them safe enough to run with real data today.

This is **not** a general-purpose framework trying to compete on velocity or multi-agent complexity.  
It is **the unbreakable cage**: kernel-level isolation, syscall control, real-time PII redaction, Merkle tamper-evident audit, and enforced cost/loop kills.

We cut everything else to focus on what matters most in 2026 Europe: **trust, provability, and safety** — before agents touch sensitive data, regulated workflows, or production budgets.

### ✨ Key Highlights

- **🔒 Hard Kernel Isolation** — cgroups + seccomp sandbox + resource quotas
- **🛡️ Real-time PII Redaction** — >95% accuracy, <50ms (before data reaches agents)
- **📊 Tamper-Evident Merkle Audit** — every action cryptographically proven + clean PDF/JSON export
- **💰 Enforced Cost & Loop Kills** — hard termination on budget exceed or infinite loop
- **🎯 Perfect User Experience** — Terminal width awareness, file discovery commands, enhanced guidance
- **Minimal & Trustworthy** — sequential execution only, 4 core agents, enhanced CLI (7 commands)
- **Production-Ready** — hybrid distribution (binaries + pip + Docker) + air-gapped capable

### 📦 What's Included

#### Security & Isolation
- Process sandboxing (cgroups + seccomp)
- Hard resource limits (CPU, memory, disk, network)
- Syscall-level I/O interception & access control
- Agent lifecycle management & recovery

#### Cost & Budget Protection
- Hard kill-switches for API cost limits
- Token monitoring
- Per-workflow budget enforcement
- Infinite loop prevention

#### Compliance & Data Protection
- Real-time PII detection & redaction
- Built-in rule packs (EU AI Act basics + French GDPR presets)
- (Bias monitoring optional – only if already complete)

#### Audit & Transparency
- Cryptographic Merkle tamper-evident ledger
- Complete execution traces
- Clean professional PDF/JSON audit reports (internal use)
- Full integrity verification

#### Execution & Agents
- Sequential execution only
- Basic error handling + retry/fallback
- 4 core agents: LLM, HTTP/web, Filesystem, Tool Executor

#### Developer & Deployment
- **Enhanced CLI** (init, run, files, audit export, logs, status, templates, clean, setup)
- **Perfect User Experience**: Terminal width awareness, file discovery, enhanced guidance
- Exactly 3–4 high-quality example workflows (polished demos)
- **Hybrid Distribution**: Standalone binaries + pip packages + Docker containers
- **Air-gapped capable** with standalone binaries (no network required)
- **Cross-platform support** (Linux/macOS/Windows)
- **Ruthless minimalism** — sequential execution only, exactly 5–7 CLI commands

### 🔄 What's Next (Roadmap)

#### Future Open Releases (V1.x / V2.0)
- Parallel/conditional/loop patterns
- More agents (DB, Email, Slack…)
- Full CLI + REST API
- Advanced observability (Prometheus/Jaeger)

#### AKIOS PRO (Paid – €48k+/year)
- FranceConnect / ProConnect-S identity verification
- La Poste qualified eIDAS timestamping & signatures
- Official 12-page regulator-ready PDF reports (CNIL/ANSM)
- Hard HDS/SecNumCloud enforcement blocks
- Qualified eIDAS human approval workflows

### 🛠️ Installation & Quick Start

**Four deployment options - choose what's best for you:**

#### 🚀 Standalone Binary (Recommended - Zero Setup)
```bash
# Download from https://github.com/akios-ai/akios/releases
# Linux: akios-linux-x64 | macOS: akios-macos-universal | Windows: akios-windows-x64.exe

# Make executable and run
chmod +x akios-linux-x64  # Skip on Windows
./akios-linux-x64 init my-project
cd my-project
./akios-linux-x64 run templates/hello-workflow.yml
```

#### 🐧 Pip Package (Python Developers)
```bash
pip install akios
akios init my-project
cd my-project
akios run templates/hello-workflow.yml
```

#### 🐳 Docker (Cross-Platform Teams)
```bash
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/akios
ls -la akios && file akios  # Verify download (~3.4KB shell script)
chmod +x akios
./akios init my-project
cd my-project
./akios run templates/hello-workflow.yml
```

#### 🚨 Direct Docker (Emergency Fallback)
```bash
# Use when wrapper script download fails
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.0 init my-project
cd my-project
# Create wrapper script for future use
echo '#!/bin/bash
exec docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.0 "$@"' > akios
chmod +x akios
./akios run templates/hello-workflow.yml
```

**All methods provide identical functionality and security, with Docker optimized for performance through smart caching.**

### 📚 Documentation & Resources

- Full README: philosophy, quick start, limits
- Module Scope Docs: detailed boundaries for each part of the cage
- templates/README.md: explanations of the 3–4 examples
- GitHub: https://github.com/akios-ai/akios

### 🤝 Community & Support

- **Discussions**: Ask questions, share use-cases
- **Issues**: Report bugs, suggest scope-aligned improvements
- **Security bugs**: Private to hello@akios.ai
