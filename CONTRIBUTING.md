# Contributing to AKIOS
**Document Version:** 1.2.0
**Date:** 2026-02-25

Thank you for your interest in AKIOS!  
AKIOS is a **deliberately minimal, security-first containment layer** for AI agents in its early stage (v1.2.0).

Our current priority is **stability, auditability, and extreme simplicity**.
Because of this, contribution rules are intentionally strict at this stage.

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you agree to abide by its terms.

## Developer Certificate of Origin (DCO)

We require a DCO sign-off on every commit. Add `Signed-off-by: Your Name <email>` to each commit (use `git commit -s` to automate). By signing off, you certify the DCO in `DCO.md`.

## Current Contribution Stance (February 2026 – v1.2.0)

**We are currently not accepting unsolicited pull requests**, with **very few exceptions**:

- Critical security vulnerabilities (with clear reproduction steps)
- Severe correctness/denial-of-service issues in the core sandbox/runtime

For **all other changes** (including documentation, formatting, refactoring, new features, tests, performance improvements, etc.):

1. **Open an issue first**  
   Describe the concrete problem you see  
   Explain the security/reliability impact  
   Propose your intended approach (high-level)

2. Wait for explicit maintainer agreement  
   Only once a maintainer says "yes, go ahead and implement" should you open a PR

We enforce this process to:
- Protect the project's security invariants
- Keep the codebase auditable and minimal
- Avoid wasting contributor and maintainer time on changes that don't align with current priorities

## If you want to contribute seriously

We are **very happy** to work closely with thoughtful contributors who:
- Take the time to deeply understand the security/runtime philosophy (please read the full codebase + docs first)
- Identify meaningful gaps (containment bypasses, audit weaknesses, edge-case failures, constrained env issues…)
- Communicate clearly and patiently

If this describes you, please don't hesitate to open a well-written issue — we will engage seriously.

## Quick Summary – What We Currently Accept

| Type of contribution                  | Status in v1.0.16           | Process required                  |
|---------------------------------------|-----------------------------|------------------------------------|
| Critical security fix                 | Welcome                     | Issue first → fast-track possible  |
| Bug / correctness issue (non-trivial) | Case-by-case                | Issue → explicit green light       |
| Documentation / typos / formatting    | Not accepted at this time   | —                                  |
| Refactoring / style / tests           | Not accepted at this time   | —                                  |
| New features / integrations / tools   | Not accepted at this time   | —                                  |
| Performance optimizations             | Case-by-case (very rare)    | Issue → explicit green light       |

## How to open a great issue

- Title: Clear and specific ("Potential fd leak in restricted mode when X")
- Description: Problem → Impact (security/runtime) → Reproduction steps → Proposed direction
- Be concise but precise

Thank you very much for reading this far, and thank you for respecting our current constraints.  
We deeply appreciate everyone who wants to help make AI agents safer.

The AKIOS team 🛡️
