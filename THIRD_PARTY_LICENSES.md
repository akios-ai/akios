# AKIOS v1.0.0 – Third-Party Licenses
**Document Version: 1.1**  
**Date: December 31, 2024**  

This document lists **all third-party software components** used in AKIOS v1.0.0 Open Runtime and their licenses.

AKIOS uses a comprehensive set of dependencies for core functionality, security, LLM integration, document processing, API services, and development tools. All dependencies are compatible with GPL-3.0-only licensing.

## Core Runtime Dependencies

| Dependency          | Version         | License              | Purpose                                      | Website / Repo                                      |
|---------------------|-----------------|----------------------|----------------------------------------------|-----------------------------------------------------|
| **pydantic**        | >=2.0.0         | MIT                  | Type-safe data validation and settings       | https://github.com/pydantic/pydantic               |
| **pydantic-settings**| >=2.0.0         | MIT                  | Configuration management with pydantic       | https://github.com/pydantic/pydantic-settings      |
| **click**           | >=8.0.0         | BSD-3-Clause         | Command-line interface framework             | https://github.com/pallets/click                   |
| **pyyaml**          | >=6.0           | MIT                  | YAML parsing and serialization               | https://github.com/yaml/pyyaml                     |
| **jsonschema**      | >=4.21.0        | MIT                  | JSON schema validation                       | https://github.com/python-jsonschema/jsonschema   |
| **httpx**           | >=0.25.0        | BSD                  | HTTP client for API integrations             | https://github.com/encode/httpx                    |
| **requests**        | >=2.25.0        | Apache-2.0           | HTTP library for web requests                | https://github.com/psf/requests                    |
| **cryptography**    | >=42.0.0        | Apache-2.0           | Cryptographic operations and security        | https://github.com/pyca/cryptography               |
| **psutil**          | >=5.9.0         | BSD                  | System and process utilities                 | https://github.com/giampaolo/psutil                |
| **openai**          | >=1.0.0         | MIT                  | OpenAI API client                            | https://github.com/openai/openai-python            |
| **anthropic**       | >=0.30.0        | MIT                  | Anthropic Claude API client                  | https://github.com/anthropics/anthropic-sdk-python |
| **google-generativeai**| >=0.8.0       | Apache-2.0           | Google Gemini API client                     | https://github.com/google/generative-ai-python    |
| **tiktoken**        | >=0.5.0         | MIT                  | Token counting for LLM providers             | https://github.com/openai/tiktoken                 |
| **protobuf**        | >=5.29.5        | BSD-3-Clause         | Protocol buffer serialization                | https://github.com/protocolbuffers/protobuf       |
| **PyPDF2**          | >=3.0.0         | BSD                  | PDF document processing                      | https://github.com/py-pdf/pypdf                    |
| **pdfminer.six**    | >=20231228      | MIT                  | PDF text extraction                          | https://github.com/pdfminer/pdfminer.six          |
| **python-docx**     | >=1.1.0         | MIT                  | Microsoft Word document processing           | https://github.com/python-openxml/python-docx     |

## Optional Runtime Dependencies

| Dependency          | Version         | License              | Purpose                                      | Website / Repo                                      | Group |
|---------------------|-----------------|----------------------|----------------------------------------------|-----------------------------------------------------|-------|
| **fastapi**         | >=0.104.0       | MIT                  | REST API framework                           | https://github.com/tiangolo/fastapi                | api |
| **uvicorn**         | >=0.24.0        | BSD                  | ASGI server for FastAPI                      | https://github.com/encode/uvicorn                  | api |
| **prometheus-client**| >=0.17.0        | Apache-2.0           | Prometheus metrics collection                | https://github.com/prometheus/client_python        | monitoring |
| **seccomp**         | >=1.0.0         | LGPL-2.1            | Linux syscall filtering                      | https://github.com/seccomp/libseccomp              | seccomp |
| **backoff**         | >=2.2.0         | MIT                  | Retry logic with exponential backoff         | https://github.com/litl/backoff                    | extended |
| **aiohttp**         | >=3.9.0         | Apache-2.0           | Asynchronous HTTP client                     | https://github.com/aio-libs/aiohttp                | extended |

## Development & Testing Dependencies

| Dependency          | Version         | License              | Purpose                                      | Website / Repo                                      |
|---------------------|-----------------|----------------------|----------------------------------------------|-----------------------------------------------------|
| **pytest**          | >=7.0.0         | MIT                  | Testing framework                            | https://github.com/pytest-dev/pytest               |
| **pytest-cov**      | >=4.0.0         | MIT                  | Test coverage reporting                      | https://github.com/pytest-dev/pytest-cov           |
| **black**           | >=23.0.0        | MIT                  | Code formatting                              | https://github.com/psf/black                       |
| **isort**           | >=5.12.0        | MIT                  | Import sorting                               | https://github.com/PyCQA/isort                     |
| **mypy**            | >=1.0.0         | MIT                  | Static type checking                         | https://github.com/python/mypy                     |
| **ruff**            | >=0.1.0         | MIT                  | Fast Python linter and formatter             | https://github.com/astral-sh/ruff                  |
| **pre-commit**      | >=3.0.0         | MIT                  | Git hooks framework                          | https://github.com/pre-commit/pre-commit           |
| **flake8**          | >=5.0.0         | MIT                  | Style guide enforcement                      | https://github.com/pycqa/flake8                    |
| **sphinx**          | >=5.0.0         | BSD-2-Clause         | Documentation generation                     | https://github.com/sphinx-doc/sphinx               |
| **sphinx-rtd-theme**| >=1.2.0         | MIT                  | Read the Docs theme for Sphinx               | https://github.com/readthedocs/sphinx_rtd_theme    |
| **tox**             | >=4.0.0         | MIT                  | Testing automation                           | https://github.com/tox-dev/tox                     |
| **types-PyYAML**    | >=6.0.0         | Apache-2.0           | Type stubs for PyYAML                        | https://github.com/python/typeshed                 |
| **types-requests**  | >=2.0.0         | Apache-2.0           | Type stubs for requests                      | https://github.com/python/typeshed                 |

## Build System Dependencies

| Dependency          | Version         | License              | Purpose                                      | Website / Repo                                      |
|---------------------|-----------------|----------------------|----------------------------------------------|-----------------------------------------------------|
| **setuptools**      | >=65.0.0        | MIT                  | Python package building                      | https://github.com/pypa/setuptools                 |
| **wheel**           | >=0.37.0        | MIT                  | Python wheel packaging                       | https://github.com/pypa/wheel                      |
| **build**           | >=1.0.0         | MIT                  | Python package building frontend             | https://github.com/pypa/build                      |
| **PyInstaller**     | >=5.0.0         | GPL-2.0             | Standalone executable creation               | https://github.com/pyinstaller/pyinstaller         |

## License Compatibility

All dependencies are **compatible with GPL-3.0-only**:
- **MIT**: Fully compatible (pydantic, pyyaml, openai, anthropic, tiktoken, fastapi, pdfminer.six, python-docx, pytest, black, isort, mypy, ruff, pre-commit, flake8, sphinx-rtd-theme, tox, setuptools, wheel, build)
- **Apache-2.0**: Compatible (cryptography, requests, google-generativeai, prometheus-client, aiohttp, types-PyYAML, types-requests)
- **BSD-3-Clause**: Compatible (click, protobuf)
- **BSD**: Compatible (httpx, psutil, uvicorn, PyPDF2)
- **BSD-2-Clause**: Compatible (sphinx)
- **GPL-2.0**: Compatible (PyInstaller - build tool only)
- **LGPL-2.1**: Compatible (seccomp - optional security enhancement)

No GPL-incompatible licenses are used.

## Security & Maintenance

- All dependencies are **actively maintained** with regular security updates
- **Automated security scanning** via pip-audit in CI/CD pipeline
- **Vulnerability patching** within 30 days for critical issues
- **Dependency updates** reviewed quarterly for security and compatibility

## Attribution & Notices

When distributing AKIOS, include license notices for all third-party components. Full license texts are available at the linked repositories.

**Example attribution notice** (for inclusion in distributed packages):
```
AKIOS includes the following third-party software:

Core Dependencies:
- pydantic (MIT): https://github.com/pydantic/pydantic/blob/main/LICENSE
- PyYAML (MIT): https://github.com/yaml/pyyaml/blob/main/LICENSE
- cryptography (Apache-2.0): https://github.com/pyca/cryptography/blob/main/LICENSE
- httpx (BSD): https://github.com/encode/httpx/blob/main/LICENSE
- psutil (BSD): https://github.com/giampaolo/psutil/blob/main/LICENSE
- openai (MIT): https://github.com/openai/openai-python/blob/main/LICENSE
- anthropic (MIT): https://github.com/anthropics/anthropic-sdk-python/blob/main/LICENSE
- google-generativeai (Apache-2.0): https://github.com/google/generative-ai-python/blob/main/LICENSE

[Additional dependencies listed in THIRD_PARTY_LICENSES.md]

Full license texts and complete dependency list available in THIRD_PARTY_LICENSES.md
```

## Summary

AKIOS v1.0.0 uses **40+ third-party dependencies** providing comprehensive functionality for secure AI agent execution, including LLM integration, document processing, API services, security, and development tools. All dependencies are well-maintained, GPL-3.0-compatible, and selected for their security, performance, and reliability.


