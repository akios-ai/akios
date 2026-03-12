<div align="center">
  <img src="https://raw.githubusercontent.com/akios-ai/akios/main/assets/logo.png" alt="AKIOS" width="180"/>
  <h1>AKIOS</h1>
  <h3>The open-source security cage for AI agents</h3>
  <p>
    <strong>Kernel-hard sandbox</strong> · <strong>44 PII patterns</strong> · <strong>Merkle audit trail</strong> · <strong>Cost kill-switches</strong>
  </p>

  <a href="https://pypi.org/project/akios/"><img src="https://img.shields.io/pypi/v/akios?color=%2334D058&label=PyPI" alt="PyPI"></a>
  <a href="https://pypi.org/project/akios/"><img src="https://img.shields.io/pypi/pyversions/akios?color=%2334D058" alt="Python"></a>
  <a href="https://github.com/akios-ai/akios/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--only-blue" alt="License"></a>
  <a href="https://github.com/akios-ai/akios"><img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey" alt="Platform"></a>
  <a href="https://github.com/akios-ai/akios/stargazers"><img src="https://img.shields.io/github/stars/akios-ai/akios?style=social" alt="Stars"></a>
</div>

<br>

<div align="center">

**AKIOS wraps any AI agent in a hardened security cage** — kernel-level process isolation,<br>
real-time PII redaction, cryptographic Merkle audit trails, and automatic cost kill-switches —<br>
so you can deploy AI workflows in regulated environments without building security from scratch.

</div>

<br>

<div align="center">

[Quick Start](#-quick-start) · [Architecture](#-architecture) · [Features](#-key-features) · [Documentation](#-documentation) · [Contributing](#-contributing)

</div>

<br>

## 🏗️ Architecture

> Every workflow step passes through five security layers before anything touches the outside world.

```
              ┌────────────────────────────────────┐
              │        Untrusted AI Agents         │
              │        LLMs, Code, Plugins         │
              └──────────────────┬─────────────────┘
                                 │
                                 ▼
╔════════════════════════════════════════════════════════════════╗
║                     AKIOS SECURITY RUNTIME                     ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐  ║
║  │ 1. Policy Engine    allowlist verification               │  ║
║  │ 2. Kernel Sandbox   seccomp-bpf + cgroups v2             │  ║
║  │ 3. PII Redaction    44 patterns, 6 categories            │  ║
║  │ 4. Budget Control   cost kill-switches, token limits     │  ║
║  │ 5. Audit Ledger     Merkle tree, SHA-256, JSONL          │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                ║
╚════════════════════════════════╤═══════════════════════════════╝
                                 │
                                 ▼
              ┌────────────────────────────────────┐
              │      Protected Infrastructure      │
              │       APIs, Databases, Cloud       │
              └────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
pip install akios
akios init my-project && cd my-project
akios setup                              # Configure LLM provider (interactive)
akios run templates/hello-workflow.yml    # Run inside the security cage
```

<details>
<summary><b>📦 Docker (all platforms — macOS, Linux, Windows)</b></summary>

```bash
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios && chmod +x akios
./akios init my-project && cd my-project
./akios run templates/hello-workflow.yml
```
</details>

### What happens when you run a workflow

```
$ akios run workflow.yml

╔══════════════════════════════════════════════════════════╗
║                   AKIOS Security Cage                    ║
╠══════════════════════════════════════════════════════════╣
║  🔒 Sandbox:   ACTIVE (seccomp-bpf + cgroups v2)        ║
║  🚫 PII Scan:  44 patterns loaded                       ║
║  💰 Budget:    $1.00 limit ($0.00 used)                  ║
║  📋 Audit:     Merkle chain initialized                  ║
╚══════════════════════════════════════════════════════════╝

  ▶ Step 1/3: read-document ─────────────────────────────
    Agent: filesystem │ Action: read
    ✓ PII redacted: 3 patterns found (SSN, email, phone)
    ✓ Audit event #1 logged

  ▶ Step 2/3: analyze-with-ai ───────────────────────────
    Agent: llm │ Model: gpt-4o │ Tokens: 847
    ✓ Prompt scrubbed before API call
    ✓ Cost: $0.003 of $1.00 budget
    ✓ Audit event #2 logged

  ▶ Step 3/3: save-results ─────────────────────────────
    Agent: filesystem │ Action: write
    ✓ Output saved to data/output/run_20250211_143052/
    ✓ Audit event #3 logged

══════════════════════════════════════════════════════════
  ✅ Workflow complete │ 3 steps │ $0.003 │ 0 PII leaked
══════════════════════════════════════════════════════════
```

## 🎯 Why AKIOS?

AI agents can **leak PII** to LLM providers, **run up massive bills**, execute **dangerous code**, and leave **no audit trail**. Every team building with LLMs faces this security engineering burden.

AKIOS provides **compliance-by-construction** — security guarantees that are architectural, not bolted on:

| | Without AKIOS | With AKIOS |
|:---:|:---|:---|
| 🚫 | PII leaks to LLM providers | **Automatic redaction** before any API call |
| 💸 | Runaway API costs | **Hard budget limits** with kill-switches |
| 📋 | No audit trail for compliance | **Cryptographic Merkle-chained** logs |
| 🔓 | Manual security reviews | **Kernel-enforced** process isolation |
| 🤞 | Hope-based security | **Proof-based** security |

## 🛡️ Key Features

<table>
<tr>
<td width="50%">

### 🔒 Kernel-Hard Sandbox
seccomp-bpf syscall filtering + cgroups v2 resource isolation on native Linux. Policy-based isolation on Docker (all platforms).

### 🚫 PII Redaction Engine
44 detection patterns across 6 categories: personal, financial, health, digital, communication, location. Covers SSN, credit cards, emails, phones, addresses, API keys, and more. Redaction happens **before** data reaches any LLM.

### 📋 Merkle Audit Trail
Every action is cryptographically chained. Tamper-evident JSONL logs with SHA-256 proofs. Export to JSON for compliance reporting.

</td>
<td width="50%">

### 💰 Cost Kill-Switches
Hard budget limits ($1 default) with automatic workflow termination. Token tracking across all providers. Real-time `akios status --budget` dashboard.

### 🤖 Multi-Provider LLM Support
OpenAI, Anthropic, Grok (xAI), Mistral, Gemini, AWS Bedrock, Ollama — swap providers in one line of config. All calls are sandboxed, audited, and budget-tracked.

</td>
</tr>
</table>

## 📝 Workflow Schema

AKIOS orchestrates YAML-defined workflows through **6 secure agents** — each running inside the security cage:

```yaml
# workflow.yml — every step runs inside the cage
name: "document-analysis"
steps:
  - name: "read-document"
    agent: filesystem           # 📁 Path-whitelisted file access
    action: read
    parameters:
      path: "data/input/report.pdf"

  - name: "analyze-with-ai"
    agent: llm                  # 🤖 Token-tracked, PII-scrubbed
    action: complete
    parameters:
      prompt: "Summarize this document: {previous_output}"
      model: "gpt-4o"
      max_tokens: 500

  - name: "notify-team"
    agent: http                 # 🌐 Domain-whitelisted, rate-limited
    action: post
    parameters:
      url: "https://api.example.com/webhook"
      json:
        summary: "{previous_output}"
```

<details>
<summary><b>🔍 Preview what the LLM actually sees (after PII redaction)</b></summary>

```bash
$ akios protect show-prompt workflow.yml

Interpolated prompt (redacted):
  "Summarize this document: The patient [NAME_REDACTED] with
   SSN [SSN_REDACTED] was seen at [ADDRESS_REDACTED]..."

# 3 PII patterns redacted before reaching OpenAI
```
</details>

## 🔐 Security Levels

| Environment | Isolation | PII | Audit | Budget | Best For |
|:---|:---|:---:|:---:|:---:|:---|
| **Native Linux** | seccomp-bpf + cgroups v2 | ✅ | ✅ | ✅ | Production, maximum guarantees |
| **Docker** (all platforms) | Container + policy-based | ✅ | ✅ | ✅ | Development, cross-platform |

> **Native Linux** provides kernel-level guarantees where dangerous syscalls are physically blocked. **Docker** provides strong, reliable security across macOS, Linux, and Windows.

## ⌨️ CLI Reference

<table>
<tr><th>Command</th><th>Description</th></tr>
<tr><td><code>akios init my-project</code></td><td>Create secure workspace with templates</td></tr>
<tr><td><code>akios setup</code></td><td>Configure LLM provider (interactive)</td></tr>
<tr><td><code>akios run workflow.yml</code></td><td>Execute workflow inside security cage</td></tr>
<tr><td><code>akios workflow validate w.yml</code></td><td>Validate workflow YAML against schema</td></tr>
<tr><td><code>akios status</code></td><td>Security & budget dashboard</td></tr>
<tr><td><code>akios status --budget</code></td><td>Cost tracking breakdown per workflow</td></tr>
<tr><td><code>akios cage up / down</code></td><td>Activate / destroy cage + all data</td></tr>
<tr><td><code>akios cage up --no-pii --no-audit</code></td><td>Ablation mode (benchmarking)</td></tr>
<tr><td><code>akios cage down --passes N</code></td><td>Secure overwrite with N passes</td></tr>
<tr><td><code>akios protect scan file.txt</code></td><td>Scan file for PII patterns</td></tr>
<tr><td><code>akios protect show-prompt w.yml</code></td><td>Preview what the LLM sees (redacted)</td></tr>
<tr><td><code>akios audit verify</code></td><td>Verify Merkle chain integrity</td></tr>
<tr><td><code>akios audit stats</code></td><td>Audit ledger statistics (event count, Merkle root)</td></tr>
<tr><td><code>akios audit rotate</code></td><td>Rotate audit log with Merkle chain linkage</td></tr>
<tr><td><code>akios audit export --format json</code></td><td>Export audit logs for compliance</td></tr>
<tr><td><code>akios doctor</code></td><td>System health check</td></tr>
<tr><td><code>akios templates list</code></td><td>Browse industry workflow templates</td></tr>
<tr><td><code>akios http GET https://...</code></td><td>Secure HTTP request via agent</td></tr>
</table>

## ⚡ Performance

> Measured on AWS EC2 **t4g.micro** (ARM64, 1 GB RAM) — the smallest instance available.

| Operation | Latency | Notes |
|:---|:---:|:---|
| Full security pipeline | **0.47 ms** | PII + policy + audit + budget |
| PII scan (44 patterns) | 0.46 ms | All 6 categories |
| SHA-256 Merkle hash | 0.001 ms | Per audit event |
| CLI cold start (Docker) | ~1.4 s | One-time startup |

**Sub-millisecond overhead** means security adds virtually zero cost to your workflows.

<details>
<summary><b>📊 Reproducibility & methodology</b></summary>

All benchmarks are reproducible. See [EC2 Performance Testing](docs/ec2-performance-testing.md) for the full methodology, validation procedures, and instructions to run on your own infrastructure.

</details>

## 📚 Documentation

| | Guide | Description |
|:---:|:---|:---|
| 🚀 | [Getting Started](GETTING_STARTED.md) | 3-minute setup guide |
| ⌨️ | [CLI Reference](docs/cli-reference.md) | All commands and flags |
| ⚙️ | [Configuration](docs/configuration.md) | Settings, `.env`, `config.yaml` |
| 🔒 | [Security](docs/security.md) | Architecture and threat model |
| 🤖 | [Agents](AGENTS.md) | Filesystem, HTTP, LLM, Tool Executor, Webhook, Database |
| 🐳 | [Deployment](docs/deployment.md) | Docker, native Linux, EC2 |
| 🔧 | [Troubleshooting](TROUBLESHOOTING.md) | Common issues and fixes |
| 📝 | [Changelog](CHANGELOG.md) | Release history |

## 🏛️ Project Structure

<details>
<summary><b>Click to expand source tree</b></summary>

```
src/akios/
├── cli/                        # 21 CLI commands (argparse)
│   └── commands/               # audit, compliance, doctor, http, protect, run, ...
├── config/                     # YAML + .env configuration, themes, detection
├── core/
│   ├── analytics/              # Cost tracking (cost_tracker.py)
│   ├── audit/                  # Merkle-chained JSONL ledger
│   │   └── merkle/             # SHA-256 Merkle tree (tree.py, node.py)
│   ├── compliance/             # Security posture scoring
│   ├── runtime/
│   │   ├── agents/             # LLM, HTTP, Filesystem, ToolExecutor, Webhook, Database
│   │   ├── engine/             # Workflow orchestrator + kill switches
│   │   ├── llm_providers/      # OpenAI, Anthropic, Grok, Mistral, Gemini, Bedrock, Ollama
│   │   └── workflow/           # YAML parser + validator
│   └── ui/                     # Rich terminal output, PII display, colors
└── security/
    ├── pii/                    # 44 regex patterns, 6 categories (detector, redactor, rules)
    ├── sandbox/                # cgroups v2 resource isolation (manager, quotas)
    ├── syscall/                # seccomp-bpf policy + interceptor
    └── validation.py           # Runtime security validation
```

</details>

## 🔬 Research

AKIOS introduces **compliance-by-construction** — the idea that security guarantees should be architectural properties of the runtime, not features that can be misconfigured or bypassed.

> Our NeurIPS 2026 submission formalizes this paradigm. Preprint coming soon on arXiv.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/akios-ai/akios.git
cd akios
make build    # Build Docker image
make test     # Run test suite
```

Good first issues are tagged with [`good first issue`](https://github.com/akios-ai/akios/labels/good%20first%20issue).

## 💬 Community

- 📖 [Documentation](docs/README.md)
- 💬 [GitHub Discussions](https://github.com/akios-ai/akios/discussions)
- 🐛 [Issue Tracker](https://github.com/akios-ai/akios/issues)
- 🔒 Security issues → [security@akioud.ai](mailto:security@akioud.ai) (private disclosure)

<details>
<summary><b>⚖️ Legal & Disclaimers</b></summary>

> **EU AI Act:** AKIOS is not designed for "high-risk" use cases under the EU AI Act. For such deployments, consult a compliance expert and implement additional regulatory controls on top of AKIOS.

**AKIOS is provided "AS IS" without warranty of any kind.** By using AKIOS you acknowledge:

- **You are responsible for** your own API keys, cloud costs (AWS/GCP/Azure), IAM configurations, credential management, and infrastructure security. AKIOS cost kill-switches cover LLM API spend only — not compute, storage, or data transfer.
- **Docker mode** provides strong policy-based security but does **not** enforce host filesystem permissions or kernel-level seccomp-bpf isolation. For maximum security, use native Linux with sudo.
- **Performance varies** by instance type, region, load, and configuration. Published benchmarks are measured on AWS EC2 t4g.micro (ARM64) in us-east-1 and may not match your environment.
- **PII redaction** uses regex pattern matching (44 patterns, >95% accuracy) — it is not a substitute for professional data governance. Review output before sharing with external parties.
- **Audit logs** in Docker may lose up to ~100 events if the container is forcefully killed (SIGKILL) during a flush window. Use native Linux for zero-loss audit durability.

AKIOS is **not responsible** for: cloud infrastructure charges, credential leaks, data breaches from misconfigured deployments, performance on untested platforms, or regulatory compliance decisions. See [LEGAL.md](LEGAL.md) and [SECURITY.md](SECURITY.md) for full details.

</details>

## 🏢 Need More?

AKIOS covers 44 PII patterns, 6 agents, and full audit logging for most compliance workflows. If your organization needs **extended PII coverage** (50+ patterns including jurisdiction-specific identifiers), **governance dashboards**, or **dedicated support**, visit [akioud.ai](https://akioud.ai) to learn about our commercial offerings.

## 🔗 Related Projects

**[EnforceCore](https://github.com/akios-ai/EnforceCore)** — The open-source enforcement library (Apache-2.0) for AI agents. EnforceCore provides general-purpose policy enforcement, PII redaction, and audit trails for any agent framework. AKIOS is the complete production runtime built on top of it, adding kernel-level sandboxing, comprehensive PII redaction, workflow orchestration, and compliance reporting.

## 📄 License

AKIOS is licensed under [GPL-3.0-only](LICENSE).
See [NOTICE](NOTICE), [LEGAL.md](LEGAL.md), and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

---

<div align="center">
  <strong>Run AI agents safely — anywhere.</strong>
  <br><br>
  <a href="GETTING_STARTED.md">Get Started</a> · <a href="docs/cli-reference.md">CLI Reference</a> · <a href="AGENTS.md">Agents</a> · <a href="CHANGELOG.md">Changelog</a>
  <br><br>
  <sub>Built by <a href="https://github.com/akios-ai">akios-ai</a> · Licensed under <a href="LICENSE">GPL-3.0-only</a></sub>
</div>
