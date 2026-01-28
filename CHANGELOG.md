# Changelog
**Document Version:** 1.0  
**Date:** 2026-01-25  

All notable changes to AKIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-24

### Added
- **🚀 Hybrid Distribution**: Revolutionary multi-deployment options
  - **Standalone Binaries**: Zero-dependency executables for instant deployment
    - Linux x64/ARM64, macOS Universal, Windows x64 binaries
    - Air-gapped capable, no Python/Docker required
    - SHA256 cryptographic verification for all downloads
  - **Pip Packages**: Maximum security with kernel-hard features on Linux
  - **Docker Containers**: Cross-platform consistency with policy-based security
- **🔒 Enhanced Security Architecture**: Defense-in-depth across all platforms
  - **Native Linux**: seccomp-bpf + cgroups v2 kernel-hard isolation
  - **Docker**: Policy-based container security (allowlisting, PII redaction, audit)
  - **Binaries**: Embedded security with platform-appropriate isolation
  - **Unified PII Protection**: 50+ pattern detection, real-time redaction
  - **Cryptographic Audit Trails**: Merkle tree verification, tamper-evident logs
- **⚡ Zero-Setup Deployment**: Download-and-run experience
  - Pre-built binaries with all dependencies included
  - Cross-platform compatibility (Linux/macOS/Windows)
  - Instant startup, no configuration required
- **📊 Production-Ready Features**: Complete AI workflow security
  - Real AI provider integration (OpenAI, Anthropic, Grok, Mistral, Gemini)
  - Cost kill-switches ($1.00 default budget limits)
  - Resource controls (CPU, memory, file size limits)
  - Comprehensive error handling and recovery
- **🎯 Perfect User Experience**: 10/10 UX across all interactions
  - **Terminal Width Awareness**: Templates list adapts to screen width
  - **File Discovery Commands**: `akios files` shows available input/output files
  - **Enhanced Template Guidance**: Clear file availability and usage tips
  - **Improved Progress Feedback**: Better status indicators and next steps
  - **10/10 Setup Wizard**: Revolutionary user onboarding experience
    - **Mock-First Approach**: 80% of users can test instantly without API keys
    - **Skip Option**: Visible from start, no obligation to configure
    - **Dynamic Pricing Examples**: Budget explanations adapt to selected provider
    - **Real-Time Validation**: Spinner feedback during API key testing
    - **Forgiving UX**: Backup options, cancel anytime, clear defaults
    - **Professional Polish**: Bold headers, inline previews, actionable next steps
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
- **Installation Experience**: From single Docker method to hybrid distribution choice
- **Security Communication**: Clear platform capability explanations
- **Documentation Structure**: Comprehensive user guides and troubleshooting
- **Release Process**: Automated pipeline with quality assurance

### Security
- **Military-grade sandboxing** with platform-appropriate isolation
- **Automatic PII redaction** across all deployment methods
- **Cryptographic audit trails** with integrity verification
- **Cost and resource controls** preventing abuse
- **Tamper-evident logging** for regulatory compliance
- **SHA256 verification** for all binary downloads

### Technical
- **Cross-platform binary builds** using PyInstaller unified specs
- **Embedded dependencies** eliminating external requirements
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
- Security reports: hello@akios.ai (private only)
- See README.md for current scope & limits

*For the complete history, see the [Git repository](https://github.com/akios-ai/akios/commits/main).*

This changelog is **locked** for V1.0.  
Future entries will reflect only scope-aligned changes.
