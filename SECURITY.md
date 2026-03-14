# AKIOS Security Policy
**Document Version:** 1.5.0
**Date:** 2026-03-11

## 🔒 Security Overview

AKIOS v1.5.0 is a **minimal, open-source security cage** for AI agents.  
We take security very seriously — the entire product is built around hard containment, real-time protection, and provable audit.

This policy explains how we handle vulnerabilities in the open runtime.

## 📋 Supported Versions

| Version | Supported     | Security Updates |
|---------|---------------|------------------|
| 1.0.x   | ✅ Active     | ✅ Full Support   |
| <1.0    | ❌ End of Life| ❌ No Support    |

## 🚨 Reporting Vulnerabilities

**DO NOT report security issues on public GitHub.**

Send private reports to: **security@akioud.ai**

### What to Include
- Clear description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact (e.g. sandbox bypass, PII leak, cost overrun)
- Suggested fix (if any)
- Your contact info

### Our Response Process
1. **Acknowledgment**: Within 24 hours
2. **Triage & Validation**: Within 72 hours
3. **Fix Development**: 2–4 weeks (depending on severity)
4. **Coordinated Disclosure**: We release fix + advisory together
5. **Credit**: We publicly thank responsible reporters (Hall of Fame)

## 🛡️ What We Protect In v1.5.0
- Security sandboxing (kernel-hard on native Linux, strong policy-based in Docker)
- Syscall interception & resource quotas
- Real-time PII redaction (44 patterns across 6 categories)
- Enforced cost & infinite loop kill-switches
- Merkle tamper-evident audit ledger
- **Non-root Docker container** — containers run as UID 1001 by default
- **AST-safe condition evaluator** — no `eval()` anywhere in the codebase
- **REST API** — self-hosted FastAPI server (`akios serve`) with OpenAPI spec
- **Cage down data destruction** — session data wipe (audit logs, workflow outputs)
- **HTTPS domain whitelist** — selective network access for HTTP agent
- **`--exec` rejection** — shell-injection trap blocks arbitrary command execution
- **`akios http`** — secure HTTP requests with domain whitelisting & PII redaction
- **`akios protect show-prompt`** — preview interpolated + redacted LLM prompts

**Security Cage Lifecycle:**
- `cage up` → activate protections → workflows execute → data generated
- `cage down` → **session data destroyed** (audit/, data/output/) → input data preserved

**Secure Data Erasure (cage down):**
- Each file is overwritten with cryptographically random bytes, fsynced to disk, overwritten with zeros, fsynced again, then deleted (`unlink`)
- `--passes N` option repeats the overwrite cycle N times (default: 1)
- `--fast` option skips overwrite and just deletes (for CI/CD cleanup where forensic recovery is not a concern)
- ⚠️ **SSD caveat**: On solid-state drives with wear-leveling, overwritten sectors may be remapped. Extra passes have limited benefit. For maximum security on SSDs, use full-disk encryption (LUKS/FileVault) as the underlying layer.

**Network Security:**
- Default: All network access blocked
- `allowed_domains` whitelist for HTTP agent (specific domains only)
- LLM APIs always permitted (OpenAI, Anthropic, Grok, Mistral, Gemini, Bedrock, Ollama)

**No guarantees**: No software is 100% secure.  
Users must secure their environment and validate outputs.

## 📞 Contact

Security reports: **security@akioud.ai**  
General questions: **hello@akios.ai**

Thank you for helping keep the cage strong.

*AKIOS — Where AI meets unbreakable security*  
*Use responsibly. Your safety and compliance are your responsibility.* 🛡️
