<div align="center">
  <img src="https://raw.githubusercontent.com/akios-ai/akios/main/assets/logo.png" alt="AKIOS" width="200"/>
  <h1>AKIOS</h1>
  <p><strong>The open-source security cage for AI agents.</strong></p>
  <p>Sandbox · PII Redaction · Merkle Audit · Cost Kill-Switches</p>

  <a href="https://pypi.org/project/akios/"><img src="https://img.shields.io/pypi/v/akios?color=blue&label=PyPI" alt="PyPI"></a>
  <a href="https://pypi.org/project/akios/"><img src="https://img.shields.io/pypi/pyversions/akios" alt="Python"></a>
  <a href="https://github.com/akios-ai/akios/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--only-green" alt="License"></a>
  <a href="https://github.com/akios-ai/akios/stargazers"><img src="https://img.shields.io/github/stars/akios-ai/akios?style=social" alt="Stars"></a>
  <a href="https://github.com/akios-ai/akios"><img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey" alt="Platform"></a>

</div>

---

AKIOS wraps any AI agent in a **hardened security cage** — kernel-level process isolation (seccomp-bpf + cgroups v2), real-time PII redaction across 50+ patterns, cryptographic Merkle audit trails, and automatic cost kill-switches — so you can deploy AI workflows in regulated environments without building security from scratch.

```
┌─────────────────────────────────────────────────────────┐
│                    AKIOS Security Cage                   │
│                                                         │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  │
│   │   LLM   │  │  HTTP   │  │  File   │  │   Tool   │  │
│   │  Agent  │  │  Agent  │  │  Agent  │  │ Executor │  │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬─────┘  │
│        │            │            │             │        │
│   ┌────▼────────────▼────────────▼─────────────▼────┐   │
│   │           Security Primitives Layer             │   │
│   │  PII Scan → Sandbox → Budget → Audit → Merkle  │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│   🔒 seccomp-bpf  🛡️ cgroups v2  📋 Merkle tree       │
│   💰 cost kills   🚫 50+ PII     🌐 HTTPS whitelist   │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install
pip install akios

# Create a project
akios init my-project && cd my-project

# Configure your LLM provider
akios setup

# Run your first secure workflow
akios run templates/hello-workflow.yml

# Check security status
akios status
```

**Docker** (all platforms):
```bash
curl -O https://raw.githubusercontent.com/akios-ai/akios/main/src/akios/cli/data/wrapper.sh
mv wrapper.sh akios && chmod +x akios
./akios init my-project && cd my-project
./akios run templates/hello-workflow.yml
```

## Why AKIOS?

**The problem:** AI agents can leak sensitive data, run up massive bills, execute dangerous code, and leave no audit trail. Every team building with LLMs faces the same security engineering burden.

**The solution:** AKIOS provides **compliance-by-construction** — security guarantees that are architectural, not bolted on. Your workflows run inside a cage where violations are physically impossible, not just discouraged.

| Without AKIOS | With AKIOS |
|---------------|------------|
| PII leaks to LLM providers | Automatic redaction before any API call |
| Runaway API costs | Hard budget limits with kill-switches |
| No audit trail for compliance | Cryptographic Merkle-chained logs |
| Manual security reviews | Kernel-enforced process isolation |
| Hope-based security | Proof-based security |

## Key Features

🔒 **Kernel-Hard Sandbox** — seccomp-bpf syscall filtering + cgroups v2 resource isolation on native Linux. Policy-based isolation on Docker (all platforms).

🛡️ **PII Redaction** — 50+ detection patterns across 6 categories (personal, financial, health, digital, communication, location) including NPI, DEA, and medical records. Redaction happens before data reaches any LLM.

📊 **Merkle Audit Trail** — Every action is cryptographically chained. Tamper-evident JSONL logs with SHA-256 proofs. Export to JSON for compliance reporting.

💰 **Cost Kill-Switches** — Hard budget limits ($1 default) with automatic workflow termination. Token tracking across all providers.

🌐 **HTTPS Whitelist** — Network access locked to explicit domain allowlist. LLM APIs always pass through. Plain HTTP blocked in sandbox mode.

🤖 **5 LLM Providers** — OpenAI, Anthropic, Grok (xAI), Mistral, Gemini. Swap providers in one line of config.

🗑️ **Data Destruction** — `cage down` destroys all session data (audit logs, inputs, outputs). Nothing remains.

🏥 **Industry Templates** — Healthcare (HIPAA), Banking (PCI-DSS), Insurance, Accounting (SOX), Government (FedRAMP), Legal — ready-to-run sector workflows.

## How It Works

AKIOS orchestrates YAML-defined workflows through 4 secure agents:

```yaml
# workflow.yml — every step runs inside the cage
name: "document-analysis"
steps:
  - name: "read-document"
    agent: filesystem
    action: read
    parameters:
      path: "data/input/report.pdf"

  - name: "analyze-with-ai"
    agent: llm
    action: complete
    parameters:
      prompt: "Summarize this document: {previous_output}"
      model: "gpt-4o"
      max_tokens: 500
```

```bash
akios run workflow.yml
# ✅ PII automatically redacted from prompt
# ✅ Budget tracked ($0.003 of $1.00 used)
# ✅ Audit event logged with Merkle proof
# ✅ Output saved to data/output/run_*/
```

## Security Levels

| Environment | Isolation | PII | Audit | Budget |
|-------------|-----------|-----|-------|--------|
| **Native Linux** (recommended) | seccomp-bpf + cgroups v2 | ✅ | ✅ | ✅ |
| **Docker** (all platforms) | Container + policy-based | ✅ | ✅ | ✅ |

Native Linux provides kernel-level guarantees. Docker provides strong, reliable security across macOS, Linux, and Windows.

## CLI at a Glance

```bash
akios init my-project          # Create secure workspace
akios setup                    # Configure LLM provider (interactive)
akios run workflow.yml         # Execute workflow in cage
akios status                   # Security & budget dashboard
akios status --budget          # Cost tracking breakdown
akios cage up / down           # Activate / destroy cage + data
akios protect scan file.txt    # Scan file for PII
akios protect show-prompt w.yml # Preview what the LLM sees
akios audit verify             # Verify Merkle integrity
akios audit export --format json # Export for compliance
akios doctor                   # System health check
akios templates list           # Browse workflow templates
akios http GET https://...     # Secure HTTP request
```

## Performance

Measured on AWS EC2 t4g.micro (ARM64, 1 GB RAM) — the smallest instance available:

| Operation | Latency |
|-----------|---------|
| Full security pipeline (PII + policy + audit + budget) | **0.47 ms** |
| PII scan (50+ patterns) | 0.46 ms |
| SHA-256 Merkle hash | 0.001 ms |
| CLI cold start (Docker) | ~1.4 s |

Sub-millisecond overhead means security adds virtually zero cost to your workflows.

> Reproducible: see [EC2 Performance Testing](docs/ec2-performance-testing.md) for methodology and validation procedures.

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](GETTING_STARTED.md) | 3-minute setup guide |
| [CLI Reference](docs/cli-reference.md) | All commands and flags |
| [Configuration](docs/configuration.md) | Settings, `.env`, `config.yaml` |
| [Security](docs/security.md) | Architecture and threat model |
| [Agents](AGENTS.md) | Filesystem, HTTP, LLM, Tool Executor |
| [Deployment](docs/deployment.md) | Docker, native Linux, EC2 |
| [Troubleshooting](TROUBLESHOOTING.md) | Common issues and fixes |
| [Changelog](CHANGELOG.md) | Release history |

## Architecture

```
src/akios/
├── cli/            # 18 CLI commands (argparse)
├── core/
│   ├── engine.py   # Sequential workflow orchestrator
│   ├── agents/     # LLM, HTTP, Filesystem, ToolExecutor
│   ├── audit/      # Merkle-chained JSONL ledger
│   └── sandbox.py  # seccomp-bpf + cgroups v2
├── security/
│   └── pii/        # 50+ regex patterns, 6 categories
└── config/         # YAML + .env configuration
```

## Research

AKIOS introduces **compliance-by-construction** — the idea that security guarantees should be architectural properties of the runtime, not features that can be misconfigured or bypassed.

Our NeurIPS 2026 submission formalizes this paradigm. Preprint coming soon on arXiv.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/akios-ai/akios.git
cd akios
make build          # Build Docker image
make test           # Run test suite
```

Good first issues are tagged with [`good first issue`](https://github.com/akios-ai/akios/labels/good%20first%20issue).

## Community

- 📖 [Documentation](docs/README.md)
- 💬 [GitHub Discussions](https://github.com/akios-ai/akios/discussions)
- 🐛 [Issue Tracker](https://github.com/akios-ai/akios/issues)
- 🔒 Security issues → [security@akioud.ai](mailto:security@akioud.ai) (private disclosure)

## ⚖️ Legal & Disclaimers

> **EU AI Act:** AKIOS is not designed for "high-risk" use cases under the EU AI Act. For such deployments, consult a compliance expert and implement additional regulatory controls on top of AKIOS.

**AKIOS is provided "AS IS" without warranty of any kind.** By using AKIOS you acknowledge:

- **You are responsible for** your own API keys, cloud costs (AWS/GCP/Azure), IAM configurations, credential management, and infrastructure security. AKIOS cost kill-switches cover LLM API spend only — not compute, storage, or data transfer.
- **Docker mode** provides strong policy-based security but does **not** enforce host filesystem permissions or kernel-level seccomp-bpf isolation. For maximum security, use native Linux with sudo.
- **Performance varies** by instance type, region, load, and configuration. Published benchmarks are measured on AWS EC2 t4g.micro (ARM64) in us-east-1 and may not match your environment.
- **PII redaction** uses regex pattern matching (50+ patterns, >95% accuracy) — it is not a substitute for professional data governance. Review output before sharing with external parties.
- **Audit logs** in Docker may lose up to ~100 events if the container is forcefully killed (SIGKILL) during a flush window. Use native Linux for zero-loss audit durability.

AKIOS is **not responsible** for: cloud infrastructure charges, credential leaks, data breaches from misconfigured deployments, performance on untested platforms, or regulatory compliance decisions. See [LEGAL.md](LEGAL.md) and [SECURITY.md](SECURITY.md) for full details.

## License

AKIOS is licensed under [GPL-3.0-only](LICENSE).
See [NOTICE](NOTICE), [LEGAL.md](LEGAL.md), and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

---

<div align="center">
  <strong>Run AI agents safely — anywhere.</strong>
  <br><br>
  <a href="GETTING_STARTED.md">Get Started</a> · <a href="docs/cli-reference.md">CLI Reference</a> · <a href="AGENTS.md">Agents</a> · <a href="CHANGELOG.md">Changelog</a>
</div>
