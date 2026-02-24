# Security Features
**Document Version:** 1.0.16  
**Date:** 2026-02-22  

## Security Overview

AKIOS v1.0.16 provides **defense-in-depth security** for AI agent workflows. The system is built around kernel-level isolation (native Linux) or container-based isolation (Docker), real-time PII protection, cryptographic audit trails, and strict cost controls.

## Supported Versions

| Version | Supported     | Security Updates |
|---------|---------------|------------------|
| 1.0.x   | Active        | Full Support     |
| <1.0    | End of Life   | No Support       |

## Reporting Vulnerabilities

**DO NOT report security issues on public GitHub.**

Send private reports to: **security@akioud.ai**

### What to Include
- Clear description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact (e.g. sandbox bypass, PII leak, cost overrun)
- Suggested fix (if any)

### Our Response Process
1. **Acknowledgment**: Within 24 hours
2. **Triage & Validation**: Within 72 hours
3. **Fix Development**: 2–4 weeks (depending on severity)
4. **Coordinated Disclosure**: Fix + advisory released together
5. **Credit**: Responsible reporters acknowledged in Hall of Fame

---

## Security Cage

The Security Cage is the core abstraction — a controlled environment where AI workflows execute with full protections active.

### Activating the Cage

```bash
# Activate full security: PII redaction, network lock, sandbox, audit
akios cage up

# Ablation mode — disable specific protections for benchmarking
akios cage up --no-pii --no-audit --no-budget

# Check current security posture
akios cage status

# Run diagnostics
akios doctor
```

When the cage is **ACTIVE**, these protections are enforced:
- **PII Redaction**: All inputs/outputs automatically scanned and redacted
- **Network Lock**: Only LLM API endpoints + configured `allowed_domains` pass
- **Sandbox**: Process isolation via cgroups v2 + seccomp-bpf (native) or container policy (Docker)
- **Audit Logging**: Every action cryptographically logged with Merkle chains
- **Cost Controls**: Budget kill-switches halt execution if limits exceeded

### Deactivating the Cage

```bash
# Full cage down — destroy ALL session data (default)
akios cage down

# Secure overwrite with multiple passes (GDPR Art. 17)
akios cage down --passes 3

# Fast mode — skip secure overwrite for speed (dev only)
akios cage down --fast

# Dev mode — relax protections but keep data for debugging
akios cage down --keep-data
```

⚠️ **WARNING: `cage down` is irreversible data destruction**

**Default behavior `akios cage down`:** Permanently destroys:
- ✂️ `audit/` — All Merkle-chained audit logs (cannot be recovered)
- ✂️ `data/output/` — All workflow outputs and `output.json` (cannot be recovered)
- ✂️ `data/input/` — All user-provided input files (cannot be recovered)

**After `cage down`: ZERO DATA RESIDUE. Nothing survives.**

This is the cage's core security promise:
- No audit trail left behind
- No outputs stored on disk
- No input data leaked
- No recovery possible

**Use `--keep-data` only during active development** when you need to inspect intermediate results:
```bash
# Dev mode: Keep data for debugging, relax security
akios cage down --keep-data
# Result: Data preserved, but protections disabled (not suitable for production)
```

### Cage Status Verification

```bash
# Check current cage security posture
akios cage status

# Output shows:
# Security Cage: ACTIVE
# ├─ PII Redaction: ENABLED
# ├─ Network Lock: HTTPS LOCKED
# ├─ LLM Access: ALLOWED
# ├─ Sandbox: ENFORCED
# ├─ Audit Trail: RUNNING
# └─ Cost Controls: ACTIVE
```

### Bypass Resistance

The cage blocks four attack vectors:

1. **Network exfiltration**: External HTTP calls blocked (except approved LLM APIs)
2. **Command injection**: Only approved agents can execute actions — no arbitrary shell commands
3. **Cost abuse**: Budget kill-switch halts execution when limits exceeded
4. **Shell injection via `--exec`**: The `akios run --exec` flag is a security trap that rejects shell injection attempts with "Direct shell execution is not permitted inside the security cage" and logs the attempt to the audit trail

---

## PII Protection

AKIOS detects and redacts 53 PII patterns across 6 categories (personal, financial, health, digital identity, communication, location).

### Scanning Files

```bash
# Scan a file for PII before processing
akios protect scan data/input/document.txt

# Preview what the LLM will see after redaction
akios protect preview templates/workflow.yml

# Show the exact interpolated & redacted prompt sent to the LLM
akios protect show-prompt templates/healthcare.yml
```

### PII Marker Format

Detected PII is replaced with typed markers using guillemet notation:

| PII Type | Marker | Example |
|----------|--------|---------|
| Email | `«EMAIL»` | john@example.com → `«EMAIL»` |
| SSN | `«SSN»` | 442-01-9821 → `«SSN»` |
| Phone | `«PHONE»` | (319) 555-1701 → `«PHONE»` |
| Name | `«NAME»` | James T. Kirk → `«NAME»` |
| Address | `«ADDRESS»` | 1701 Enterprise Way → `«ADDRESS»` |
| Credit Card | `«CREDIT_CARD»` | 4111-1111-1111-1111 → `«CREDIT_CARD»` |
| NPI | `«US_NPI»` | 1234567893 → `«US_NPI»` |
| DEA Number | `«US_DEA»` | AB1234563 → `«US_DEA»` |
| Medical Record | `«MEDICAL_RECORD_NUMBER»` | MRN-2024-0847 → `«MEDICAL_RECORD_NUMBER»` |

In terminal output, PII markers display in **magenta** for instant visual identification. Original text appears in red for contrast.

### When Redaction Happens

1. **Before LLM calls**: All input data is scanned and PII replaced with markers
2. **After LLM responses**: Output is re-scanned for any PII the model may have generated
3. **In audit logs**: All logged data is automatically redacted
4. **In exports**: Audit exports and compliance reports contain only redacted text

---

## Deployable Output

Every workflow execution produces a structured `output.json` artifact:

```bash
# Retrieve the latest execution result as JSON
akios output latest
```

The output includes:
- **Metadata**: version, workflow name, workflow ID, timestamp
- **Execution**: status, steps executed, execution time
- **Security**: PII redaction status, audit enabled, sandbox enabled
- **Cost**: total cost, budget limit, remaining budget, over-budget flag
- **Results**: per-step array with agent, action, status, timing, output text

Designed for CI/CD pipeline integration — pipe directly to `jq`, feed to downstream systems, or store as compliance artifacts.

---

## Data Lifecycle

The cage enforces a strict data lifecycle:

```
cage up → protections activate → workflows execute → data generated
                                                           ↓
cage down → audit/ destroyed → data/output/ destroyed → data/input/ PRESERVED
                                                           ↓
                                                Session artifacts removed
                                                User input data retained
```

This guarantees no session artifacts (audit logs, workflow outputs) survive a cage teardown. User input data (`data/input/`) is preserved to prevent accidental data loss.

---

## Audit & Compliance

### Merkle-Chained Audit Trail

Every operation is logged with a SHA-256 hash chained to the previous entry, creating a tamper-evident ledger. The Merkle root hash is persisted on every flush and compared at verification time to detect tampering:

```bash
# Verify audit chain integrity (compares stored vs recomputed Merkle root)
akios audit verify

# Machine-readable verification (includes stored root and match status)
akios audit verify --json

# View audit ledger statistics (event count, size, Merkle root)
akios audit stats
akios audit stats --json

# Rotate audit log (archive current + start fresh with Merkle chain linkage)
akios audit rotate
akios audit rotate --json

# Export full audit trail for compliance systems
akios audit export --json

# Save as compliance artifact
akios audit export --json > audit-report.json
```

**Verification Process:** `akios audit verify` rebuilds the Merkle tree from audit events and compares the recomputed root against the stored root hash. If they match, the trail is **VERIFIED** (tamper-free). If they differ, it reports **TAMPERED** and returns exit code 1.

### Compliance Frameworks

AKIOS audit exports are designed for regulatory examination across sectors:

| Sector | Regulation | Compliance Features |
|--------|-----------|-------------------|
| Healthcare | HIPAA, HITECH | PHI redaction, access logging, audit proof |
| Banking | PCI-DSS, BSA-AML, GLBA | Financial PII redaction, transaction audit |
| Insurance | NAIC, State DOI | Claim data protection, fraud detection audit |
| Accounting | SOX 302/404, PCAOB | Financial audit trail, control verification |
| Government | FISMA, FedRAMP, Privacy Act | Clearance data protection, access audit |
| Legal | ABA Rule 1.6, FRE 502 | Privilege protection, case data redaction |
| EU/France | RGPD, CNIL, ANSSI | DCP redaction, RGS compliance, data lifecycle |

### Budget Controls

```bash
# View current budget status
akios status --budget

# Budget kill-switch in action (set very low limit)
AKIOS_BUDGET_LIMIT_PER_RUN=0.10 akios run workflow.yml
```

Default limits:
- **Budget per workflow**: $1.00
- **Max tokens per call**: 1000
- **Automatic termination**: Workflow halted if budget exceeded

---

## Platform Security

### Native Linux (Maximum Security)

With sudo privileges on Linux kernel 5.4+:
- **cgroups v2**: Real CPU, memory, and I/O resource quotas
- **seccomp-bpf**: Syscall filtering with BPF bytecode enforcement
- **Process isolation**: Each agent runs in isolated cgroup
- **Kernel-hardened**: Direct kernel integration, minimal attack surface

Requirements:
- Linux kernel 5.4+ with seccomp support
- System packages: `libseccomp-dev` and `python3-seccomp`
- sudo privileges for full kernel-hard protection

Without sudo, AKIOS gracefully degrades to policy-based mode (same protections as Docker).

### Docker (Cross-Platform)

Container-based isolation on Linux, macOS, and Windows:
- **Container boundary**: Process isolation from host system
- **Policy-based sandbox**: Command allowlisting and path restrictions
- **Resource limits**: Container-level CPU/memory caps
- **No special permissions**: Works without sudo or kernel modules

Both modes provide: PII redaction, cryptographic audit, cost controls, and network restrictions. Native Linux adds kernel-level enforcement on top.

---

## Network Security & HTTPS Whitelist

### How Network Access Works

By default, **all external network access is BLOCKED** (secure-first design):

```yaml
network_access_allowed: false  # Default: network locked
```

This protects against:
- ✅ Unauthorized data exfiltration via HTTP agent
- ✅ Injection of malicious content from untrusted APIs
- ✅ Uncontrolled API costs

### LLM APIs Always Pass Through

**Important:** LLM API endpoints (OpenAI, Anthropic, Grok, Mistral, Gemini) **always have network access** regardless of lock status. This is by design — AKIOS is built for AI workflows and cannot function without LLM connectivity.

The `network_access_allowed` setting controls **only the HTTP agent**, not LLM APIs.

### Configuring HTTPS Whitelist

To allow the HTTP agent access to specific APIs, whitelist their domains:

**Option 1: In `config.yaml`**
```yaml
network_access_allowed: true
allowed_domains:
  - "api.salesforce.com"
  - "api.mycompany.com"
  - "data.example.org"
```

**Option 2: Via `.env` file**
```bash
AKIOS_NETWORK_ACCESS_ALLOWED=true
AKIOS_ALLOWED_DOMAINS="api.salesforce.com,api.mycompany.com,data.example.org"
```

**Subdomain Handling:**
Subdomains must be added explicitly — they are not automatically allowed:

```yaml
allowed_domains:
  - "api.salesforce.com"         # Allows api.salesforce.com only
  - "analytics.salesforce.com"   # Must add separately
  - "*.example.com"              # Wildcard NOT supported
```

### Request Flow Diagram

```
Workflow → HTTP Agent Request
              ↓
     Is target an LLM API?
     ↙                    ↘
   YES                    NO
   ↓                      ↓
ALLOWED              Check whitelist
(no check)            ↓
                 In allowed_domains?
                 ↙              ↘
               YES              NO
               ↓                ↓
           ALLOWED          BLOCKED
                            ❌ 403 error
```

### Security: What's Protected

| Threat | Protection | Status |
|--------|-----------|--------|
| Unauthorized API calls | Whitelist enforcement | ✅ Blocked by default |
| Data exfiltration to 3rd-party | Domain whitelist | ✅ Requires explicit approval |
| LLM API unavailability | Bypass whitelist check | ✅ Always allowed |
| Subdomain takeover attacks | Explicit per-subdomain | ✅ No wildcards |

---

```bash
# Security dashboard
akios status --security

# JSON output for automation
akios status --security --json

# Full diagnostics
akios doctor

# Cage posture
akios cage status
```

The dashboard shows:
- Security level (Full kernel-hard vs Strong policy-based)
- PII protection status (input and output redaction)
- Network access (allowed/blocked)
- Audit logging and chain integrity
- Cost controls and budget remaining
- Compliance indicators

---

## Contact

Security reports: **security@akioud.ai**  
General questions: **hello@akios.ai**