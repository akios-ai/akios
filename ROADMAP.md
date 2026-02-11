# AKIOS Roadmap – v1.0, Future Open & PRO  
**Document Version:** 1.0.5  
**Date:** 2026-02-10  

This roadmap clearly separates the three tracks:  
- **AKIOS Open Runtime v1.0** (free, minimal security cage – locked)  
- **Future Open Releases** (V1.x / V2.0 – gradual usability improvements, community-driven)  
- **AKIOS PRO** (paid legal upgrade – regulated sectors only)

No feature bleed. Open stays clean & viral. PRO captures regulated industry.

### 1. AKIOS Open Runtime v1.0 – Current & Locked (January 2026)

**Focus**: Strong cross-platform security foundation – Docker-based protection
**License**: GPL-3.0-only (free, open-source)
**Status**: ✅ Final & locked – ship this

**Key Features (no changes allowed)**:
- Policy-based container isolation (Docker security across all platforms)
- Full kernel-hard sandbox on native Linux (cgroups + seccomp + resource quotas)
- Syscall-level I/O interception & access control (Linux native)
- Real-time PII redaction (>95% accuracy, <50ms)
- Cryptographic Merkle tamper-evident audit ledger + clean PDF/JSON export
- Hard cost & infinite loop kill-switches
- Sequential execution only
- 4 core agents: LLM, HTTP/web, Filesystem, Tool Executor
- Minimal CLI (20 commands: init, run, status, cage, doctor, templates, files, logs, audit, clean, setup, compliance, testing, output, timeline, docs, protect, http)
- 3–4 high-quality static example workflows
- Docker wrapper + native Linux binary (cross-platform capable)

**Philosophy**: Minimal by design. Strong security foundation across all platforms.

### 2. Future Open Releases (V1.x / V2.0) – Planned Gradual Improvements

**Focus**: Make the cage more usable without diluting security  
**License**: GPL-3.0-only (free, open-source)  
**Timeline**: 2026–2027 (no fixed dates – community & contributor-driven)

**Prioritized Evolution** (rough order – no promises on dates):

**V1.1 – Usability & Developer Experience** (High Priority – Next logical step)  
- Full CLI suite (15–23 essential commands)  
- Basic REST API (20–30 endpoints)  
- 10+ high-quality example templates  
- Improved logging & error messages  
- Configuration documentation generator  

**V1.2 – Orchestration Expansion** (Medium–High Priority)  
- Parallel simple + conditional execution  
- Loop & retry patterns  
- Fan-out / map-reduce basics  
- Enhanced state persistence (filesystem only)  
- Basic multi-agent coordination  

**V1.3 – Agent Ecosystem Growth** (Medium Priority)  
- Database connectors (PostgreSQL, SQLite)  
- Email & Slack agents  
- GitHub agent (issue/comment/PR)  
- Webhooks receiver  
- More local model support (llama.cpp, etc.)  

**V2.0 Horizon – Advanced** (Low Priority – Long-term)  
- Prometheus / Jaeger basic integration  
- Plugin system for community agents  
- Basic multi-tenant isolation  
- Community marketplace for templates/agents  

**Guiding Rules for All Future Open Releases**:
1. Security & governance first — every feature must preserve or strengthen the cage  
2. Minimalism remains — add only what makes the cage more usable for security-conscious users  
3. No legal/certified features — FranceConnect, eIDAS, hard HDS, official PDFs → PRO only  
4. Community-driven — priorities shift based on real user needs & contributions  
5. No fixed dates — progress depends on contributors & core team

### 3. AKIOS PRO – Paid Legal Upgrade (Q2–Q3 2026 Initial Launch)

**Focus**: Instant legal permission for regulated/high-risk use  
**License**: Proprietary (encrypted plugin + license key)  
**Pricing**: €48,000+/year (unlimited agents, on-prem)  
**Status**: Planned – after v1.0 Open ships

**Exclusive Features** (only these in initial PRO – no more):
- FranceConnect / ProConnect-S official identity verification  
- La Poste qualified eIDAS timestamping & signatures  
- Official 12-page regulator-ready PDF reports (CNIL/ANSM templates)  
- Hard HDS/SecNumCloud enforcement blocks  
- Qualified eIDAS human approval workflows  
- License validation & basic usage tracking  

**How it works**:  
- Load encrypted plugin + valid license key  
- Same workflows, same infrastructure  
- `--fr-strict` mode activates PRO features  
- Fallback to open behavior if no/invalid license  

**Target Customers**:  
- Banks & insurance  
- Hospitals & health  
- Public sector & administrations  
- Any EU AI Act high-risk deployment

**No** distributed clustering, AI governance, threat detection, multi-cloud optimization in initial PRO — those are future expansions.

### 4. Timeline Summary (High-Level)

- **Jan 2026**: AKIOS Open v1.0 launch (free cage)  
- **2026**: V1.x open releases (gradual usability)  
- **Q2–Q3 2026**: AKIOS PRO initial pilots & launch (€48k+)  
- **2027+**: PRO expansions (if demand justifies)

