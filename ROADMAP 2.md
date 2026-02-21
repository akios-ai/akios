# AKIOS Roadmap
**Document Version:** 1.0.9  
**Date:** 2026-02-20  
**License:** GPL-3.0-only  

This roadmap covers the open-source AKIOS project — the security-cage runtime for AI agents.

---

## Foundation: AKIOS v1.0 (January 2026)

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

## Shipped: v1.0.9 — "Science + Orchestration" (February 2026)

**Theme:** Research-grade evaluation AND workflow improvements.  
**Status:** ✅ Shipped

- ✅ **Pluggable PII backend** — `PIIDetectorProtocol` interface; regex (default) + Presidio (stub, deferred to akios-pro)
- ✅ **PII accuracy evaluation** — annotated test corpus with precision/recall/F1 by category
- ✅ **Insurance PII patterns** — policy, group, claim, prior-authorization detection
- ✅ **context_keywords gate** — suppress false-positive PII matches without surrounding context
- ✅ **LangGraph integration** — working example (215 lines) of LangGraph tool calls through AKIOS enforcement
- ✅ **TLA+ formal specification** — 130-line model-checked safety invariants for the enforcement pipeline
- ✅ **Conditional execution** — `condition` field on workflow steps
- ✅ **Error recovery** — `on_error` field (skip / fail / retry)
- ✅ **Engine refactoring (partial)** — unified output key-probing, `_emit_audit()` helper, `_extract_output_value()`
- ✅ **ALLOWED_MODELS to config** — model set in Pydantic settings with `json_schema()` export
- ✅ **Weighted compliance scoring** — security 50%, audit 30%, cost 20%
- ✅ **Action name unification** — canonical actions synced with AGENTS.md; old names accepted as aliases
- ✅ **Config JSON Schema** — auto-generated from Pydantic settings for IDE auto-completion
- ✅ **Dead code & tech debt** — `gc.collect()` removal, probe-file race fix, dynamic version in output.json

### Known Issues Carried Forward
- ⚠️ Condition evaluator uses `eval()` with bypassable token blocklist — fixed in v1.0.9
- ⚠️ Engine grew to 1,643 lines instead of shrinking — split in v1.0.9
- ⚠️ Dockerfile runs as root (non-root user commented out) — fixed in v1.0.9

---

## Current: v1.0.9 — "Hardening" (Target: March 2026)

**Theme:** Fix security vulnerabilities, split the monolith, add programmatic access.  
**Status:** 🔧 In development

### 🔴 P0 — Security (Critical)

- **Non-root Docker container** — uncomment and fix the `akios` user in Dockerfile; containers must not run as root
- **Safe condition evaluator** — replace `eval()` + substring token blocklist with AST-based safe evaluator; eliminate code injection risk

### 🟡 P1 — Architecture

- **Engine split** — break `engine.py` (1,643 lines) into `StepExecutor`, `TemplateRenderer`, `OutputExtractor`, `ConditionEvaluator`; no file > 400 lines
- **REST API** — self-hosted FastAPI server (`akios serve`) with 6 endpoints: `/status`, `/audit/events`, `/audit/verify`, `/workflows`, `/workflows/{id}/run`, `/compliance/report`. OpenAPI auto-generated
- **Print → logging migration** — replace ~380 `print()` calls with structured `logging` module; keep stderr prints for CLI UX only

### 🟢 P2 — Quality

- **SQLite state persistence** — replace in-memory state for workflow resume and historical run queries
- **Retry with backoff** — configurable retry count + exponential backoff for `on_error: retry`
- **PII accuracy corpus expansion** — grow from ~3 samples/pattern to 20+ for real confidence metrics

---

## v1.0.10 — "Scale" (Target: Q3 2026)

**Theme:** Production readiness and community extensibility.

- **Webhook agent** — new agent for workflow event notifications (Slack, Discord, Teams)
- **Parallel step execution** — `parallel:` blocks with per-step sandboxing and atomic budget tracking
- **Plugin system** — pip-installable community agent packages
- **Database agents** — PostgreSQL, SQLite with query whitelisting

---

## v1.0.11+ — "Platform" (Future)

**Theme:** From CLI tool to security platform. Non-binding.

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

