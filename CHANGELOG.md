# Changelog
**Document Version:** 1.0.3
**Date:** 2026-01-28

All notable changes to AKIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2026-01-28

### Fixed
- **🐛 Critical Bug Fixes**: Resolved issues in release process and asset handling
- **📦 Distribution Fixes**: Corrected file inclusion in release bundles
- **🔧 Build Process**: Improved prepare script to include assets directory
- **📋 Documentation**: Updated version references across all files

### Security
- **🔒 Dependency Updates**: Security patches for protobuf and other dependencies
- **🛡️ Build Security**: Enhanced validation of release artifacts

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
