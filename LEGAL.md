# AKIOS Legal Information & Disclaimers
**Document Version:** 1.6.0  
**Date:** 2026-03-14  

---

## ⚖️ Important Legal Notice

**AKIOS is open-source software provided free of charge.**

**Relationship to the GPL-3.0-only license:** This notice is informational. The GNU GPL-3.0-only license is the governing license for the AKIOS software. Nothing in this document adds restrictions beyond the GPL-3.0-only; in the event of any conflict, the GPL-3.0-only controls.

This document contains important legal information about your rights and responsibilities when using AKIOS. We recommend you read it carefully.

---

## 📄 License & Copyright

**Copyright © 2025 AKIOUD AI, SAS**

AKIOS is free software licensed under the **GNU General Public License version 3 only (GPL-3.0-only)**.

You may:
- ✅ Use AKIOS for any purpose
- ✅ Modify the source code
- ✅ Distribute copies (modified or unmodified)
- ✅ Share improvements with the community

You must:
- 📋 Include the GPL-3.0-only license with any distribution
- 📋 Make source code available when distributing binaries
- 📋 Preserve copyright notices

**Full license text**: [GNU GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)

---

## 🚨 Critical Disclaimers

### No Warranties
**AKIOS IS PROVIDED "AS IS" WITH NO WARRANTIES OF ANY KIND.**

We make **no guarantees** about:
- Security effectiveness (no system is 100% secure)
- AI output accuracy or safety
- Prevention of all possible harms
- Compliance with laws or regulations
- Suitability for any specific purpose

### User Responsibility
**YOU ARE SOLELY RESPONSIBLE FOR HOW YOU USE AKIOS.**

This includes responsibility for:
- 🔒 Securing your environment and data
- ✅ Validating AI outputs before use
- 📊 Monitoring costs and resource usage
- ⚖️ Ensuring legal compliance in your jurisdiction
- 🛡️ Protecting sensitive information
- 🚫 Preventing misuse or harmful applications

### AI-Specific Risks
**AI systems can produce harmful, biased, or incorrect outputs.**

AKIOS cannot prevent all risks associated with AI, including:
- 🤖 Generation of harmful or inappropriate content
- 📈 Unpredictable AI behavior
- 🎯 Biased or discriminatory outputs
- 🔍 Privacy violations
- 💰 Unexpected costs or resource consumption
- ⚠️ Security vulnerabilities

**You must implement additional safeguards appropriate for your use case.**

---

## 🛡️ Limitation of Liability

**TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, AKIOUD AI, SAS, ITS CONTRIBUTORS, OR ANY OTHER PARTY INVOLVED IN CREATING, PRODUCING, OR DELIVERING AKIOS SHALL NOT BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY ARISING FROM OR RELATED TO YOUR USE OF AKIOS.**

This **complete exclusion of liability** applies to all damages including, but not limited to:
- **Direct damages**: Financial losses, data loss, system failures
- **Indirect damages**: Lost profits, business interruption, reputational harm
- **Consequential damages**: Legal penalties, regulatory fines, third-party claims
- **Special damages**: Personal injury, property damage, environmental harm
- **Punitive damages**: Any punitive or exemplary awards

**This exclusion applies even if:**
- We were advised of the possibility of such damages
- Such damages were foreseeable
- Our negligence or fault caused the harm
- Any limited remedy fails its essential purpose

**Carve-outs (where required by law):** This limitation does not exclude or limit liability where such exclusion is prohibited by applicable law, including for death or personal injury caused by negligence, gross negligence or willful misconduct, and any non-waivable statutory rights (e.g., certain consumer or product liability protections).

---

## 🔍 Compliance & Regulatory Notice

**AKIOS does not guarantee compliance with any laws, regulations, or standards.**

Users are responsible for:
- 🇪🇺 EU AI Act compliance
- 🇫🇷 French data protection laws (CNIL, HDS)
- 🏛️ Industry-specific regulations
- 🌍 International export controls
- 📋 Organizational security standards

**For regulated environments requiring certifications or guarantees, consult legal experts and consider commercial alternatives.**

---

## 🌐 Governing Law & Jurisdiction

*Note: This section applies to disputes about the website, services, or trademarks, not to rights granted under the GPL-3.0-only license.*

Operational disputes (non-GPL matters) are governed by **French law**.

Any such disputes shall be resolved in the courts of **Paris, France**.

---

## 📞 Legal Entity Information

**AKIOUD AI, SAS**  
8b rue Abel  
75012 Paris, France  

**Contact**: hello@akios.ai  

---

## ⚠️ Final Warnings

### Open Source Nature
AKIOS is community-developed open-source software. **We cannot control how others modify or use it.**

### No Professional Services
This software does not include professional services, support, or consulting.

### Regular Updates
Security and functionality can change. **Keep your installation updated and monitor for security advisories.**

### Export Controls
AKIOS may be subject to French and EU export control regulations. Users must comply with applicable laws.

---

---

## 📋 Responsibility Acceptance Guidelines

**For safe production use, we recommend you understand and acknowledge the following:**

### Infrastructure Responsibility

**AKIOS is NOT responsible for:**
- ❌ Infrastructure performance or availability (AWS, Kubernetes, your servers)
- ❌ Network latency, connectivity, or data transfer costs
- ❌ Cloud provider billing, charges, or cost overruns
- ❌ Instance configuration, sizing, or resource allocation
- ❌ Operating system security or updates
- ❌ Third-party service integrations or dependencies

**YOU are responsible for:**
- ✅ Choosing appropriate infrastructure for your workload
- ✅ Monitoring and controlling cloud provider costs
- ✅ Securing your infrastructure (firewalls, security groups, network policies)
- ✅ Maintaining your operating system and dependencies
- ✅ Validating performance meets your requirements on YOUR infrastructure
- ✅ Testing on your chosen instance type before claiming performance parity

### Data Security Responsibility

**AKIOS provides algorithmic controls:**
- ✅ Sandbox isolation (seccomp-bpf + cgroups on Linux)
- ✅ PII redaction (50+ pattern detection)
- ✅ Audit trails (cryptographic Merkle proofs)
- ✅ Budget enforcement (LLM API kill-switches)

**YOU must provide:**
- ✅ Infrastructure security (credentials, access controls, encryption)
- ✅ Data sensitivity classification (know what data you're processing)
- ✅ Compliance enforcement (your laws, your industry rules)
- ✅ Secret management (API keys, passwords, tokens)
- ✅ Monitoring and alerting (costs, suspicious activity, data access)

### Performance Validation Responsibility

**AKIOS validates and documents:**
- ✅ Security pipeline overhead on AWS EC2 t4g.micro (0.47 ms full pipeline)
- ✅ Docker performance on all platforms (sub-2s startup, functional security)
- ✅ Security overhead analysis (policy-based vs kernel-hard)

**YOU must validate:**
- ✅ Performance on YOUR instance type and region
- ✅ Performance meets YOUR application requirements
- ✅ Cost-benefit trade-offs for your use case
- ✅ Compatibility with your existing systems

See [EC2 Performance Testing Guide](./docs/ec2-performance-testing.md) for validation procedures.

### Compliance Responsibility

**AKIOS cannot guarantee compliance.**

YOU are responsible for:
- ✅ Legal compliance in YOUR jurisdiction
- ✅ EU AI Act compliance (if applicable)
- ✅ Data protection laws (GDPR, HIPAA, etc.)
- ✅ Industry regulations (finance, healthcare, etc.)
- ✅ Contractual obligations (customer agreements, SLAs)
- ✅ Export control compliance (ITAR, EAR, etc.)

**For regulated environments:**
- 🚫 Do NOT assume AKIOS satisfies compliance requirements
- 🎓 Consult legal experts and compliance specialists
- 🔍 Conduct thorough risk assessments
- 📋 Document your compliance justifications
- ✅ Consider professional support solutions

---

## ✅ Recommended Pre-Use Checklist

**We recommend you acknowledge the following before production deployment:**

1. **I understand the security capabilities and limitations**
   - AKIOS provides strong security through sandboxing and PII redaction
   - AKIOS does NOT provide absolute security or guarantee protection from all attacks
   - I am responsible for additional security measures appropriate to my use case

2. **I understand the performance metrics**
   - AKIOS achieves documented baselines on t4g.micro EC2 (0.47 ms security pipeline) and Docker
   - Performance on other infrastructure may differ
   - I will validate performance on MY infrastructure before production use

3. **I understand the infrastructure responsibility**
   - AKIOS is responsible only for the sandbox and algorithms
   - AWS/cloud costs, security groups, networking, storage are MY responsibility
   - AKIOS will not reimburse unexpected infrastructure charges

4. **I understand the compliance responsibility**
   - AKIOS does not guarantee legal or regulatory compliance
   - I am responsible for compliance in MY jurisdiction
   - I will consult experts for regulated or high-risk deployments

5. **I understand the liability limits**
   - AKIOS is provided "as-is" with no warranties
   - AKIOS is not liable for damages from using AKIOS
   - Use of AKIOS is entirely at your own risk

**We recommend confirming these understandings by:**
- [ ] Reading this entire LEGAL.md document
- [ ] Reading the [EC2 Performance Testing Guide](./docs/ec2-performance-testing.md)
- [ ] Testing AKIOS on my infrastructure before production use
- [ ] Monitoring costs and security of my deployment
- [ ] Consulting experts for compliance-sensitive use cases

---


## 📦 Source Code Availability for Distributions

If you distribute AKIOS in binary form (including Docker images), you must provide the complete corresponding source code (or a written offer) in accordance with GPL-3.0-only §6 (GPLv3 §6). Publish the source alongside the binaries or provide a documented retrieval method.

## 📚 Third-Party Components

AKIOS includes third-party software; see `THIRD_PARTY_LICENSES.md` for notices and license terms. Comply with those licenses when redistributing.

---

*AKIOS — Where AI meets unbreakable security*  
*Use responsibly. Your safety and compliance are your responsibility.* 🛡️
