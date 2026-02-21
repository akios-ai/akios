# AKIOS Roadmap
**Document Version:** 1.0.8  
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

## Shipped: v1.0.7 — "Integrity" (February 2026)

**Theme:** Fix critical integrity issues. No new features — only truth.  
**Status:** ✅ Shipped

- ✅ **Real compliance scoring** — replace hardcoded scores with actual computed values
- ✅ **Audit log integrity** — fix 10K event cap, Merkle coverage gaps, O(n²) appends. Add log rotation
- ✅ **Secure data erasure** — overwrite-before-delete for `cage down` (GDPR Art. 17)
- ✅ **PII pattern overlaps** — resolve duplicate regexes, fix ICD-10 misclassification
- ✅ **Ablation benchmark support** — toggle individual enforcement primitives for research
- ✅ **Multi-instance benchmarks** — validate performance across ARM64 and x86_64 instances
- ✅ **Workflow validation** — expand `akios workflow` beyond stub
- ✅ **Repo hygiene** — remove dead dependencies and duplicate files

---

## Current: v1.0.8 — "Science + Orchestration" (Target: March 2026)

**Theme:** Research-grade evaluation AND workflow improvements.  
**Status:** 🔧 In development

- **Pluggable PII backend** — abstract detector interface; support regex (default) and Presidio
- **PII accuracy evaluation** — annotated test corpus with precision/recall/F1 by category
- **Insurance PII patterns** — policy, group, claim, prior-authorization detection
- **context_keywords gate** — suppress false-positive PII matches without surrounding context
- **LangGraph integration** — working example of LangGraph tool calls through AKIOS enforcement
- **TLA+ formal specification** — model-checked safety invariants for the enforcement pipeline
- **Conditional execution** — `condition` field on workflow steps with safe expression evaluator
- **Error recovery & retry** — `on_error` field (skip / fail / retry) with configurable backoff
- **Engine refactoring** — unified output key-probing, `_emit_audit()` helper, logger integration
- **ALLOWED_MODELS to config** — move hardcoded model set to `settings.yaml` / Pydantic settings
- **DNS check dedup** — shared `check_network_available()` utility (was duplicated in 3 files)
- **Weighted compliance scoring** — security 50 %, audit 30 %, cost 20 % (was equal-weight average)
- **Action name unification** — canonical actions synced with AGENTS.md; old names accepted as aliases
- **Config JSON Schema** — auto-generated from Pydantic settings for IDE auto-completion
- **Dead code & tech debt** — remove `gc.collect()`, fix probe-file race, dynamic version in output.json

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

