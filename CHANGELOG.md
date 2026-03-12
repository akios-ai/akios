# Changelog
**Document Version:** 1.4.2
**Date:** 2026-03-12

All notable changes to AKIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.2] - 2026-03-12

### Added

- **Ollama provider** — Full runtime implementation for locally-hosted open-source models (Llama, Mistral, Gemma, Phi, etc.) via the Ollama REST API. No API key required. Default model: `llama3.2`. Configurable via `OLLAMA_HOST` / `OLLAMA_BASE_URL` environment variables.
- Commercial offerings breadcrumb in README for organizations needing extended PII coverage

### Fixed

- Corrected class names in API reference (`HttpAgent` → `HTTPAgent`, `LlmAgent` → `LLMAgent`)
- Fixed default model in API reference (`gpt-3.5-turbo` → `gpt-4o-mini`)
- Removed false "Industry Templates" claim from README
- Fixed CLI command count across all docs (was "18", actual is 21)
- Fixed `cage down` documentation to correctly state that `data/input/` is preserved (not destroyed)
- Updated stale version strings (`1.0.16` → `1.4.1`) in CLI reference
- Added missing agents (webhook, database) to workflow schema error examples
- Added missing filesystem actions (list, exists) to workflow schema
- Fixed stale dates across documentation files
- Removed obsolete model names from CLI reference (gpt-3.5-turbo, gpt-4)
- Fixed garbled emoji characters in README headings

## [1.4.1] - 2026-03-11

### Fixed — Hotfix

- Removed internal product-name references from all public-facing files (P10 gate compliance)
- Restored `_load_health_patterns` / `_load_location_patterns` function definitions in PII rules module
- Corrected CHANGELOG migration language to use neutral phrasing

## [1.4.0] - 2026-03-11

### Changed — PII Boundary Refinement

#### ⚠️ BREAKING: Healthcare & Financial PII Patterns Removed from OSS

The following specialized PII patterns have been **removed from AKIOS OSS** to focus
the open-source engine on general-purpose detection:

**Healthcare patterns removed (8):**
- `us_npi` — US National Provider Identifier
- `us_dea` — US Drug Enforcement Administration number
- `medical_record_number` — MRN-format medical record numbers
- `insurance_policy` — HMO/PPO/BCBS policy numbers
- `insurance_group` — Insurance group/employer IDs
- `insurance_claim` — Insurance claim references
- `prior_authorization` — Prior authorization numbers
- `medicare_mbi` — Medicare Beneficiary Identifier

**Financial patterns removed (5):**
- `iban` — International Bank Account Numbers
- `bic` — BIC/SWIFT codes
- `routing_number` — US bank routing numbers (ABA)
- `wire_transfer` — Wire transfer references
- `crypto_wallet` — Cryptocurrency wallet addresses (BTC/ETH)

**What stays in OSS (44 patterns across 6 categories):**
- **Personal (20):** email, phone (FR/US/UK/DE), SSN, French SSN, passport EU,
  driver's license, birth date, full name, France/Germany ID, UK NI, tax ID, ITIN,
  license plate, company name, VIN, bank account
- **Health (9):** French health insurance, US health insurance (generic), medical record
  (generic), medication dosage, blood pressure, lab results, diagnosis codes, vital signs,
  emergency contact
- **Financial (3):** credit card, Amex, PayPal email
- **Communication (3):** IPv4, IPv6, MAC address
- **Digital (6):** AWS keys, API keys, JWT, private key headers, GitHub tokens, passwords in URLs
- **Location (3):** postal address, French address, GPS coordinates

#### Migration Guide
If your workflows depend on NPI, DEA, MRN, IBAN, BIC, routing number, wire transfer, or
crypto wallet detection, reach out if you need continued coverage for these patterns. All other patterns
continue to work identically.

### Updated
- Documentation updated across 12 files to reflect new pattern count (44)
- Release checklist and process updated for v1.4.0
- Test suite updated: removed `test_pii_mrn.py`, updated accuracy corpus and dedup tests
- PII bridge module updated for new pattern count

## [1.3.0] - 2026-02-27

### Added — "Unified Audit" (Merkle Bridge + Production Backends)

#### Merkle Bridge (EnforceCore v1.12.0)
- **AKIOS audit events now include pre-computed Merkle hashes** when writing to EnforceCore backends.
  EC stores AKIOS's hash via `external_hash` mode — no re-hashing, no format mismatch.
- EnforceCore v1.12.0 `verify_trail(skip_entry_hash=True)` verifies chain linkage without
  recomputing entry hashes — format-agnostic verification now possible.
- SQLite backend stores `akios_merkle_hash` in event metadata for cross-reference.
- EnforceCore dependency updated: `>=1.12.0` (was `>=1.11.1`).

#### Audit Backend Improvements
- Secondary backends (SQLite, PostgreSQL) now receive AKIOS Merkle hashes alongside events.
- Dual-write enrichment: ledger passes both event data and computed hash to extra backends.

### Infrastructure
- 1,554 tests passing WITH enforcecore v1.12.0
- 1,553 tests passing WITHOUT enforcecore (cardinal rule maintained)
- Merkle cross-verification test updated for v1.12.0 bridge API

## [1.2.3] - 2026-02-27

### Verified — Real EnforceCore v1.11.1 Integration Testing

All AKIOS bridge modules verified against real `enforcecore==1.11.1` (2,324 tests, 97% coverage).

#### Bridges Verified Working
- **SecretScanner** — `SecretScanner().detect()` returns correct `DetectedSecret` objects
- **RuleEngine** — `RuleEngine.with_builtins().check()` returns correct `RuleViolation` objects
- **HookRegistry** — `HookRegistry.global_registry()` accessible, add_pre_call/add_post_call work
- **PatternRegistry** — `PatternRegistry.register()` accepts AKIOS patterns correctly

#### CRITICAL FINDING: Merkle Chain Formats Incompatible
- AKIOS uses binary Merkle tree (SHA-256 of event JSON)
- EnforceCore uses linear chain (SHA-256 of entry payload, different field ordering)
- `verify_trail()` reports hash mismatch on ALL entries
- **Decision:** EnforceCore audit backends (SQLite, PostgreSQL) used for QUERYABLE STORAGE ONLY.
  AKIOS's own JSONL + Merkle verification stays authoritative. Backend swap deferred until
  Merkle format bridge implemented (v1.3.0+).

#### Fixed
- **fix: compliance.py eu-ai-act import path** — `from ....config` (4 dots, wrong depth) → `from akios.config`
- **fix: enforcecore dependency version** — `>=1.2.0` → `>=1.11.1` (matches actual target)
- **fix: Merkle cross-verification test** — now documents incompatibility as expected behavior

### Infrastructure
- 1,554 tests passing WITH enforcecore==1.11.1 installed
- 1,553 tests passing WITHOUT enforcecore (cardinal rule maintained)

## [1.2.2] - 2026-02-26

### Added — "Foundation RC" (EnforceCore Integration — Phase 3)

#### EU AI Act Reports (`akios compliance eu-ai-act`, requires EnforceCore)
- Generate Article 9/13/14/52 compliance reports from AKIOS audit trail
- HTML + JSON formats via EnforceCore's `ReportGenerator`

#### PostgreSQL Audit Backend (`AKIOS_AUDIT_BACKEND=postgresql`)
- Events written to PostgreSQL alongside primary JSONL (never replaces it)
- Configure via `AKIOS_AUDIT_PG_DSN=postgresql://...`

#### Lifecycle Hooks (requires EnforceCore + `use_enforcecore=True`)
- `pre_workflow`, `post_workflow` hooks at workflow lifecycle points
- New module: `src/akios/security/hooks.py`

#### Unicode PII Normalization (requires EnforceCore + `use_enforcecore=True`)
- Accent-folded evasion detection via `normalize_text()`

#### Merkle Cross-Verification Test (critical gate for v1.3.0)
- Test verifies AKIOS audit JSONL is readable by EnforceCore verifier
- MUST PASS before migrating audit backends in v1.3.0

#### Release Process Improvement
- `post_release_gate.sh` PyPI checks now retry 3× with 30s backoff

### Infrastructure
- 1,553 unit tests passing (+11 new RC tests).

## [1.2.1] - 2026-02-26

### Added — "Foundation Beta" (EnforceCore Integration — Phase 2)

#### PII Bridge (requires EnforceCore + `AKIOS_USE_ENFORCECORE=true`)
- **Dual-engine PII detection** — AKIOS's 50+ patterns + EnforceCore's `SecretScanner` run together. AKIOS is authoritative; EC adds 11-category secret detection on top.
- **Pattern registration** — AKIOS healthcare/financial/EU patterns registered into EnforceCore's `PatternRegistry`.
- New module: `src/akios/security/pii/bridge.py`

#### SQLite Audit Backend (optional, alongside JSONL)
- **`AKIOS_AUDIT_BACKEND=sqlite`** — audit events written to SQLite **in addition to** primary JSONL. Merkle chain never replaced.
- New setting: `audit_backend` (default: `jsonl`)
- New modules: `src/akios/core/audit/backends/`

#### Release Process Improvements
- `pre_release_gate.sh` auto-uninstalls stale akios from EC2 before deploying.
- EC2 setup fallback version corrected (was stuck at 1.0.11).

### Infrastructure
- 1,542 unit tests passing (+13 new tests).

## [1.2.0] - 2026-02-26

### Added — "Foundation" (EnforceCore Integration — Phase 1)

This is the first release in the v1.2.0 "Foundation" series, which integrates
[EnforceCore](https://github.com/akios-ai/EnforceCore) (Apache-2.0) as an optional
dependency. **AKIOS works fully without EnforceCore.** Install with:
`pip install 'akios[enforcecore]'`

#### Secret Detection (new — requires EnforceCore)
- **`akios protect secrets <file>`** — Scan files and text for 11 categories of leaked
  credentials: AWS keys, GitHub tokens, PEM private keys, database connection strings,
  bearer tokens, GCP service accounts, Azure connection strings, SSH private keys, and more.
- New module: `src/akios/security/secrets.py` — bridges to EnforceCore `SecretScanner`.
- Gracefully returns empty result when EnforceCore not installed.

#### Content Rule Enforcement (new — requires EnforceCore)
- Shell injection, SQL injection, path traversal, and code execution detection in
  `tool_executor` and `database` agent configs via EnforceCore `RuleEngine`.
- Only active when `AKIOS_USE_ENFORCECORE=true` is set.
- New module: `src/akios/security/content_rules.py` — bridges to EnforceCore `RuleEngine`.

#### Doctor Diagnostics
- **`akios doctor`** now includes an EnforceCore availability check (10th check).
  Shows install instructions when not present.

#### Optional Dependency
- New `pip install akios[enforcecore]` extra for `enforcecore>=1.2.0`.
- New settings: `use_enforcecore` (default: False), `enforcecore_content_rules`,
  `enforcecore_secret_scan`.

### Infrastructure
- 1,529 unit tests passing (+15 new EnforceCore integration tests).
- All tests verified to pass WITH and WITHOUT EnforceCore installed.

## [1.1.2] - 2026-02-25

### Fixed — Bedrock Reliability & Token Reporting

- **fix: Token reporting returns 0 for Bedrock runs** — Step executor now checks nested `usage` dict and `tokens_used` as fallbacks when top-level `prompt_tokens`/`completion_tokens` keys are missing. Tokens flow correctly: Bedrock provider → LLM agent → step executor → cost tracker → JSON output.
- **fix: ~50% intermittent failures with Bedrock** — Added handling for AWS credential exceptions (NoCredentialsError, PartialCredentialsError, TokenRetrievalError) and connection errors (EndpointConnectionError) with clear error messages and retry. Previously these hit the generic `except Exception` and produced silent exit code 1.
- **fix: JSON error output on broken pipe** — `_emit_json_error()` now catches BrokenPipeError and falls back to stderr. Docker consumers always get structured error output even when stdout pipe closes.
- **fix: Wrong json_mode parameter in error handlers** — Exception handlers in `run.py` now correctly pass `json_mode=True` when `--json-output` is active (was hardcoded `False`).

## [1.1.1] - 2026-02-25

### Fixed — Bedrock Provider Hardening

- **fix: Add Bedrock to PROVIDER_MODELS validation** — Workflows using `provider: bedrock` no longer crash with "Unknown LLM provider" during config validation. All 10 Bedrock model IDs (Claude 3.5, Llama 3.1, Titan) now validated.
- **fix: Include boto3 in official Docker image** — `boto3>=1.34.0` now installed by default in the Docker image. SDK consumers no longer need a custom Dockerfile to use AWS Bedrock.

## [1.1.0] - 2026-02-25

### Added — v1.1.0 "Scale" (First proper semver minor release)

#### Webhook Agent (new)
- **New agent type: `webhook`** — Send notifications to Slack, Discord, Microsoft Teams, or generic HTTP POST endpoints.
- Actions: `notify`, `send`
- Platform-specific payload builders (Slack blocks, Teams cards, Discord messages)
- Security: PII redaction on messages, HTTPS enforcement, rate limiting (10/min)
- Mock mode support for testing

#### Database Agent (new)
- **New agent type: `database`** — Query PostgreSQL and SQLite with security enforcement.
- Actions: `query`, `execute`, `count`
- Security: parameterized queries only (no raw SQL), DDL always blocked, read-only by default
- PII redaction on query results, audit logging of all queries
- Configurable max rows (10,000) and timeout (60s)

#### Parallel Step Execution
- **`parallel:` blocks** in workflow YAML for concurrent step execution.
- ThreadPoolExecutor with max 4 workers
- Thread-safe execution context and cost tracking
- Kill switches evaluated between parallel groups
- No nested parallel blocks (v1.1.0 limitation)

#### Plugin System
- **pip-installable agent packages** via `akios.agents` entry points.
- Auto-discovery at import time via `importlib.metadata.entry_points()`
- Type-checked: only BaseAgent subclasses registered
- Schema relaxed to accept plugin agent types

#### Doctor Command Redesign (BUG-06 from v1.0.16)
- **`akios doctor` rewritten** as proper diagnostic tool (no longer duplicates `status --security`)
- 9 diagnostic checks: Python version, dependencies, config, API keys, sandbox, disk space, PII engine, audit system
- Each check shows PASS/WARN/FAIL with actionable fix suggestions
- JSON output via `--json` flag
- Exempt from platform security check (runs on all platforms)

### Changed
- Agent registry expanded from 4 to 6 core agents
- Workflow schema v1.2.0: supports parallel blocks, webhook/database agents, plugin agents
- Loop constructs still blocked; parallel blocks now use native `parallel:` syntax
- `bump-version.sh` now covers all 12 root docs (was 5) + auto-verifies with `verify-version-sync.sh`

### Infrastructure
- Release planning docs: `internal/docs/dev/releases/v1.1.0-PLAN.md`, `v1.2.0-PLAN.md`
- Release process hardening: post_release_gate.sh path + Docker fixes, wrapper.sh vlatest fix

## [1.0.16] - 2026-02-23

### Fixed — Beta Tester Bug Reports (10 Bugs Fixed + 1 Deferred)

Addresses 11 confirmed bugs from external beta tester audit. 4 additional reports were investigated and rejected with evidence (see `internal/docs/BETA_TESTER_RESPONSE_v1.0.16.md`).

#### REST API Fixes

- **🔧 BUG-01 (P0): `/api/v1/audit/verify` endpoint crashes** — Fixed `AttributeError` in audit verify endpoint. Changed `ledger.verify_chain()` → `ledger.verify_integrity()` and `ledger.event_count` → `ledger.size()` to match actual `AuditLedger` API.
- **🔧 BUG-09 (P1): `/api/v1/workflow/run` response missing fields** — Added `total_steps` and `output_directory` fields to engine result dict. REST API `WorkflowResult` schema now returns complete workflow execution metadata.

#### CLI Fixes

- **🔧 BUG-02 (P0): `akios setup --mock-mode` still prompts for input** — Automated setup (`--mock-mode`, `--provider`, `--defaults`) now implies `force=True` internally, bypassing the `.env` overwrite confirmation prompt. Fully non-interactive as documented.
- **🔧 BUG-04+05 (P1): `akios http` rejects uppercase methods and missing HEAD/OPTIONS** — Added `type=str.lower` for case-insensitive method matching. Added `head` and `options` to allowed HTTP methods (was 5, now 7).
- **🔧 BUG-07 (P1): `--json-output` leaks plain text from template switching** — Template switching messages ("Switching to...", "Creating workflow.yml...") now suppressed when `--json-output` is active. All output paths respect the JSON-only contract.
- **🔧 BUG-08 (P1): `AKIOS_JSON_MODE` env var has no effect** — `is_json_mode()` now checks both CLI args and `os.environ.get('AKIOS_JSON_MODE')`. Environment variable control restored for SDK/CI consumers.
- **🔧 BUG-10 (P2): Testing subcommand names inconsistent with docs** — Renamed `notes` → `show-notes`, `clear` → `clear-notes`, `log` → `log-issue` with original names as aliases for backward compatibility.
- **🔧 BUG-11 (P2): `akios timeline` searches for `*.json` instead of `*.jsonl`** — Fixed 3 glob patterns in timeline command from `*.json` to `*.jsonl` to match actual audit log format.

#### Documentation Fixes

- **📄 BUG-13 (P2): Detection system docs reference non-existent commands** — Removed `akios setup --show-environment` and `akios config show-environment` from docs (commands never existed).
- **📄 BUG-14 (P2): Detection system docs show wrong field names** — Fixed `EnvironmentInfo` fields, `ContainerType` enum values, and programmatic access code example to match actual source code.

#### Deferred

- **⏩ BUG-06 (P2): `akios doctor` duplicates `status --security`** — Confirmed as design issue. Deferred to v1.1.0 for proper command responsibility redesign (doctor → diagnostics, status → runtime state).

### Changed

- **📦 Version bump** — All version references updated to 1.0.16 across 30+ files.
- **📝 AGENTS.md** — Document version updated to 1.0.16.

### Infrastructure

- **📄 Beta tester response document** — Created `internal/docs/BETA_TESTER_RESPONSE_v1.0.16.md` with full analysis of all 15 reported bugs (11 confirmed, 4 rejected with evidence).

## [1.0.15] - 2026-02-23

### Fixed — SDK Integration Issues (7 P0 + 1 P1 Resolved)

- **🔧 P0-1: Pydantic Settings crashes on unknown env vars** — Changed `extra="forbid"` to `extra="ignore"` in `Settings` model. Downstream consumers can now pass env vars like `AKIOS_LLM_PROVIDER`, `AKIOS_FORCE_PULL`, `AKIOS_BEDROCK_MODEL_ID`, `AKIOS_BEDROCK_REGION` without triggering `ValidationError`.
- **🔧 P0-2: `--json-output` emits plain text on exception** — Exception handlers in `run_run_command()` now detect `--json-output` and emit structured JSON error blobs instead of plain text. SDK consumers always receive valid JSON regardless of success or failure.
- **🔧 P0-3: JSON output missing `error` and `error_category` fields** — Added `error` (string or null) and `error_category` (string or null, from `ErrorCategory` enum) to the `--json-output` schema. SDK consumers can now distinguish error types (configuration, runtime, security, network, validation, resource).
- **🔧 P0-4: Bedrock provider missing from cost calculation** — Added `bedrock` pricing dict with all 10 supported model IDs (Claude 3.5 Sonnet/Haiku/Opus, Llama 3.1 8B/70B/405B, Titan Express/Lite). Previously fell back to $0.002/1K tokens (8× overpriced for Haiku).
- **🔧 P0-5: Dockerfile missing `/app/.akios` directory** — Added `/app/.akios` to the `mkdir -p` command in the Dockerfile. SDK consumers mounting tmpfs at `/app/.akios` no longer risk race conditions.
- **🔧 P0-6: No `--json-output` contract tests** — Added `TestJsonOutputContract` class with 3 tests validating JSON schema for success, exception failure, and workflow error scenarios.
- **🔧 P1-1: Bedrock `ThrottlingException` raises immediately** — Added retry with exponential backoff (3 attempts, 1s/2s/4s delays) for `ThrottlingException` in both `complete()` and `chat_complete()`. Concurrent SDK usage no longer crashes on transient throttling.

### Infrastructure

- **✅ 1,523 unit tests** — All passing, 0 failures, 7 skipped.
- **📄 4 new tests** — 1 settings validation + 3 JSON output contract tests.

## [1.0.14] - 2026-02-22

### Fixed — End-User Testing Issues (13 Issues Resolved)

- **🔧 ISSUE-01+07 (P0): Template degradation on `pip install`** — Replaced `pkg_resources` (missing on Ubuntu 24.04 venv) with `importlib.resources.files()` for template bundling. All 4 workflow templates now install correctly via pip on all platforms.
- **🔧 ISSUE-02 (P0): Template switching prompt blocks Docker** — Restructured `handle_template_run()` to auto-approve template switching in non-interactive mode (`not sys.stdin.isatty()`). Docker and CI/CD pipelines no longer hang on confirmation prompts.
- **🔧 ISSUE-03 (P0): Misleading seccomp guidance in venv** — `_seccomp_available()` now detects venv environments and shows targeted guidance: "recreate venv with: `python3 -m venv --system-site-packages venv`" instead of generic kernel messages.
- **🔧 ISSUE-04 (P1): `cage down` destroys user input data** — Removed `data/input/` from `_wipe_cage_data()` targets. User input files are now preserved during cage down. Only audit logs and workflow outputs are wiped.
- **🔧 ISSUE-05 (P1): Bedrock env vars missing from Docker wrapper** — Added 6 AWS/Bedrock environment variables to `wrapper.sh` docker run command: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`, `AKIOS_BEDROCK_MODEL_ID`, `AKIOS_BEDROCK_REGION`.
- **🔧 ISSUE-06 (P1): `protect scan` rejects inline text** — Added `--text` flag and auto-detection for inline PII text (vs file paths). JSON output key changed from `"file"` to `"source"` for clarity.
- **🔧 ISSUE-08 (P2): Duplicate wrapper scripts** — Deleted stale root `./akios` wrapper. Canonical wrapper is now `src/akios/cli/data/wrapper.sh` only.
- **🔧 ISSUE-09+13 (P2): `akios init` missing `.env` and `workflows/`** — Uncommented `.env` creation code and added `workflows/` to `dirs_to_create` in init command.
- **🔧 ISSUE-10 (P2): Init message shows wrong command prefix** — Init welcome message now uses dynamic `get_command_prefix()` detection instead of hardcoded `akios` command.
- **🔧 ISSUE-11 (P2): Wrapper fallback hardcoded to version** — Changed wrapper `FALLBACK_VERSION` from `"1.0.13"` to `"latest"` to avoid manual bumps on every release.

### Fixed — Additional Issues Discovered

- **🧪 ISSUE-15: Test breakage from cage behavior change** — Updated `test_cage_secure_wipe.py` to reflect input data preservation: removed `input_files`/`input_bytes` assertions, added preservation check, changed overwrite test to use `data/output/`.
- **📄 ISSUE-16/17/18: Docs inconsistent with cage behavior** — Updated SECURITY.md, docs/security.md, and GETTING_STARTED.md to reflect that `cage down` preserves `data/input/`. Data lifecycle diagrams corrected.
- **🔧 ISSUE-19: Bedrock env vars missing from `.env` template** — Added `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `AKIOS_BEDROCK_MODEL_ID`, `AKIOS_BEDROCK_REGION` to both `.env` and `.env.example` templates in `akios init`.

### Changed

- **📦 `pkg_resources` → `importlib.resources`** — Template system now uses Python 3.9+ stdlib `importlib.resources.files()` instead of deprecated `pkg_resources`. Eliminates the `setuptools` runtime dependency.
- **🛡️ Cage down behavior** — `data/input/` is now explicitly preserved during `cage down`. Only `audit/` and `data/output/` are securely wiped. Wipe summary shows "Input data preserved" confirmation.
- **🐳 Docker wrapper** — Fallback version strategy changed from hardcoded version string to `"latest"` tag. AWS/Bedrock environment variables now forwarded into container.

### Infrastructure

- **📄 30+ docs updated** — All document version headers bumped to 1.0.14.
- **🧪 Tests updated** — Cage wipe tests aligned with new input preservation behavior.

## [1.0.13] - 2026-02-22

### Added — AWS Bedrock Provider
- **☁️ AWS Bedrock LLM provider** — New `bedrock` provider enables running AKIOS workflows against AWS Bedrock models using IAM authentication (no API key required). Supports Anthropic Claude, Meta Llama, and Amazon Titan model families via the `invoke_model` API.
- **🔧 Environment variable controls** — `AKIOS_BEDROCK_MODEL_ID` and `AKIOS_BEDROCK_REGION` environment variables for model and region override. Standard AWS credential chain (env vars, instance profile, SSO) supported.
- **📦 Optional dependency** — `pip install akios[bedrock]` installs `boto3>=1.34.0`. Bedrock provider gracefully errors if boto3 is missing.
- **🧪 25 new tests** — `test_bedrock_provider.py` covering IAM auth bypass, Anthropic/Meta/Titan response parsing, token extraction, error handling (AccessDenied, Throttling), and input validation.

### Added — Release Process Improvements
- **📝 Automated docs version update** — New `00b_update-docs-version.sh` script replaces stale version strings across all `docs/` and root `.md` files. Eliminates the recurring issue of forgotten documentation version bumps.
- **📋 GOVERNANCE.md in bundle** — Added to `01_prepare-bundle.sh` copy list (was missing from public releases).

### Changed
- **🤖 LLM agent Bedrock support** — Provider factory, API key bypass (IAM auth), default model mapping, and environment variable resolution all extended for `bedrock` provider.
- **🔒 Allowed providers** — `bedrock` added to default `allowed_providers` and Bedrock model IDs added to `allowed_models` in security settings.

### Infrastructure
- **✅ 1,519+ unit tests passing** — 0 regressions. 25 new Bedrock tests + full suite green.
- **📄 30+ docs updated** — All stale v1.0.11 references fixed across documentation.

## [1.0.12] - 2026-02-22

### Added — Structured Output & Observability
- **📊 `--json-output` CLI flag** — New `akios run --json-output` emits a structured JSON summary to stdout with workflow status, token usage, cost, and PII redaction metadata. Designed for CI/CD pipelines, automation scripts, and programmatic consumption. Distinct from `--json` (which only suppresses Rich UI formatting).
- **🔢 Token input/output tracking** — `CostKillSwitch` now tracks `tokens_input` and `tokens_output` separately alongside `total_cost`. LLM providers already return `prompt_tokens`/`completion_tokens`; these are now surfaced through the engine to the final result.
- **🛡️ PII redaction metadata** — Engine now aggregates `pii_redaction_count` and `pii_redacted_fields` across all workflow steps. Available in both `--json-output` and `output.json`.
- **📋 Enriched engine return** — `engine.run()` result dict now includes: `tokens_input`, `tokens_output`, `total_cost`, `llm_model`, `pii_redaction_count`, `pii_redacted_fields`. Same data written to `output.json` for downstream tooling.
- **🧪 12 new tests** — `test_structured_output_v1.0.12.py` covering token tracking, PII aggregation, enriched return dict, and `--json-output` flag parsing.

### Changed
- **📈 `output.json` enriched** — Now includes `pii_redaction_count`, `pii_redacted_fields` under `security`, and `tokens_input`/`tokens_output`/`llm_model` under `cost`.
- **🤖 LLM agent result enriched** — Agent `execute()` now returns `prompt_tokens`, `completion_tokens`, and `llm_model` alongside existing `tokens_used` and `cost_incurred`. Mock mode returns realistic token breakdowns.

### Infrastructure
- **✅ 1,513+ unit tests passing** — 0 regressions from observability changes.

## [1.0.11] - 2026-02-22

### Fixed — Code Quality
- **🔧 Seccomp kernel check** — `validation.py` was passing literal `$(uname -r)` string instead of evaluating it. Now uses `platform.release()` + `os.path.exists()` for correct kernel version detection.
- **📦 PyPDF2 → pypdf migration** — Replaced deprecated `PyPDF2` with `pypdf>=4.0.0` across `filesystem.py`, `pyproject.toml`, and `requirements.txt`.
- **🔇 Merkle stderr noise** — `ledger.py` no longer emits errors when audit directory doesn't exist; guarded with `parent.exists()` check, error downgraded to debug level.
- **🐍 requires-python ≥3.9** — Dropped Python 3.8 classifier (EOL), removed premature 3.14 classifier. `requires-python` now `">=3.9"`.
- **⚠️ Test return warnings** — Renamed `test_*` → `check_*` for 3 validation helper functions that returned values (pytest warning suppression).
- **📋 requirements.txt alignment** — Removed stale optional deps (fastapi, uvicorn, prometheus-client), added missing core deps (rich, questionary, google-generativeai, requests, fuzzywuzzy, python-Levenshtein).

### Fixed — Release Process (Critical)
- **🚨 Wrapper fallback stuck at 1.0.7** — `wrapper.sh` and root `./akios` had hardcoded `FALLBACK_VERSION="1.0.7"` since v1.0.7. Root cause: `bump-version.sh` used exact-match `version="$OLD"` which couldn't find `version="1.0.7"` during v1.0.8+ bumps. Fixed with regex matching.
- **🔧 bump-version.sh structural fix** — Phase 3 (CLI source) now uses regex `version="[0-9]..."` for wrapper fallback. Phase 5 now includes root `./akios`. Verification scan includes `akios` wrapper file.
- **📝 6 stale doc version headers** — Updated Document Version 1.0.9 → 1.0.11 in AGENTS.md, GETTING_STARTED.md, CONFIG.md, cli-reference.md, workflow-schema.md, api-reference.md.

### Added — Release Process Hardening
- **🛡️ Pre-release gate P5a–P5d** — New checks: wrapper.sh fallback version (P5a), root `./akios` mirror match (P5b), root VERSION file (P5c), Dockerfile OCI label (P5d). No more missed version sources.
- **🐳 Docker build Phase 8.5 + 8.6** — Post-build verification: Phase 8.5 checks `akios --version` inside the image matches pyproject.toml. Phase 8.6 verifies wrapper fallback inside the image.
- **📊 verify-version-sync.sh** — New standalone script checking all 8 version sources (pyproject.toml, src/VERSION, root VERSION, _version.py, wrapper.sh, root ./akios, Dockerfile OCI label, CHANGELOG entry). Run before any release.
- **🔄 Dynamic version checks in tests** — Docker and EC2 `test-cli.sh` and `master-test.sh` now read expected version from pyproject.toml instead of hardcoded strings. Never needs manual bumping again.

### Infrastructure
- **✅ 1,500 unit tests passing** — 0 failures, 5 skipped, 2 warnings (upstream pkg_resources only).
- **📄 RELEASE_PLAN_v1.0.11.md** — Full release plan with root cause analysis of the wrapper version gap.

## [1.0.10] - 2026-02-22

### Fixed — Security
- **🔒 `os.system` → ANSI escape** — Removed `os.system("clear")` call in `rich_output.py`, replaced with ANSI escape sequence `\033[2J\033[H`. Eliminates shell injection surface.
- **🛡️ Bare `except` → `except Exception`** — Fixed 2 bare `except:` clauses in `loader.py` and `init.py` that silently swallowed `KeyboardInterrupt` and `SystemExit`.
- **⚙️ `apply_all_quotas` no-op** — Was a pass-through stub; now delegates to `apply_resource_quotas()` for actual enforcement.
- **🧹 Engine dead stubs** — Replaced no-op `_apply_security_context` / `_record_metrics` stubs with `logger.debug()` calls for transparency.

### Added — Test Coverage
- **🧪 55 new tests** across 9 test files covering `serve` CLI, `workflow validate`, MRN PII detection, compliance scoring, doctor/NPI detection, filesystem agent, HTTP agent, output filter, and `protect show-prompt`.
- **✅ Test framework hardened** — Fixed 5 `test_init_command.py` failures (macOS platform check bypass, `--force` flag, multi-JSON output parse). All 1,495 unit tests passing, 0 failures.

### Infrastructure
- **📦 Release automation** — Auto-evidence logging added to release scripts 00–09. SHA-256 manifest generator for reproducible builds.
- **🔧 pytest.ini** — Created with proper `pythonpath = src` for Python 3.14 compatibility.

## [1.0.9] - 2026-02-21

### Added — Security Hardening
- **🐳 Non-root Docker** — Container now runs as `USER akios` (UID 1000) instead of root. Eliminates entire class of container-escape privilege escalation attacks. `Dockerfile` creates dedicated `akios` user with locked password, no login shell.
- **🧮 AST-safe condition evaluator** — New `condition_evaluator.py` (367 lines) replaces `eval()` with a whitelist-based AST walker. Only allows: comparisons, boolean logic, string/number literals, `True`/`False`/`None`, and safe builtins (`len`, `str`, `int`, `bool`). Blocks `__import__`, attribute access, function calls to dangerous builtins. Zero use of `eval()` in the entire codebase.
- **🔁 Retry with exponential backoff** — New `engine/retry.py` (189 lines) implements configurable retry logic with exponential backoff + jitter. Supports `max_retries`, `base_delay`, `max_delay`, `backoff_factor` per step. Integrates with `on_error: retry` workflow field.

### Added — Architecture
- **🏗️ Engine module split** — Monolithic `engine.py` refactored into 7 focused submodules under `src/akios/core/engine/`: `runner.py` (orchestration), `steps.py` (step execution), `conditions.py` (conditional logic), `errors.py` (error handling), `variables.py` (template interpolation), `retry.py` (backoff), `output.py` (result formatting). Public API unchanged via `__init__.py` re-exports.
- **🌐 REST API (`akios serve`)** — New FastAPI-based REST API in `src/akios/api/` with 6 endpoints: health check, workflow run, workflow list, workflow validate, status, and version. CLI command `akios serve --host --port` starts Uvicorn server. 17/17 integration tests passing.

### Changed
- **📝 Print→logging migration** — 26 `print()` calls across 10 core files converted to structured `logging.getLogger(__name__)` calls. Remaining CLI `print()` calls are intentional user-facing output (Rich panels, progress indicators).
- **🧪 Unit test suite hardened** — 1458 tests passing, 5 skipped, 0 failures. Fixed syscall test (`sandbox_enabled=True` required), performance benchmark (memory delta instead of absolute threshold), and 3 rounds of test fixture rewrites.

### Infrastructure
- **🐳 Docker test suite** — Updated to 205 tests (22 CLI + 30 security + 7 workflows + 132 demos + 14 performance). New tests: `serve --help`, `workflow validate`, insurance PII detection, non-root container verification, safe condition evaluator hardening, setuid/setgid audit.
- **☁️ EC2 test suite** — Updated to 207 tests (22 CLI + 29 security + 7 workflows + 132 demos + 17 performance). New tests mirror Docker additions plus serve benchmarks, compliance JSON, and timeline JSON performance checks.
- **📋 Release process** — Test count references updated across `RELEASE_PROCESS.md`, `pre_release_gate.sh`, and `post_release_gate.sh`.

## [1.0.8] - 2026-02-19

### Added — PII Detection
- **🔌 Pluggable PII backend** — New `PIIDetectorProtocol` (runtime-checkable Protocol) enables swappable detection engines. Factory function `create_pii_detector(backend=)` reads `pii_backend` from settings. Regex is default; Presidio available as optional backend.
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

**Legal/certified features** (FranceConnect, eIDAS, hard HDS blocks, official PDFs) are planned for a future licensed edition.

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
