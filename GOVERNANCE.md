# AKIOS Governance

**Version:** 1.0.13  
**Last Updated:** February 22, 2026  
**Status:** Active

## Overview

AKIOS is licensed under the **GNU General Public License v3.0 (GPL-3.0) ONLY**. This is a copyleft license that requires all derivative works to also be licensed under **GPL-3.0 ONLY** (not GPL-3.0-or-later). This document describes how decisions are made, who has authority, and how the community participates in shaping the project's direction.

**License Clarification:**
- **GPL-3.0 ONLY** (not "GPL-3.0-or-later") - You cannot relicense under GPL-4.0 or any future version
- **No dual licensing** - AKIOS will not offer commercial/proprietary licenses
- **No relicensing** - Cannot be converted to MIT, Apache, or proprietary licenses without following governance process (unanimous core team + community veto)
- **All contributions are GPL-3.0** - By contributing code, you agree it's licensed under GPL-3.0

**Governance Philosophy:**
- **Transparent**: All decisions and discussions are public
- **Inclusive**: Community input shapes the roadmap
- **Meritocratic**: Contributions earn influence
- **Pragmatic**: Balance between consensus and velocity

---

## Project Structure

### Core Team

**Role:** Final decision authority, code ownership, release management

**Responsibilities:**
- Review and merge pull requests
- Triage issues and feature requests
- Maintain code quality standards
- Release planning and versioning
- Security vulnerability management
- Community moderation

**Current Core Team:**
- TBD (Founding maintainers)

**How to Join:**
- Sustained high-quality contributions (10+ merged PRs)
- Demonstrated understanding of codebase
- Active community participation (Discord, GitHub Discussions)
- Nomination by existing core team member
- Unanimous approval by core team

### Contributors

**Role:** Code, documentation, and community contributions

**Responsibilities:**
- Submit pull requests
- Review others' PRs
- Answer questions in Discord/GitHub
- Report bugs and suggest features
- Improve documentation

**Recognition:**
- Listed in CONTRIBUTORS.md
- Contributor role in Discord
- Eligibility for swag/rewards (when available)

**How to Become a Contributor:**
- Merge at least one pull request
- Automatic recognition after merge

### Community Members

**Role:** Users, adopters, feedback providers

**Responsibilities:**
- Use AKIOS in projects
- Report bugs and issues
- Suggest features and improvements
- Share use cases and success stories
- Help other users in Discord

**Participation:**
- No formal requirements
- Open to everyone

---

## Decision-Making Process

### Types of Decisions

#### 1. Day-to-Day Decisions (Low Impact)

**Examples:**
- Bug fixes
- Documentation improvements
- Minor feature enhancements
- Code refactoring (no API changes)

**Process:**
1. Contributor opens pull request
2. Core team member reviews
3. If approved, merged (no additional approval needed)
4. If changes requested, contributor iterates

**Timeline:** 24-48 hours for review

#### 2. Significant Decisions (Medium Impact)

**Examples:**
- New features
- API additions (backward-compatible)
- Dependency updates
- Performance optimizations

**Process:**
1. Contributor opens GitHub Issue or Discussion
2. Community provides feedback (7-day discussion period)
3. Core team member summarizes consensus
4. If consensus reached, contributor implements
5. Pull request reviewed and merged

**Timeline:** 1-2 weeks from proposal to merge

#### 3. Major Decisions (High Impact)

**Examples:**
- Breaking API changes
- Architecture redesigns
- License changes
- New core dependencies
- Major version releases (v2.0, v3.0)

**Process:**
1. Core team member (or active contributor) opens RFC (Request for Comments) in GitHub Discussions
2. RFC includes:
   - Problem statement
   - Proposed solution
   - Alternatives considered
   - Migration strategy (if breaking change)
3. Community discussion (minimum 14 days)
4. Core team meeting (weekly) to discuss
5. Decision made by core team (consensus or majority vote)
6. Decision documented in RFC thread
7. Implementation plan created

**Timeline:** 3-4 weeks minimum

#### 4. Governance Decisions

**Examples:**
- Changes to this GOVERNANCE.md
- Core team membership changes
- Project name/branding changes
- **License changes (GPL-3.0 is permanent unless this process followed)**

**Process:**
1. Core team member proposes change
2. RFC in GitHub Discussions (minimum 21 days)
3. Core team vote (unanimous approval required)
4. Community veto possible (if 100+ contributors object, proposal rejected)
5. Decision documented

**Timeline:** 4+ weeks

**Note on License Changes:**
- AKIOS is committed to GPL-3.0
- License changes are extremely unlikely and would require overwhelming justification
- Any license change must remain copyleft (no proprietary relicensing)

---

## Consensus and Voting

### Consensus Model

**Preferred approach:** Lazy consensus

**How it works:**
- Proposal made publicly (GitHub Issue/Discussion)
- If no objections within review period → assumed approved
- If objections raised → discussion continues until resolved

**Benefits:**
- Fast for uncontroversial decisions
- Inclusive (silence = consent, not exclusion)

### Voting (When Consensus Fails)

**When required:**
- Breaking changes with significant disagreement
- Core team membership decisions
- Major resource allocation decisions

**Voting Rights:**
- Core team members only (1 vote each)

**Thresholds:**
- Simple majority (>50%): Feature acceptance, minor policy changes
- Supermajority (>66%): Breaking changes, new core dependencies
- Unanimous (100%): Core team membership, governance changes

**Voting Process:**
1. Motion proposed in GitHub Discussion
2. Voting period: 7 days
3. Core team members vote publicly (comment with +1, -1, or abstain)
4. Result calculated and documented

---

## Contribution Acceptance Criteria

### Pull Request Requirements

**All PRs must:**
- ✅ Pass CI/CD checks (tests, linting)
- ✅ Include tests for new functionality
- ✅ Update documentation (if user-facing changes)
- ✅ Follow code style guidelines (see CONTRIBUTING.md)
- ✅ Include commit messages explaining "why" (not just "what")
- ✅ **Be GPL-3.0 compatible (by submitting PR, you agree your contribution is licensed under GPL-3.0)**

**PRs are rejected if:**
- ❌ Breaks existing functionality (without good reason)
- ❌ Lacks tests
- ❌ Introduces security vulnerabilities
- ❌ Significantly degrades performance (without justification)
- ❌ Violates coding standards
- ❌ Duplicates existing functionality

**Gray Areas:**
- Performance vs. readability trade-offs → Discuss in PR comments
- API design disagreements → Escalate to GitHub Discussion
- Scope creep → Split into multiple PRs

---

## Roadmap Planning

### Quarterly Roadmap Process

**Timeline:**
- Month 1: Community input (GitHub Discussions, Discord polls)
- Month 2: Core team reviews feedback, drafts roadmap
- Month 3: Roadmap published, work begins

**Input Sources:**
1. GitHub Issues (feature requests, bug reports)
2. Discord discussions (#feedback channel)
3. Community surveys (quarterly)
4. Production user feedback (direct outreach)
5. Security audits and compliance requirements

**Prioritization Criteria:**
1. Security vulnerabilities (highest priority)
2. Production blockers (cannot deploy without fix)
3. High-impact features (many users affected)
4. Compliance requirements (GDPR, EU AI Act)
5. Community-requested features (upvotes, comments)
6. Technical debt reduction
7. Nice-to-have enhancements

**Published Artifacts:**
- Quarterly roadmap document (GitHub Discussions)
- GitHub Projects board (visual tracking)
- Release milestones (GitHub Releases)

---

## Community Input Mechanisms

### 1. GitHub Issues

**Purpose:** Bug reports, feature requests

**Process:**
- Anyone can open
- Core team triages (labels, milestones)
- Community can upvote/comment

**Response SLA:**
- Triage: <48 hours (business days)
- First response: <7 days

### 2. GitHub Discussions

**Purpose:** Ideas, RFCs, questions

**Process:**
- Anyone can start discussion
- Community provides input
- Core team summarizes and decides

**Categories:**
- 💡 Ideas (feature proposals)
- 🛠️ Development (technical discussions)
- ❓ Q&A (user questions)
- 📢 Announcements (project updates)
- 🎓 Show & Tell (community projects)

### 3. Discord

**Purpose:** Real-time community interaction

**Channels:**
- #feedback (feature requests, UX feedback)
- #help (user support)
- #contributors (contribution coordination)
- #general (community chat)

**Process:**
- Informal discussions
- Important topics escalated to GitHub

### 4. Community Surveys

**Frequency:** Quarterly

**Topics:**
- Feature priorities
- Pain points
- Use cases
- Deployment environments

**Results:**
- Published publicly (anonymized)
- Inform roadmap decisions

### 5. Monthly Community Call

**Format:** Virtual meeting (Zoom/Discord)

**Agenda:**
- Roadmap updates
- Feature demos
- Q&A with core team
- Community showcases

**Recording:**
- Published to YouTube
- Summary posted to GitHub Discussions

---

## Conflict Resolution

### Types of Conflicts

#### 1. Technical Disagreements

**Example:** "Should we use library X or library Y?"

**Resolution:**
1. Discuss in PR comments or GitHub Discussion
2. Present benchmarks, trade-offs, references
3. Core team member makes final decision (if no consensus)
4. Document reasoning for future reference

#### 2. Behavioral Issues

**Example:** Code of Conduct violations

**Resolution:**
1. Report to core team (email: conduct@akios.ai)
2. Core team investigates privately
3. Warning, temporary ban, or permanent ban (depending on severity)
4. Decision communicated to involved parties
5. Public announcement (if warranted)

**Appeals Process:**
- Email conduct@akios.ai with appeal reasoning
- Different core team member reviews
- Final decision within 7 days

#### 3. Governance Disputes

**Example:** "This decision wasn't made according to governance process"

**Resolution:**
1. Raise issue in GitHub Discussion
2. Core team reviews process adherence
3. If violation confirmed → decision revisited
4. If no violation → decision stands, clarification documented

---

## Release Process

### Version Numbering (Semantic Versioning)

**Format:** MAJOR.MINOR.PATCH (e.g., 1.2.3)

- **MAJOR:** Breaking changes (v1.0 → v2.0)
- **MINOR:** New features (backward-compatible)
- **PATCH:** Bug fixes (backward-compatible)

### Release Cadence

- **Patch releases:** As needed (bug fixes, security)
- **Minor releases:** Monthly (feature accumulation)
- **Major releases:** Yearly (or when breaking changes accumulated)

### Release Authority

**Patch & Minor:**
- Any core team member can release
- Must pass CI/CD
- Must update CHANGELOG.md

**Major:**
- Requires core team vote (supermajority)
- Requires migration guide
- Requires 2-week deprecation notice (if breaking)

### Release Checklist

- [ ] All tests passing
- [ ] CHANGELOG.md updated
- [ ] Version bumped (pyproject.toml, _version.py)
- [ ] Documentation updated
- [ ] Release notes drafted (GitHub Releases)
- [ ] Security vulnerabilities addressed
- [ ] Breaking changes documented (if major)
- [ ] PyPI package published
- [ ] Docker image published
- [ ] Announcement posted (X, LinkedIn, Discord)

---

## Security Vulnerability Handling

### Reporting

**Channel:** security@akios.ai (private)

**Do NOT:** Open public GitHub Issue for security vulnerabilities

**Response SLA:**
- Acknowledgment: <24 hours
- Initial assessment: <72 hours
- Patch released: <7 days (critical), <30 days (high)

### Disclosure Process

1. Researcher reports vulnerability privately
2. Core team acknowledges and investigates
3. Patch developed (private repo or branch)
4. Coordinated disclosure date set (with researcher)
5. Patch released
6. Public advisory published (GitHub Security Advisories)
7. Credit to researcher (if desired)

**Policy:** Responsible disclosure (90-day window for patching)

---

## Forking and Derivatives

### You Must Meet These Requirements (GPL-3.0 Compliance):

**MANDATORY:**
- ✅ Your fork MUST be licensed under GPL-3.0 (copyleft requirement)
- ✅ You MUST include the original LICENSE file
- ✅ You MUST include copyright notices from original AKIOS
- ✅ You MUST disclose source code of your fork

**RECOMMENDED:**
- ✅ Attribution (credit original AKIOS project)
- ✅ Clear branding (don't confuse users about official vs. fork)
- ✅ Link back to upstream AKIOS repository

**PROHIBITED:**
- ❌ Relicensing under non-GPL-3.0 license (violates GPL-3.0)
- ❌ Distributing without source code (violates GPL-3.0)
- ❌ Removing copyright notices (violates GPL-3.0)
- ❌ Claiming fork is "proprietary" or "closed source" (impossible under GPL-3.0)

### Upstream Contributions:

- If your fork has valuable features → Consider PR to upstream AKIOS
- We're open to merging good ideas from forks
- Your PR will be licensed under GPL-3.0 (same as AKIOS)

---

## Communication Channels

### Public Channels

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** RFCs, ideas, Q&A
- **Discord:** Real-time chat (https://discord.gg/akios)
- **X (Twitter):** Announcements (@akios_ai)
- **LinkedIn:** Blog posts, case studies

### Private Channels

- **Core team email:** team@akios.ai
- **Security email:** security@akios.ai
- **Code of Conduct email:** conduct@akios.ai

---

## Changes to Governance

This document is not set in stone. As AKIOS grows, governance will evolve.

**How to propose changes:**
1. Open GitHub Discussion with proposal
2. Tag: "governance"
3. Minimum 21-day discussion period
4. Core team vote (unanimous approval required)
5. Document updated

**History:**
- v1.0 (January 31, 2026): Initial governance document

---

## Inspiration and Attribution

This governance model is inspired by:
- Python Enhancement Proposals (PEP-1)
- Rust RFC process
- Node.js governance
- Apache Software Foundation

We stand on the shoulders of giants. Thank you to these communities for sharing their governance wisdom.

---

## Questions?

- GitHub Discussions: https://github.com/akios-ai/akios/discussions
- Discord #general: https://discord.gg/akios
- Email: team@akios.ai

**This governance document is a living document. Help us improve it.**
