# AKIOS Roadmap
**Document Version:** 1.2.2  
**Date:** 2026-02-24  
**License:** GPL-3.0-only  

This roadmap covers the open-source AKIOS project — the security-cage runtime for AI agents.

> **Two-project model:** AKIOS (GPL-3.0) is the complete production runtime. [EnforceCore](https://github.com/akios-ai/EnforceCore) (Apache-2.0) is the general-purpose enforcement library. Starting from v1.2.0, AKIOS will use EnforceCore as its enforcement foundation while keeping its unique value: kernel sandbox, healthcare PII patterns, workflow engine, agents, CLI, and compliance reports.

> **Versioning note:** Releases v1.0.5 through v1.0.15 added significant new features (REST API, AWS Bedrock provider, `--json-output`, Rich UI, conditional execution, etc.) that per strict Semantic Versioning should have incremented the minor version. We are correcting this going forward: **v1.0.16 is the final patch release** in the v1.0.x series (bug fixes only), after which new features will ship under **v1.1.0+** with proper semver compliance.

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

## Shipped: v1.0.8 — "Science + Orchestration" (February 2026)

**Theme:** Research-grade evaluation AND workflow improvements.  
**Status:** ✅ Shipped

- ✅ **Pluggable PII backend** — `PIIDetectorProtocol` interface; regex (default) + Presidio (stub)
- ✅ **PII accuracy evaluation** — annotated test corpus with precision/recall/F1 by category
- ✅ **Insurance PII patterns** — policy, group, claim, prior-authorization detection
- ✅ **context_keywords gate** — suppress false-positive PII matches without surrounding context
- ✅ **LangGraph integration** — working example (215 lines) of LangGraph tool calls through AKIOS enforcement
- ✅ **TLA+ formal specification** — 130-line model-checked safety invariants for the enforcement pipeline
- ✅ **Conditional execution** — `condition` field on workflow steps
- ✅ **Error recovery** — `on_error` field (skip / fail / retry)
- ✅ **Weighted compliance scoring** — security 50%, audit 30%, cost 20%
- ✅ **Action name unification** — canonical actions synced with AGENTS.md; old names accepted as aliases
- ✅ **Config JSON Schema** — auto-generated from Pydantic settings for IDE auto-completion

---

## Shipped: v1.0.9 — "Hardening" (February 2026)

**Theme:** Fix security vulnerabilities, split the monolith, add programmatic access.  
**Status:** ✅ Shipped

- ✅ **Non-root Docker container** — containers no longer run as root
- ✅ **Safe condition evaluator** — AST-based evaluator replaces `eval()` + token blocklist
- ✅ **Engine split** — monolith broken into 7 focused modules (no file >400 lines)
- ✅ **REST API (`akios serve`)** — self-hosted FastAPI server with 6 endpoints, OpenAPI auto-generated
- ✅ **Print → logging migration** — structured logging throughout
- ✅ **Retry with exponential backoff** — configurable `max_retries`, `base_delay`, `backoff_factor`

---

## Shipped: v1.0.10 through v1.0.11 — Security & Quality (February 2026)

**Status:** ✅ Shipped

- ✅ **v1.0.10** — `os.system` removal, bare `except` fixes, `apply_all_quotas` enforcement, engine dead stub cleanup, 55 new tests (1,495 total)
- ✅ **v1.0.11** — Release automation with SHA-256 manifests, `pytest.ini` for Python 3.14 compatibility, code quality fixes

---

## Shipped: v1.0.12 — "Structured Output" (February 2026)

**Status:** ✅ Shipped

- ✅ **`--json-output` flag** — machine-readable structured JSON output for SDK/CI consumers
- ✅ **Token tracking** — per-call and per-session token usage statistics
- ✅ **PII metadata** — `pii_redactions_applied` and `pii_patterns_found` in LLM responses

---

## Shipped: v1.0.13 — "AWS Bedrock" (February 2026)

**Status:** ✅ Shipped

- ✅ **AWS Bedrock provider** — IAM-authenticated LLM calls (Claude, Llama, Titan models)
- ✅ **Wrapper version fix** — `detect_version()` reads dynamically from `VERSION` file
- ✅ **Pre-release gate hardening** — P5a–P5d version sync checks
- ✅ **PyPDF2 → pypdf migration** — replaced deprecated dependency
- ✅ **Python 3.9+ requirement** — dropped Python 3.8 (EOL)

---

## Shipped: v1.0.14 — "End-User Testing" (February 2026)

**Status:** ✅ Shipped

- ✅ 13 end-user testing issues fixed (template bundling, Docker prompt bypass, etc.)

---

## Shipped: v1.0.15 — "SDK Integration" (February 2026)

**Status:** ✅ Shipped

- ✅ 7 P0 + 1 P1 SDK integration fixes (Pydantic extra vars, JSON error schema, Bedrock pricing/throttling)

---

## Shipped: v1.0.16 — "Beta Tester Fixes" (February 2026)

**Theme:** Fix 11 verified bugs from independent beta testing. Bug fixes only — no new features.
**Status:** ✅ Shipped

> These bugs were reported by an independent first-time tester on Ubuntu 24.04 / GitHub Codespaces and verified against source code. 4 additional reported bugs were investigated and rejected as false positives.

### 🔴 P0 — Critical (2)

- **REST API audit/verify broken** — `/api/v1/audit/verify` calls nonexistent `verify_chain()` and `merkle_root` on `AuditLedger`. Must use `verify_integrity()` and actual ledger API.
- **`setup --mock-mode` still prompts** — `force` flag not propagated to `run_first_time_setup()`, causing `input()` prompts in non-interactive/CI environments.

### 🟡 P1 — High (8)

- **HTTP agent rejects uppercase methods** — `akios http GET` fails; argparse `choices` are lowercase-only with no normalization.
- **HTTP agent missing HEAD/OPTIONS** — Only 5 methods registered (GET, POST, PUT, DELETE, PATCH); HEAD and OPTIONS missing.
- **`--json-output` leaks Rich to stdout** — Template switch messages and info prints leak to stdout before the `--json-output` flag is checked.
- **`AKIOS_JSON_MODE` env var is dead** — Set in `main.py` but never propagated to any command. Only triggers on config validation errors.
- **REST API workflow run incomplete** — Response missing `total_steps` and `output_directory`; engine return dict doesn't include them.
- **Testing subcommand names don't match docs** — Docs say `show-notes`/`clear-notes`/`log-issue`; actual subcommands are `notes`/`clear`/`log`.
- **Timeline doesn't work** — Searches for `*.json` files but audit stores `*.jsonl`.
- **`--show-environment` doesn't exist** — Neither the CLI flag nor a `config` subcommand is registered; documented in detection-system.md but never implemented.

### 🟢 P2 — Medium (1)

- **`EnvironmentInfo` API mismatches docs** — 6+ attribute/type mismatches between `detection.py` and `detection-system.md` (e.g., `is_ci` vs `ci_type`, `has_unicode_support` vs `unicode_capable`).

### Documentation Fixes (alongside code fixes)

- Sync `docs/cli-reference.md` testing subcommand names with actual implementation
- Sync `docs/detection-system.md` with actual `EnvironmentInfo` attributes
- Remove or implement `--show-environment` from docs
- Fix REST API endpoint documentation for `/audit/verify`

### ❌ Rejected Bugs (Not Included)

| Bug | Claim | Reason for Rejection |
|-----|-------|---------------------|
| BUG-03 | `init` shows Docker-style `./akios` after pip install | Dynamic `get_command_prefix()` works correctly; already fixed in v1.0.14 |
| BUG-12 | Duplicate events in audit logs | Audit emission path is clean; `_emit_audit()` helper has no double-emission |
| BUG-15 | `init` silently overwrites from parent directory | Same `force` guard applies to both local and parent config detection |

---

## Shipped: v1.1.0 — "Scale" (February 2026)

**Theme:** Production readiness and community extensibility. First proper semver minor release.
**Status:** ✅ Shipped

- ✅ **Webhook agent** — new agent for workflow event notifications (Slack, Discord, Teams)
- ✅ **Parallel step execution** — `parallel:` blocks with ThreadPoolExecutor and thread-safe context
- ✅ **Plugin system** — pip-installable community agent packages via entry points
- ✅ **Database agents** — PostgreSQL, SQLite with query whitelisting and DDL blocking
- ✅ **`doctor` command redesign** — 9 diagnostic checks with actionable fix suggestions

---

## Shipped: v1.2.0 — "Foundation" (February 2026)

**Status:** ✅ Shipped

**Theme:** Begin EnforceCore integration — adopt the shared enforcement foundation without losing AKIOS identity.

> **Context:** [EnforceCore](https://github.com/akios-ai/EnforceCore) (Apache-2.0) is AKIOUD AI's open enforcement library. AKIOS uses it as an OPTIONAL dependency while keeping its own unique value: kernel sandbox, healthcare PII, workflow engine, agents, CLI, and compliance reports.

- **EnforceCore as optional dependency** — `pip install akios[enforcecore]` for enhanced features
- **Secret detection** — 11-category API key/token scanner via EnforceCore (`akios protect secrets`)
- **Content rules** — shell injection, SQL injection, path traversal detection in Tool Executor and Database agents
- **EU AI Act compliance reports** — generate Article 9, 13, 14, 52 reports (`akios compliance report`)
- **PII bridge** — register AKIOS's 50+ healthcare patterns into EnforceCore's `PatternRegistry` for unified scanning
- **Unicode hardening** — homoglyph/encoding evasion detection for PII
- **SQLite + PostgreSQL audit backends** — optional storage alongside default JSONL
- **Lifecycle hooks** — pre_workflow, post_workflow, step_complete events

**What stays AKIOS-only:** Kernel sandbox (seccomp-bpf + cgroups v2), 50+ healthcare PII patterns (GPL-3.0), workflow engine, 6 agents, CLI, compliance reports. AKIOS works fully without EnforceCore.

---

## Next: v1.3.0 — "Unified Audit" (Target: Q3 2026)

**Theme:** Merkle format bridge + production-grade audit backends.

> **Known limitation (v1.2.3):** AKIOS and EnforceCore use incompatible Merkle chain formats (AKIOS: binary tree, EnforceCore: linear chain). v1.3.0 must implement a format adapter before promoting EnforceCore backends to primary. Currently, EC backends (SQLite, PostgreSQL) are used for queryable storage only — AKIOS's own JSONL + Merkle verification stays authoritative.

- **Merkle format bridge** — adapter that converts AKIOS events to EnforceCore hash format when writing to EC backends. Both systems keep their own format for verification.
- **Pluggable audit backends** — SQLite, PostgreSQL promoted to production-ready (with bridge)
- **Audit data migration** — `akios audit migrate` command for JSONL → SQLite/PG
- **Resource guards** — layer EnforceCore's `CostTracker` + `KillSwitch` under kernel sandbox
- **HIPAA/SOX query templates** — compliance queries for healthcare and financial audit
- **EnforceCore version tracking** — release process updated to verify bridge compatibility on EC version changes

---

## v1.4.0 — "Observability" (Target: Q4 2026)

**Theme:** Production monitoring and observability.

- **OpenTelemetry** — tracing + Prometheus metrics (via EnforceCore telemetry)
- **Streaming LLM output** — per-token PII filtering
- **Audit retention policies** — auto-archive, auto-delete based on age

---

## v1.5.0 — "Scale" (Target: Q1 2027)

**Theme:** High-throughput and multi-tenant capabilities.

- **Fan-out / map-reduce** — execution patterns for batch workflows
- **Multi-tenant isolation** — per-tenant budgets, audit trails, PII policies
- **Community template marketplace** — share and discover workflow templates

---

## v2.0.0 — "Platform" (Future, only if breaking changes needed)

**Theme:** Major version only if backward-incompatible changes required. Non-binding.

Most features will ship as v1.x minor releases. v2.0.0 is reserved for genuine breaking changes that cannot be done backward-compatibly (e.g., workflow schema v2, Python 3.11+ minimum, deprecated CLI removal).

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

