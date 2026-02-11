# AKIOS Security Policy
**Document Version:** 1.0  
**Date:** 2026-01-25  

## 🔒 Security Overview

AKIOS v1.0 is a **minimal, open-source security cage** for AI agents.  
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

## 🛡️ What We Protect In v1.0
- Security sandboxing (kernel-hard on native Linux, strong policy-based in Docker)
- Syscall interception & resource quotas
- Real-time PII redaction (including healthcare: NPI, DEA, Medical Record Numbers)
- Enforced cost & infinite loop kill-switches
- Merkle tamper-evident audit ledger
- **Cage down data destruction** — complete session data wipe (audit, outputs, inputs)
- **HTTPS domain whitelist** — selective network access for HTTP agent
- **`--exec` rejection** — shell-injection trap blocks arbitrary command execution
- **`akios http`** — secure HTTP requests with domain whitelisting & PII redaction
- **`akios protect show-prompt`** — preview interpolated + redacted LLM prompts

**Security Cage Lifecycle:**
- `cage up` → activate protections → workflows execute → data generated
- `cage down` → **all data destroyed** (audit/, data/output/, data/input/) → zero residue

**Network Security:**
- Default: All network access blocked
- `allowed_domains` whitelist for HTTP agent (specific domains only)
- LLM APIs always permitted (OpenAI, Anthropic, Grok, Mistral, Gemini)

**No guarantees**: No software is 100% secure.  
Users must secure their environment and validate outputs.

## 📞 Contact

Security reports: **security@akioud.ai**  
General questions: **hello@akios.ai**

Thank you for helping keep the cage strong.

*AKIOS — Where AI meets unbreakable security*  
*Use responsibly. Your safety and compliance are your responsibility.* 🛡️
