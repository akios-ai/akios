# 📚 AKIOS v1.0.15 - Documentation
**Document Version:** 1.0.13  
**Date:** 2026-02-22  

**Complete user guide for AKIOS - Secure AI Workflow Execution**

Welcome to the official AKIOS documentation! This section contains all the guides you need to get started, configure, deploy, and troubleshoot AKIOS.

## 🚀 Getting Started

**New to AKIOS? Start here!**

- **[quickstart.md](quickstart.md)** - Complete setup and usage guide
  - Installation options (Pip, Docker)
  - API key configuration
  - Running your first AI workflow
  - Security features and best practices

## 📖 User Guides

### Getting Started & Configuration
- **[quickstart.md](quickstart.md)** - Complete setup and usage guide
- **[configuration.md](configuration.md)** - All configuration options documented
- **[cli-reference.md](cli-reference.md)** - Complete command-line interface guide

### Environment & Accessibility
- **[detection-system.md](detection-system.md)** - How AKIOS auto-detects your environment (Docker, Kubernetes, CI/CD, TTY, Unicode) 🆕
- **[accessibility-guide.md](accessibility-guide.md)** - Symbol modes, colorblind support, Unicode, screen readers 🆕
- **[theme-customization.md](theme-customization.md)** - Create and customize color themes 🆕
- **[examples.md](examples.md)** - Real-world usage examples and tutorials 🆕

### Security & Deployment
- **[security.md](security.md)** - Security features and compliance information
- **[deployment.md](deployment.md)** - Production deployment and scaling best practices
- **[ec2-performance-testing.md](ec2-performance-testing.md)** - Complete AWS EC2 testing guide with performance validation, instance recommendations, and cost estimation
- **[troubleshooting.md](troubleshooting.md)** - Common issues and solutions
- **[migration-guide.md](migration-guide.md)** - Migrate to hybrid distribution

### For Developers
- **[workflow-schema.md](workflow-schema.md)** - YAML workflow schema and syntax reference
- **[api-reference.md](api-reference.md)** - Developer API reference
- **[best-practices.md](best-practices.md)** - AKIOS development and deployment best practices

### For Organizations
- **[Compliance Reporting](deployment.md#compliance--audit-trails)** - Cryptographic audit trails and compliance logging
- **[Integration Guides](integration/)** - API integration and document processing examples
## 📋 Templates & Examples

AKIOS comes with production-ready workflow templates:

- `hello-workflow.yml` - Basic AI interaction with security validation
- `document_ingestion.yml` - Document processing with PII redaction
- `batch_processing.yml` - Multi-file AI analysis with cost controls
- `file_analysis.yml` - Security-focused file analysis and threat detection

All templates produce **real AI output** from live LLM providers with full audit trails. The `batch_processing.yml` template demonstrates scalable local processing.

## 🔗 Quick Links

| What you want to do | Where to go |
|---------------------|-------------|
| **First time setup** | [quickstart.md](quickstart.md) |
| **Choose installation method** | [quickstart.md](quickstart.md#choose-your-installation-method) |
| **Understand environment detection** | **[detection-system.md](detection-system.md)** 🆕 |
| **Accessibility & colorblind support** | **[accessibility-guide.md](accessibility-guide.md)** 🆕 |
| **Create custom color themes** | **[theme-customization.md](theme-customization.md)** 🆕 |
| **See real-world examples** | **[examples.md](examples.md)** 🆕 |
| **Migrate to v1.0** | [migration-guide.md](migration-guide.md) |
| **Configure settings** | [configuration.md](configuration.md) |
| **Run commands** | [cli-reference.md](cli-reference.md) |
| **Test on AWS EC2** | [ec2-performance-testing.md](ec2-performance-testing.md) |
| **Workflow syntax** | [workflow-schema.md](workflow-schema.md) |
| **Process documents** | [integration/document-processing.md](integration/document-processing.md) |
| **Integrate APIs** | [integration/api-integration.md](integration/api-integration.md) |
| **Developer API** | [api-reference.md](api-reference.md) |
| **Best practices** | [best-practices.md](best-practices.md) |
| **Deploy to production** | [deployment.md](deployment.md) |
| **Fix problems** | [troubleshooting.md](troubleshooting.md) |
| **Security details** | [security.md](security.md) |

## 🌐 Ecosystem

AKIOS is part of the [AKIOUD AI](https://github.com/akios-ai) ecosystem:

| Project | License | Description |
|---------|---------|-------------|
| **[AKIOS](https://github.com/akios-ai/akios)** | GPL-3.0-only | Production runtime for secure AI agents — kernel sandbox, workflow engine, 4 agents, CLI, compliance reports |
| **[EnforceCore](https://github.com/akios-ai/EnforceCore)** | Apache-2.0 | General-purpose enforcement library — policy engine, PII redaction, audit trails, framework integrations (LangChain, CrewAI, AutoGen) |

EnforceCore is the enforcement foundation; AKIOS is the complete production runtime built on top of it.

## 📞 Support & Community

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and community help
- **Documentation** - Complete guides and troubleshooting

## 📜 Legal & Compliance

- **License**: GPL-3.0-only
- **Security**: Cryptographic audit trails with PII protection
- **Compliance**: Designed for GDPR and privacy regulation compliance

---

**Happy building with secure AI!** 🚀🤖🛡️

*AKIOS v1.0.15 - Where AI meets unbreakable security*
