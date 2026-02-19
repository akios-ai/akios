# AKIOS Roadmap
**Document Version:** 1.0.7  
**Date:** 2026-02-19  
**License:** GPL-3.0-only  

This roadmap covers the open-source AKIOS project — the security-cage runtime for AI agents.

---

## Current: AKIOS v1.0 (January 2026)

**Focus:** Strong cross-platform security foundation  
**Status:** ✅ Released and stable

### What's Shipped
- Policy-based container isolation (Docker + native Linux cgroups v2 + seccomp-bpf)
- Real-time PII redaction (50+ patterns, 6 categories, >95% accuracy, <1ms overhead)
- Cryptographic Merkle tamper-evident audit ledger + PDF/JSON export
- Hard cost & infinite loop kill-switches
- 4 core agents: LLM, HTTP, Filesystem, Tool Executor
- Multi-provider LLM support (OpenAI, Anthropic, Grok, Mistral, Gemini)
- 20-command CLI with Rich UI panels
- Docker wrapper + native Linux sandbox
- 6 sector demo workflows (healthcare, banking, insurance, accounting, government, legal)
- 0.47ms enforcement overhead (benchmarked on EC2 t4g.micro ARM64)

---

## Next: v1.0.7 — "Integrity" (Target: March 2026)

**Theme:** Fix critical integrity issues. No new features — only truth.

- **Real compliance scoring** — replace hardcoded scores with actual computed values
- **Audit log integrity** — fix 10K event cap, Merkle coverage gaps, O(n²) appends. Add log rotation
- **Secure data erasure** — overwrite-before-delete for `cage down` (GDPR Art. 17)
- **PII pattern overlaps** — resolve duplicate regexes, fix ICD-10 misclassification
- **Ablation benchmark support** — toggle individual enforcement primitives for research
- **Multi-instance benchmarks** — validate performance across ARM64 and x86_64 instances
- **Workflow validation** — expand `akios workflow` beyond stub
- **Repo hygiene** — remove dead dependencies and duplicate files

---

## v1.0.8 — "Science + Orchestration" (Target: May 2026)

**Theme:** Research-grade evaluation AND workflow improvements.

- **Pluggable PII backend** — abstract detector interface; support regex (default) and Presidio
- **LangGraph integration** — working example of LangGraph tool calls through AKIOS enforcement
- **TLA+ formal specification** — model-checked safety invariants for the enforcement pipeline
- **PII accuracy evaluation** — annotated test corpus with precision/recall/F1 by category
- **Conditional execution** — `condition` field on workflow steps
- **Error recovery & retry** — `retry` and `on_error` fields with configurable backoff
- **Step output piping** — structured JSON output, JSONPath references between steps
- **Engine refactoring** — split monolithic engine.py into focused modules

---

## v1.0.9 — "Integration" (Target: July 2026)

**Theme:** Programmatic access for self-hosted deployments.

- **REST API** — self-hosted FastAPI server (`akios serve`) with workflow execution, audit, compliance, and status endpoints. OpenAPI/Swagger auto-generated
- **Webhook agent** — new agent for workflow event notifications (Slack, Discord, Teams)
- **Parallel step execution** — `parallel:` blocks with per-step sandboxing
- **SQLite state persistence** — replace in-memory state for workflow resume and history

---

## v2.0 — "Platform" (Target: Q4 2026)

**Theme:** From CLI tool to security platform.

- Plugin system for community agents (pip-installable)
- Database agents (PostgreSQL, SQLite with query whitelisting)
- Fan-out / map-reduce execution patterns
- Prometheus metrics + OpenTelemetry traces
- Community template marketplace
- Streaming LLM output with per-token PII filtering
- Multi-tenant isolation

---

## Guiding Principles

1. **Security first** — every feature must preserve or strengthen the cage
2. **Minimalism** — add only what makes the cage more useful
3. **Honesty** — no hardcoded scores, no fake benchmarks, no approximated claims
4. **Community-driven** — priorities shift based on real user needs and contributions
5. **Backward compatible** — workflow YAML is additive only; deprecated CLI flags warn for 2 minor versions

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved. Feature requests and bug reports welcome via GitHub Issues.

