# AKIOS v1.0.3 Release Notes
**Document Version:** 1.0.3
**Date:** 2026-01-28

### 🔧 AKIOS v1.0.3: Critical Fixes & Distribution Improvements

AKIOS v1.0.3 delivers **critical bug fixes** and **distribution improvements** to ensure reliable deployment across all platforms.

### ✨ Key Highlights

- **🐛 Critical Bug Fixes**: Resolved issues in release process and asset handling
- **📦 Distribution Fixes**: Corrected file inclusion in release bundles
- **🔧 Build Process**: Improved prepare script to include assets directory
- **📋 Documentation**: Updated version references across all files
- **🔒 Security**: Dependency updates and enhanced build security

### 📦 Distribution Options

AKIOS v1.0.3 is available through multiple secure distribution channels:

#### Docker Container
```bash
docker pull akiosai/akios:v1.0.3
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.3 init my-project
```

#### Pip Package
```bash
pip install akios==1.0.3
akios --help
```

#### Standalone Binaries
Download from GitHub releases with SHA256 verification.

### 🔒 Security Features

- **Kernel-level Isolation**: cgroups + seccomp sandbox + resource quotas
- **Real-time PII Redaction**: >95% accuracy, <50ms response time
- **Tamper-evident Audit**: Merkle tree cryptographic verification
- **Cost & Loop Protection**: Hard termination on budget exceedance

### 📋 What's Fixed

- **Asset Inclusion**: Logo and assets now properly included in releases
- **Build Process**: Prepare script fixed to include assets directory
- **Version Consistency**: All version references updated to v1.0.3
- **Documentation**: Changelog and release notes updated

### 🚀 Migration from v1.0.0/v1.0.1/v1.0.2

**Important**: Previous versions (v1.0.0, v1.0.1, v1.0.2) have been yanked due to missing critical files. Please upgrade to v1.0.3 immediately.

```bash
# Upgrade from pip
pip install --upgrade akios==1.0.3

# Or fresh install
pip install akios==1.0.3
```

### 📞 Support

- **Documentation**: https://akios.ai/docs
- **Issues**: https://github.com/akios-ai/akios/issues
- **Security**: security@akios.ai

---

**AKIOS v1.0.3** - The strongest open-source security foundation for AI agents.
