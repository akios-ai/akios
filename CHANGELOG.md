# Changelog
**Document Version:** 1.0.8  
**Date:** 2026-02-19  

All notable changes to AKIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.8] - 2026-02-19

### Added — PII Detection
- **🔌 Pluggable PII backend** — New `PIIDetectorProtocol` (runtime-checkable Protocol) enables swappable detection engines. Factory function `create_pii_detector(backend=)` reads `pii_backend` from settings. Regex is default; Presidio reserved for future `akios-pro`.
- **🏥 Insurance PII patterns** — 4 new patterns: `insurance_policy`, `insurance_group`, `insurance_claim`, `prior_authorization` with context keywords for disambiguation.
- **🎯 context_keywords gate** — PII detection now checks ±100 characters around a match for contextual keywords. Patterns that lack nearby context are suppressed, significantly reducing false positives (e.g., bare 9-digit numbers no longer match as routing numbers).
- **📊 PII accuracy test corpus** — Annotated test suite (`tests/unit/test_pii_accuracy.py`) with per-pattern precision/recall/F1 scoring. Patterns scoring below 0.80 F1 fail CI.

### Added — Workflow Engine
- **🔀 Conditional execution** — New `condition` field on workflow steps. Expressions are evaluated against prior step outputs in a restricted namespace. Steps are skipped when condition evaluates to false.
- **🛡️ Error recovery** — New `on_error` field on workflow steps: `skip` (continue workflow), `fail` (halt, default), `retry` (re-attempt once with same parameters).
- **📐 Workflow schema v1.1** — `workflow_schema.json` updated to include `condition` and `on_error` properties.

### Added — Documentation & Specifications
- **🔗 LangGraph integration example** — Working example at `docs/integration/langgraph_integration.py` showing AKIOS agents as LangGraph tool-calling nodes with full security cage enforcement.
- **📜 TLA+ formal specification** — Model-checked safety invariants for the enforcement pipeline (`docs/tla/AKIOSEnforcement.tla`). Verifies: PII always redacted before output, cost kill-switch fires on overspend, audit completeness, sandbox required for execution.
- **📖 CLI testing subcommands documented** — `akios testing show-notes`, `clear-notes`, `log-issue` now documented in CLI reference.
- **⚙️ Config JSON Schema** — `Settings.json_schema()` method generates JSON Schema from Pydantic model for IDE auto-completion.

### Changed
- **⚖️ Weighted compliance scoring** — Overall compliance score now uses security-weighted formula (security 50%, audit 30%, cost 20%) instead of equal-weight average. Reflects security-first product philosophy.
- **🎯 Action name unification** — Canonical actions synced with AGENTS.md: `llm={complete,chat}`, `http={get,post,put,delete}`, `filesystem={read,write,list,exists,stat}`, `tool_executor={run}`. Old names (`generate`, `execute`, `call`, `patch`, `analyze`) accepted as backward-compatible aliases.
- **🔧 ALLOWED_MODELS to config** — Hardcoded model set moved from `engine.py` to `Settings.allowed_models` in `settings.py`. Models are now configurable via `config.yaml` or `AKIOS_ALLOWED_MODELS` env var.
- **🔍 Unified output key-probing** — Single `_extract_output_value()` method with canonical key order (`text → content → output → result → response → stdout → data`) used consistently by `{previous_output}`, `{step_X_output}`, and `_extract_step_output()`.
- **📝 Engine logging** — Added `logging.getLogger(__name__)` to engine.py. Key execution events now emit structured log records alongside user-facing print statements.
- **🏗️ Engine organisation** — Class docstring documents internal method groupings. `_emit_audit()` helper centralises the repeated audit-event emission pattern (was 7+ duplicated sites).

### Fixed
- **🐛 Probe file race condition** — `_validate_output_directory_state()` now uses `tempfile.mkstemp()` instead of a fixed `.akios_execution_test` file, eliminating race conditions under concurrent runs.
- **🐛 gc.collect() removed** — Unnecessary `gc.collect()` in `_isolate_execution_environment()` added ~50ms latency per reset with no measurable benefit. Removed.
- **🐛 _handle_workflow_failure indentation** — Fixed indentation bug in metadata dict that caused incorrect YAML/dict nesting.
- **🐛 Hardcoded version in output.json** — `akios_version` in workflow output now reads dynamically from `akios._version.__version__` instead of hardcoded `'1.0.7'`.
- **🐛 PII core.py deduplication** — `PIIRedactor.redact_text()` in `core.py` now delegates to canonical redactor instead of maintaining 3 inline fallback regexes.
- **🐛 output_filter.py consolidation** — `OutputFilter` now uses canonical `PIIRedactor` from `redactor.py` instead of maintaining independent regex patterns.

### Infrastructure
- **🌐 DNS check dedup** — Extracted `check_network_available()` to `akios.core.utils.network`. Previously duplicated in `engine.py`, `tracker.py`, and `cli/commands/run.py`.
- **📋 ROADMAP updated** — v1.0.7 marked as "Shipped", v1.0.8 "Science + Orchestration" with 15 items listed.

## [1.0.7] - 2026-02-12

### Added
- **📊 `akios audit stats`** — Show audit ledger statistics: event count, ledger size, archive segments, Merkle root hash, rotation threshold. Supports `--json` output.
- **🔄 `akios audit rotate`** — Manually trigger audit log rotation with Merkle chain linkage. Archives current ledger and starts fresh. Supports `--json` output.
- **✅ `akios workflow validate <file.yml>`** — Validate workflow YAML against the AKIOS schema: YAML syntax, required fields, agent/action existence, step schema, file path existence warnings. Supports `--json` output. (WI-6)
- **🧪 Ablation study support** — `akios cage up --no-pii --no-audit --no-budget` flags for controlled benchmarking. Engine respects these flags: audit event emission and cost kill-switch enforcement are conditional on settings. (WI-5)
- **🔑 `context_keywords` field on PIIPattern** — Ambiguous patterns (france_id, germany_id, bank_account_us, routing_number) now carry context keywords for disambiguation. (WI-4)

### Changed
- **🏦 Routing number pattern** — Now requires context keyword prefix (routing, aba, transit) instead of matching any bare 9-digit number. Reduces false positives significantly. (WI-4)
- **🗑️ `cage down --passes N`** — Configure number of secure overwrite passes for data erasure (default: 1). More passes increase security; SSD caveat documented. (WI-3)
- **⚡ `cage down --fast`** — Skip secure overwrite for speed; files deleted without shredding. Warning displayed when used. (WI-3)
- **🔐 Audit log integrity** — No silent event drops; O(1) event counter; automatic log rotation at 50K events with Merkle chain linkage between segments. (WI-2)
- **📈 Real compliance scoring** — Compliance report uses weighted scoring (PII 30%, Audit 25%, Security 25%, Config 20%) instead of binary pass/fail. (WI-1)

### Security
- **Engine ablation guards** — `audit_enabled=False` suppresses all audit event emission in the runtime engine. `cost_kill_enabled=False` disables budget enforcement. Prevents ablation benchmarks from generating noise. (WI-5)
- **Secure data erasure** — `_secure_overwrite_file()` performs random bytes → fsync → zeros → fsync → unlink per pass. SSD wear-leveling caveat documented. (WI-3)

### Fixed
- **Dead dependency removed** — Removed unused `click` from pyproject.toml and requirements.txt. (WI-7)
- **Repository hygiene** — 18 duplicate/stale files removed, .gitignore updated. (WI-8)

## [1.0.6] - 2026-02-12

### Security
- **🔐 Merkle Proof System — Complete Rewrite**
  - `get_proof()` now generates proper O(log n) sibling-hash proof paths
  - `verify_proof()` performs real SHA-256 cryptographic root recomputation
  - `akios audit verify` compares recomputed root against stored Merkle root hash
  - Ledger persists Merkle root to `merkle_root.hash` sidecar file on every flush
  - Proof format: `{"position": "left"|"right", "hash": "<hex>"}` dictionaries
- **🛡️ PII Fail-Safe Hardening**
  - All 4 agents (filesystem, HTTP, LLM, tool executor): PII import failure now blocks data with `[PII_REDACTION_UNAVAILABLE]` instead of silently passing raw content through
  - Filesystem agent PII timeout: returns `[CONTENT_REDACTED_TIMEOUT]` instead of raw content
  - CRITICAL log warning emitted when PII module fails to load
- **🌐 HTTPS Enforcement**
  - HTTP agent now blocks plain `http://` URLs when `sandbox_enabled=True`
  - Only HTTPS permitted in sandboxed mode (LLM APIs always allowed)

### Fixed
- **🏥 ICD-10 False Positives Eliminated**
  - License plate pattern changed from `[A-Z]{1,3}` to `[A-Z]{2,3}` — medical codes like `E11.9` no longer misclassified as license plates
  - Synced `pattern` and `compiled_pattern` fields in license plate rule (previously mismatched — compiled was missing negative lookaheads)
- **📋 Audit Verifier Tests**
  - Fixed mock paths for `get_settings` (was using wrong module path due to lazy import pattern)
  - Fixed ledger duplicate event loading (events no longer doubled from disk reload)
  - All 14 audit verifier tests now pass (previously 11 failures)

### Added
- **🔍 53 PII Patterns (was 43)**
  - 10 new digital identity patterns: ITIN, Medicare MBI, VIN, IPv6 address, AWS access key, generic API key, JWT token, private key header, GitHub token, password-in-URL
  - Total: 53 patterns across 6 categories (personal: 20, health: 13, financial: 8, digital: 6, communication: 3, location: 3)
- **🏥 US Health Insurance Coverage Broadened**
  - Pattern widened from `[A-Z]{2}\d{9}` to `[A-Z]{2,3}\d{6,12}` for broader carrier format support

### Tests
- Merkle tree: 36/36 tests pass (new proof format, multi-leaf, tamper detection)
- Audit verifier: 14/14 tests pass (was 3/14 — fixed mock paths and duplicate loading)
- Full unit suite: 775+ tests pass, 0 regressions from v1.0.6 changes

## [1.0.5] - 2026-02-07

### Added
- **🔒 Cage Down Data Wipe**
  - `cage down` now destroys all session data by default (audit logs, outputs, inputs)
  - Core security promise: "nothing is left" when cage goes down
  - `--keep-data` flag for development convenience (relax without wiping)
  - Detailed wipe summary showing files/bytes destroyed per category
- **📦 Deployable JSON Output (`output.json`)**
  - Every workflow run generates structured `output.json` with full metadata
  - Per-step results: agent, action, status, timing, output text
  - Security posture, cost breakdown, budget tracking included
  - `akios output latest` retrieves deployable JSON for CI/CD integration
- **🎨 PII Visibility Improvements**
  - PII markers now use magenta `«PII_TYPE»` guillemet format for instant identification
  - 6+ PII types detected and highlighted: EMAIL, PHONE, SSN, NAME, ADDRESS, DOB
  - Healthcare-specific classifiers: US_NPI, US_DEA, MEDICAL_RECORD_NUMBER
  - Improved scan output readability (removed dim styling)
- **🌐 HTTP Agent CLI (`akios http`)**
  - `akios http <METHOD> <URL>` for secure API calls with domain whitelisting
  - Supports GET, POST, PUT, DELETE with headers, body, and JSON payloads
  - Rate limiting (10 req/min), HTTPS enforcement, PII redaction on all data
- **🔍 Prompt Inspection (`akios protect show-prompt`)**
  - Preview exactly what the LLM will receive after PII redaction
  - Color-split legend: original text vs. redacted markers
  - Critical for HIPAA/GDPR compliance verification before execution
- **🛡️ `--exec` Security Trap**
  - `akios run --exec` is a honeypot that blocks shell-injection attempts
  - Returns "Direct shell execution is not permitted inside the security cage"
  - Logged as a security event in audit trail
- **🏭 Multi-Sector Support (6 Industries)**
  - Healthcare, banking, insurance, accounting, legal, government
  - Dedicated demo scripts (EN + FR) with sector-specific PII patterns
  - Headless test scripts (`demo-test.sh` + `demo-test-fr.sh`) for CI/CD
  - Edge case test suite (`edge-tests.sh`) for release verification
- **🔇 Suppressed `google.generativeai` FutureWarning**
  - No more noisy warnings on every command when Gemini SDK is installed
- **🎨 ASCII Logo on First Run**
  - Professional AKIOS logo displays once on first run (like Anthropic Claude CLI)
  - Rich-styled panel with cyan brand colors (#04B1DC)
  - First-run detection via `~/.akios/.initialized` marker
  - TTY detection (never shows in piped/scripted contexts)
  - CI/CD detection (suppresses in GitHub Actions, GitLab CI, etc.)
  - Graceful fallback to plain ANSI colors if Rich unavailable
  - Zero performance overhead on repeat runs (<1ms file check)
  - Works identically in native and Docker environments
- **🎨 Professional Terminal UI with Rich Integration**
  - Rich 13.7.0 dependency for beautiful CLI output
  - `rich_output` module with styled panels, colored tables, and message formatting
  - `pii_display` module for professional PII detection visualization
  - Colored severity indicators (🟢 🟡 🔴 ⛔) for quick status recognition
  - Professional data tables for structured CLI output
  - Styled success/warning/error/info messages
  - Code syntax highlighting with line numbers
  - Progress indicators for long-running operations
- **🔍 Enhanced PII Detection Visualization**
  - Summary display with file status
  - Detailed candidate tables with line numbers and confidence scores
  - Type breakdown with percentage distributions
  - Comprehensive scan reports with severity levels
  - CSV export functionality for compliance reporting
  - Remediation guidance with specific recommendations
- **CLI Command Enhancements**
  - `akios status`: Security & budget dashboards with Rich panels and tables
  - `akios files`: Professional file listing with formatted tables
  - `akios testing`: Issue tracking display using Rich formatting
  - Graceful fallback to plain text if Rich is unavailable
- **✅ Comprehensive Testing**
  - 14 unit tests for rich_output module (100% passing)
  - 17 unit tests for pii_display module (100% passing)
  - Integration tests for combined UI functions
  - CSV export and remediation guidance tests
- **📚 Complete Documentation**
  - New `docs/rich-ui.md` comprehensive guide
  - Updated README with Rich UI feature mention
  - Module reference for all functions
  - Styling examples and best practices
  - Terminal compatibility information

### Changed
- Refactored CLI commands to use Rich output for professional appearance
- Security dashboard now displays as formatted tables with color coding
- Budget dashboard shows breakdown in professional table format
- Testing notes display in Rich tables instead of plain text
- All styled output respects terminal capabilities (automatic fallback)
- **🐳 Docker wrapper gated behind container check**: `akios init` no longer creates a Docker wrapper script on native Linux/macOS installs — wrapper only created inside Docker containers where it's needed
- **🔧 Unified command prefix**: `get_command_prefix()` centralized in `core/ui/commands.py` with env var + dockerenv checks, replacing scattered hardcoded `sudo akios` strings
- **📋 Template defaults**: `document_ingestion.yml` now defaults to `grok`/`grok-3`; `healthcare-patient-intake.yml` updated from deprecated `gpt-4` to `gpt-4o-mini`
- **🏷️ Logo tagline**: Updated to v1.0.5

### Fixed
- **🔒 Seccomp SIGTRAP crash**: `sudo akios run` no longer crashes with signal 5 — expanded syscall allowlist by ~40 essential syscalls and switched policy filter from allowlist to blocklist approach
- **🐳 Container detection false-positive on EC2**: Native EC2 instances no longer misidentified as Docker containers — tightened `/proc/1/cgroup` matching to path-based patterns and removed unreliable hostname/cgroup-write heuristics
- **📁 Root cache directory creation**: `_save_security_cache()` now creates `/root/.akios/` directory automatically when running with sudo
- **🔧 ctypes seccomp fallback**: `_alloc_buffer()` now raises `RuntimeError` with guidance instead of silently returning NULL pointer
- **📧 Security contact email**: Standardized to `security@akioud.ai` across all documentation (was inconsistent between docs)
- **📖 Documentation accuracy**: Removed overstated "100% accuracy" and "Non-Bypassable" claims from security README; qualified with actual behavior
- **🧪 Test suite hardened**: Added 6 new kernel-hard security tests (Phase 5b) covering sudo execution, seccomp audit logs, and security mode differentiation (28→34 tests)
- **🌐 Seccomp DNS resolution**: Added `sendmmsg` and `recvmmsg` to essential syscall allowlist — fixes DNS resolution failure when calling real LLM APIs (Grok, OpenAI, etc.) with sandbox enabled on Ubuntu 24.04 ARM64 (glibc uses these for DNS)
- **🎨 Rich markup stripping in plain-text fallback**: All CLI output functions (`print_success`, `print_error`, `print_warning`, `print_info`, `print_panel`, `print_banner`, `output_with_mode`) now strip Rich markup tags (`[bold]`, `[dim]`, `[#04B1DC]`, etc.) when Rich is unavailable, preventing raw markup from appearing in terminal output
- **🤖 LLM SDK validation expanded**: `validate_llm_sdk()` now checks all 5 supported providers (openai, anthropic, xai/grok, mistralai, google-generativeai) and automatically bypasses validation when `AKIOS_MOCK_LLM=1` is set
- **📌 Version import in status command**: `akios status` now correctly imports `__version__` from `akios._version` instead of using stale hardcoded version string
- **♻️ Removed duplicate GPU/platform block**: `run.py` had a duplicated 30-line GPU detection block that ran twice per execution
- **🛡️ Guarded psutil import**: `run.py` now gracefully handles missing `psutil` with `try/except ImportError` fallback
- **🗑️ Removed dead code**: Deleted unused `run_security_dashboard()` function from `status.py`
- **🔑 Grok model duplicate key fix**: `first_run.py` model config had duplicate `"model"` key for Grok provider — consolidated to single entry
- **💥 Rich crash fallback**: `first_run.py` now catches `Exception` when importing Rich and falls back to plain-text output instead of crashing
- **🧪 Test updates**: Updated 4 test assertions for v1.0.5 version bump (status, helpers, init); launcher script test now correctly expects no wrapper on native installs
- **📢 Diagnostic banners to stderr**: Security mode banners (`🔒 Security Mode: ...`) now print to stderr instead of stdout, fixing `--json` flag contamination across all CLI commands
- **⏱️ LLM timeout consistency**: All 5 providers (OpenAI, Anthropic, Grok, Mistral, Gemini) now use 120-second timeout; previously Gemini had no timeout set

### EC2 Deployment Scripts
- Fixed shebang line in `01a-create-instance.sh` (`#!/usr/bin/env bash`)
- Fixed metadata file paths in `08-test-ssh.sh` and `09-setup-server.sh` to use correct directory structure
- Fixed API key provisioning in EC2 setup scripts
- Updated EC2 README with correct paths and instructions
- Added EC2 `.gitignore` with updated paths

## [1.0.4] - 2026-01-29

### Changed
- Enhanced release process with v3.1 safety gates
- Updated documentation with clearer version references

## [1.0.0] - 2026-01-24

### Added
- **🚀 Multi-Deployment Options**
  - **Pip Package**: Maximum security with kernel-hard features on Linux
  - **Docker Container**: Cross-platform consistency with policy-based security
- **🔒 Enhanced Security Architecture**: Defense-in-depth across all platforms
  - **Native Linux**: seccomp-bpf + cgroups v2 kernel-hard isolation
  - **Docker**: Policy-based container security (allowlisting, PII redaction, audit)
  - **Unified PII Protection**: 50+ pattern detection, real-time redaction
  - **Cryptographic Audit Trails**: Merkle tree verification, tamper-evident logs
- **📊 Production-Ready Features**: Complete AI workflow security
  - Real AI provider integration (OpenAI, Anthropic, Grok, Mistral, Gemini)
  - Cost kill-switches ($1.00 default budget limits)
  - Resource controls (CPU, memory, file size limits)
  - Comprehensive error handling and recovery
- **🎯 User Experience**
  - **Terminal Width Awareness**: Templates list adapts to screen width
  - **File Discovery Commands**: `akios files` shows available input/output files
  - **Enhanced Template Guidance**: Clear file availability and usage tips
  - **Improved Progress Feedback**: Better status indicators and next steps
  - **Setup Wizard** with mock-first approach, skip option, dynamic pricing examples, real-time API key validation, and forgiving UX
  - **Comprehensive Help System**: Complete command documentation
- **📚 Complete Documentation Suite**: User experience focused
  - Installation decision tree and platform guidance
  - Migration guide for existing deployments
  - Troubleshooting for all deployment methods
  - Configuration reference with security explanations
- **🔧 Release Infrastructure**: Enterprise-grade deployment pipeline
  - Automated multi-platform binary builds
  - Cryptographic integrity verification
  - Professional release notes and asset management
  - Version synchronization across all components

### Changed
- **Installation Experience**: From single Docker method to pip + Docker dual deployment
- **Security Communication**: Clear platform capability explanations
- **Documentation Structure**: Comprehensive user guides and troubleshooting
- **Release Process**: Automated pipeline with quality assurance

### Security
- **Kernel-level sandboxing** with platform-appropriate isolation
- **Automatic PII redaction** across all deployment methods
- **Cryptographic audit trails** with integrity verification
- **Cost and resource controls** preventing abuse
- **Tamper-evident logging** for regulatory compliance

### Technical
- **Platform-specific optimizations** for performance and security
- **Unified configuration** across all deployment methods
- **Automated testing** and quality assurance pipelines

## [Unreleased]

Future open-source releases (V1.x / V2.0) will focus on gradual usability improvements while preserving the security & governance-first cage.

Planned directions (non-binding, community-driven):
- Parallel, conditional, loop, and fan-out execution patterns
- Additional core agents (DB connectors, Email, Slack…)
- Full CLI suite and basic REST API
- Enhanced state persistence and crash recovery
- More high-quality example templates
- Basic observability (Prometheus/Jaeger integration)

**Legal/certified features** (FranceConnect, eIDAS, hard HDS blocks, official PDFs) remain exclusive to AKIOS PRO.

## Types of Changes

- `Added` — new features
- `Changed` — changes in existing functionality
- `Deprecated` — soon-to-be removed
- `Removed` — now removed features
- `Fixed` — bug fixes
- `Security` — vulnerability fixes

## Version Numbering

- **MAJOR** — incompatible API changes
- **MINOR** — backwards-compatible additions
- **PATCH** — backwards-compatible bug fixes

## Release Process

1. Development → Stabilization → Testing → Release
2. All changes must respect minimal cage philosophy
3. Security fixes prioritized

## Support & Community

- GitHub Discussions & Issues
- Security reports: security@akioud.ai (private only)
- See README.md for current scope & limits

*For the complete history, see the [Git repository](https://github.com/akios-ai/akios/commits/main).*

This changelog is **locked** for V1.0.  
Future entries will reflect only scope-aligned changes.
