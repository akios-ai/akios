# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
CLI init command - akios init

Create basic project structure (config, example template).
"""

import os
from pathlib import Path
import argparse
import logging

logger = logging.getLogger(__name__)

from ...config import get_settings
from ..helpers import CLIError, output_result
from ...core.ui.commands import (
    SETUP_COMMAND, HELLO_WORKFLOW_COMMAND, DOCUMENT_INGESTION_COMMAND,
    BATCH_PROCESSING_COMMAND, FILE_ANALYSIS_COMMAND, STATUS_COMMAND, HELP_COMMAND,
    get_command_prefix, suggest_command
)


def register_init_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the init command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "init",
        help="Create project structure with templates (optionally in subdirectory)"
    )

    parser.add_argument(
        "project_name",
        nargs="?",
        default=None,
        help="Project name (optional - creates subdirectory, defaults to current directory)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress welcome message and success output"
    )

    parser.add_argument(
        "--wizard",
        action="store_true",
        help="Run the setup wizard after project initialization"
    )

    parser.set_defaults(func=run_init_command)


def run_init_command(args: argparse.Namespace) -> int:
    """
    Execute the init command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        result = create_project_structure(project_name=args.project_name, force=args.force)
        output_result(result, json_mode=args.json, success_message="Project initialized successfully")

        # Run setup wizard if requested
        if getattr(args, 'wizard', False):
            print("\n🔧 Running setup wizard...")
            try:
                from ...core.config.first_run import SetupWizard
                from pathlib import Path
                import os

                # Find the project directory
                project_dir = Path.cwd()
                if args.project_name:
                    project_dir = project_dir / args.project_name

                wizard = SetupWizard(project_dir)
                if wizard.run_wizard():
                    print("✅ Setup wizard completed successfully!")
                else:
                    print("❌ Setup wizard was cancelled or failed.")
                    return 1
            except Exception as e:
                print(f"❌ Setup wizard failed: {e}")
                return 1

        # Add welcoming post-init message for better UX (unless --quiet or --json)
        if not getattr(args, 'quiet', False) and not getattr(args, 'json', False):
            print(f"""
🎉 Welcome to AKIOS! Your secure AI workspace is ready.

🚀 Quick Start:
   {SETUP_COMMAND}    # Configure API (1 min)
   {HELLO_WORKFLOW_COMMAND}  # First AI run

📖 Next: {SETUP_COMMAND}
""")

        return 0

    except CLIError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return e.exit_code
    except Exception as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=args.json)


def create_project_structure(project_name: str = None, force: bool = False) -> dict:
    """
    Create minimal project structure.

    Args:
        project_name: Name of project directory (optional)
        force: If True, overwrite existing files

    Returns:
        Dict with creation results

    Raises:
        CLIError: If creation fails
    """
    # Determine base path
    base_path = Path(project_name) if project_name else Path(".")

    # Check if project already exists
    config_path = base_path / "config.yaml"
    templates_dir = base_path / "templates"

    # Check for actual user-created project
    # A real project has config.yaml (templates are installed by package, not user-created)
    config_exists = config_path.exists()

    project_exists = config_exists

    if project_exists and not force:
        raise CLIError(
            "Project already exists. Use --force to overwrite.",
            exit_code=1
        )

    created_files = []
    skipped_files = []

    # Create directories
    dirs_to_create = ["templates", "data/input", "data/output", "audit"]
    for dir_path in dirs_to_create:
        dir_obj = base_path / dir_path
        dir_obj.mkdir(parents=True, exist_ok=True)
        created_files.append(str(dir_obj))

    # Create config.yaml
    if not config_path.exists() or force:
        config_content = create_default_config()
        config_path.write_text(config_content)
        created_files.append(str(config_path))
    else:
        skipped_files.append(str(config_path))

    # Create project launcher script for navigation consistency
    # Copy from Docker image (single source of truth) to avoid version drift
    launcher_script = base_path / "akios"
    if not launcher_script.exists() or force:
        # Copy wrapper from Docker image location (/app/akios)
        docker_wrapper_path = Path("/app/akios")
        if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
            logger.debug(f"Checking for wrapper at {docker_wrapper_path}")
        if docker_wrapper_path.exists():
            if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
                logger.debug(f"Wrapper exists, copying to {launcher_script}")
            try:
                import shutil
                shutil.copy2(docker_wrapper_path, launcher_script)
                launcher_script.chmod(0o755)
                created_files.append(str(launcher_script))
                if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
                    logger.debug("Wrapper copied successfully")
            except (OSError, IOError) as e:
                print(f"Warning: Could not copy launcher script from Docker image: {e}")
        else:
            if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
                logger.debug(f"Wrapper not found at {docker_wrapper_path}")
            # Fallback: create a basic launcher
            launcher_content = '''#!/bin/bash
set -e
IMAGE="akiosai/akios:v1.0.3"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to run AKIOS from this project."
  exit 1
fi

exec docker run --rm -v "$(pwd):/app" -w /app "$IMAGE" "$@"
'''
            launcher_script.write_text(launcher_content)
            launcher_script.chmod(0o755)
            created_files.append(str(launcher_script))
    else:
        skipped_files.append(str(launcher_script))

    # Create example workflows (copy from source templates)
    import shutil

    # Copy templates from package data
    try:
        import akios
        import pkg_resources

        # Get templates from package data
        try:
            template_files = pkg_resources.resource_listdir('akios', 'templates')
        except:
            template_files = []

        if template_files:
            # Copy templates from package data
            for filename in template_files:
                if filename.endswith(('.yml', '.yaml', '.md')):
                    dest_file = base_path / "templates" / filename
                    if not dest_file.exists() or force:
                        try:
                            content = pkg_resources.resource_string('akios', f'templates/{filename}')
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            with open(dest_file, 'wb') as f:
                                f.write(content)
                            created_files.append(str(dest_file))
                        except Exception as e:
                            print(f"Warning: Could not copy template {filename}: {e}", file=__import__("sys").stderr)
                            print(f"Info: Will create basic template instead for {filename}", file=__import__("sys").stderr)
        else:
            # Fallback: create basic templates inline
            create_basic_templates(base_path, created_files, force)
    except Exception as e:
        # If copying fails, create basic templates inline
        print(f"Warning: Could not copy built-in templates ({e})", file=__import__("sys").stderr)
        print("Info: Creating basic example templates instead. You can customize them as needed.", file=__import__("sys").stderr)
        create_basic_templates(base_path, created_files, force)

    # Create .gitignore if it doesn't exist
    gitignore_path = base_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = create_gitignore()
        gitignore_path.write_text(gitignore_content)
        created_files.append(str(gitignore_path))

    # Create sample .env file
    akios_env_path = base_path / ".env"
    if not akios_env_path.exists():
        akios_env_content = create_akios_env()
        akios_env_path.write_text(akios_env_content)
        created_files.append(str(akios_env_path))

    # Create .env.example template
    env_example_path = base_path / ".env.example"
    if not env_example_path.exists():
        env_example_content = create_env_example()
        env_example_path.write_text(env_example_content)
        created_files.append(str(env_example_path))

    # Create README.md with project documentation
    readme_path = base_path / "README.md"
    if not readme_path.exists():
        readme_content = create_readme()
        readme_path.write_text(readme_content)
        created_files.append(str(readme_path))

    # Create sample documents for testing document_ingestion template (supported formats)
    sample_formats = ['.txt', '.pdf', '.docx']
    for ext in sample_formats:
        sample_doc_path = base_path / "data" / "input" / f"document_example{ext}"
        if not sample_doc_path.exists():
            try:
                # Try to copy from package sample files first
                try:
                    from importlib import resources
                except ImportError:
                    import importlib_resources as resources

                sample_content = resources.files('akios.cli.data.samples.document_examples').joinpath(f'sample{ext}').read_bytes()
                sample_doc_path.write_bytes(sample_content)
                created_files.append(str(sample_doc_path))
            except Exception as e:
                # Fallback to generating content dynamically
                sample_doc_content = create_sample_document()
                sample_doc_path.write_text(sample_doc_content)
                created_files.append(str(sample_doc_path))

    # Create sample analysis target files for file_analysis template (supported formats)
    analysis_formats = ['.txt', '.pdf', '.docx']
    for ext in analysis_formats:
        analysis_target_path = base_path / "data" / "input" / f"analysis_target{ext}"
        if not analysis_target_path.exists():
            try:
                # Try to copy from package sample files first
                try:
                    from importlib import resources
                except ImportError:
                    import importlib_resources as resources

                analysis_content = resources.files('akios.cli.data.samples.analysis_targets').joinpath(f'sample{ext}').read_bytes()
                if ext == '.txt':
                    analysis_target_path.write_text(analysis_content.decode('utf-8'))
                else:
                    # For binary files (PDF, DOCX)
                    analysis_target_path.write_bytes(analysis_content)
                created_files.append(str(analysis_target_path))
            except Exception as e:
                # Fallback to generating content dynamically (only for .txt)
                if ext == '.txt':
                    analysis_content = create_sample_analysis_file()
                    analysis_target_path.write_text(analysis_content)
                    created_files.append(str(analysis_target_path))

    # Create sample batch input data for batch_processing template
    batch_dir = base_path / "data" / "input" / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample business documents
    sample_files = [
        ("customer_feedback.txt", "Customer feedback for Q4 2024:\n- Product quality excellent\n- Customer service responsive\n- Pricing competitive\n- Would recommend to colleagues"),
        ("sales_report.json", '{"quarter": "Q4", "revenue": 250000, "growth": "15%", "top_products": ["Widget A", "Widget B"]}'),
        ("employee_notes.md", "# Team Meeting Notes\n## Action Items\n- Complete project documentation\n- Schedule client review\n- Update security protocols\n## Decisions\n- Approved budget increase\n- New hire starting next month")
    ]
    
    for filename, content in sample_files:
        file_path = batch_dir / filename
        if not file_path.exists():
            file_path.write_text(content)
            created_files.append(str(file_path))

    return {
        "created_files": created_files,
        "skipped_files": skipped_files,
        "message": "AKIOS project initialized"
    }


def create_default_config() -> str:
    """Create default config.yaml content"""
    return """# AKIOS v1.0 Configuration
# Security-first defaults - modify carefully

# Security cage essentials
sandbox_enabled: true
cpu_limit: 0.8
memory_limit_mb: 256
max_open_files: 100
network_access_allowed: false

# PII & compliance
pii_redaction_enabled: true
redaction_strategy: "mask"

# Cost & loop protection
cost_kill_enabled: true
max_tokens_per_call: 1000
budget_limit_per_run: 1.0

# Audit & paths
audit_enabled: true
audit_export_enabled: true
audit_storage_path: "./audit/"
audit_export_format: "json"

# General
environment: "development"
log_level: "INFO"
"""


def create_example_workflow() -> str:
    """Create example workflow content"""
    return """name: example_workflow
description: Example AKIOS workflow demonstrating LLM and filesystem agents

steps:
  - step: 1
    agent: llm
    action: generate
    parameters:
      prompt: "Write a brief summary of artificial intelligence and its current applications."
      max_tokens: 200

  - step: 2
    agent: filesystem
    action: write
    parameters:
      path: "./data/output/ai_summary.txt"
      content: "This file will contain the AI summary from the LLM agent."

  - step: 3
    agent: filesystem
    action: list
    parameters:
      path: "./data"
"""


def create_basic_templates(base_path: Path, created_files: list, force: bool = False) -> None:
    """Create basic template files inline"""
    templates_dir = base_path / "templates"

    # Basic hello workflow
    hello_template = templates_dir / "hello-workflow.yml"
    if not hello_template.exists() or force:
        hello_content = """name: Hello World Workflow
description: |
  A simple introductory workflow demonstrating basic AKIOS functionality.
  Creates a greeting file, reads it back, and shows audit logging.

  This is the "Hello World" example for new AKIOS users.

steps:
  # Step 1: Create a simple greeting file
  - step: 1
    agent: filesystem
    config:
      allowed_paths: ["./data/output"]
      read_only: false
    action: write
    parameters:
      path: "./data/output/hello.txt"
      content: "Hello, World from AKIOS!"

  # Step 2: Read the file back to verify it was created
  - step: 2
    agent: filesystem
    config:
      allowed_paths: ["./data/output"]
    action: read
    parameters:
      path: "./data/output/hello.txt"
"""
        hello_template.write_text(hello_content)
        created_files.append(str(hello_template))

    # Basic LLM workflow
    llm_template = templates_dir / "document_ingestion.yml"
    if not llm_template.exists() or force:
        llm_content = """name: Secure Document Processing
description: |
  Hero example demonstrating AKIOS's security cage: PII redaction, Merkle audit trail,
  and sandboxed execution. This workflow reads a document, automatically redacts PII,
  generates a summary, and exports a tamper-evident audit report.

  Shows: Security-first design, real-time PII protection, cryptographic integrity.

steps:
  # Step 1: Read document from secure filesystem (path whitelisted)
  - step: 1
    agent: filesystem
    config:
      allowed_paths: ["./data/input"]
    action: read
    parameters:
      path: "./data/input/document.txt"
      # Security: Path is whitelisted, read-only access enforced

  # Step 2: Automatic PII redaction (enforced by security layer)
  # Note: PII redaction happens automatically before LLM processing
  # This step shows the redaction in action via audit logs

  # Step 3: LLM analysis with cost controls (max tokens, budget limits)
  - step: 2
    agent: llm
    config:
      provider: openai  # Options: openai, anthropic, grok, mistral, gemini
      api_key: "${OPENAI_API_KEY}"  # Or ${ANTHROPIC_API_KEY}, ${GROK_API_KEY}, ${MISTRAL_API_KEY}, ${GEMINI_API_KEY}
      model: "gpt-4o-mini"  # Or claude-3.5-sonnet, grok-4.1-fast
    action: complete
    parameters:
      prompt: |
        Analyze this document and provide a concise summary.
        Focus on key facts, entities, and main points.
        Document content will be provided with any sensitive information automatically redacted.
      max_tokens: 300
      # Security: Token limits prevent runaway costs, automatic kill-switches

  # Step 4: Store processed result (path whitelisted, controlled access)
  - step: 3
    agent: filesystem
    config:
      allowed_paths: ["./data/output"]
      read_only: false
    action: write
    parameters:
      path: "./data/output/summary.txt"
      content: "{previous_output}"
      # Security: Write access controlled, path restrictions enforced
"""
        llm_template.write_text(llm_content)
        created_files.append(str(llm_template))


def create_akios_env() -> str:
    """Create sample .env content"""
    return """# AKIOS Environment Configuration
# Edit this file with your API keys and settings
# This file is automatically loaded when running akios commands
# WARNING: Contains sensitive API keys - NEVER commit to version control!

# === API KEYS ===
# Get your API keys from the respective providers:

# OpenAI: https://platform.openai.com/api-keys
# OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic: https://console.anthropic.com/
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Grok/xAI: https://console.x.ai/
# GROK_API_KEY=xai-your-grok-key-here

# === LLM SETTINGS ===
# Default LLM provider and model
# AKIOS_LLM_PROVIDER=openai  # Options: openai, anthropic, grok, mistral, gemini
# AKIOS_LLM_MODEL=gpt-4o-mini  # Or claude-3.5-sonnet, grok-4.1-fast

# === DEVELOPMENT ===
# Use mock responses for testing (no API calls) - WARNING: Not for production!
AKIOS_MOCK_LLM=1

# === SECURITY ===
# PII redaction settings
# AKIOS_PII_REDACTION_ENABLED=true
"""


def create_env_example() -> str:
    """Create .env.example template content"""
    return """# AKIOS Environment Configuration Example
# Copy this file to .env and fill in your actual API keys
# WARNING: Never commit .env to version control!

# === API KEYS ===
# Get your API keys from the respective providers:

# OpenAI: https://platform.openai.com/api-keys
# OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic: https://console.anthropic.com/
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Grok/xAI: https://console.x.ai/
GROK_API_KEY=xai-your-grok-key-here

# Mistral AI: https://console.mistral.ai/
# MISTRAL_API_KEY=your-mistral-key-here

# Gemini/Google: https://makersuite.google.com/app/apikey
# GEMINI_API_KEY=your-gemini-key-here

# === AKIOS SETTINGS ===
# Default LLM provider and model
AKIOS_LLM_PROVIDER=grok  # Options: openai, anthropic, grok, mistral, gemini
AKIOS_LLM_MODEL=grok-3   # Provider-specific models

# Development/Testing
# AKIOS_MOCK_LLM=1        # Set to 1 for testing without API calls
# AKIOS_MOCK_LLM=0        # Set to 0 for production API calls

# Security & Performance
# AKIOS_BUDGET_LIMIT_PER_RUN=1.0    # Cost limit per workflow ($)
# AKIOS_MAX_TOKENS_PER_CALL=500     # Token limit per API call
"""


def create_gitignore() -> str:
    """Create .gitignore content"""
    return """# AKIOS project
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Environment variables (contains API keys)
.env

# Audit logs (contain sensitive data)
audit/
*.pdf
*.json

# Data directories
data/output/
data/input/private/

# Config overrides
config.local.yaml

# OS files
.DS_Store
Thumbs.db
"""


def create_readme() -> str:
    """Create README.md content for the project"""
    return """# AKIOS Project

Welcome to your AKIOS (AI Knowledge & Intelligence Operating System) project! This is a secure, sandboxed environment for running AI workflows with military-grade security.

## 🚀 Quick Start

1. **Test immediately** (mock mode enabled by default):
   ```bash
   # Test workflows without API keys first:
   {HELLO_WORKFLOW_COMMAND}
   {DOCUMENT_INGESTION_COMMAND}
   ```

   **Direct Docker (if you do not have `{get_command_prefix()}`):**
   ```bash
   docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.3 run templates/hello-workflow.yml
   ```

2. **Configure for API workflows** (if using batch_processing.yml):
   ```bash
   # Edit config.yaml to allow network access:
   network_access_allowed: true  # Required for external API calls
   ```

3. **Configure real API Keys** for production use:
   ```bash
   # Edit .env file and set AKIOS_MOCK_LLM=0, then add your API key:
   # For OpenAI: OPENAI_API_KEY=sk-your-key-here
   # For Anthropic: ANTHROPIC_API_KEY=sk-ant-your-key-here
   # For Grok: GROK_API_KEY=xai-your-key-here
   # For Mistral: MISTRAL_API_KEY=your-mistral-key-here
   # For Gemini: GEMINI_API_KEY=your-gemini-key-here
   ```

## 📁 Project Structure

```
your-project/
├── README.md           # This file - project documentation
├── workflow.yml        # ← YOUR active workflow (created by templates)
├── .env                 # API keys and configuration (edit this!)
├── .env.example         # Template with placeholder keys (copy to .env)
├── config.yaml         # 🔐 SECURITY SETTINGS - controls network access, sandboxing, costs
├── .gitignore          # Git ignore rules
├── templates/          # Pre-built workflow templates
│   ├── hello-workflow.yml
│   ├── batch_processing.yml
│   └── ...
├── data/               # Data files and workflow outputs
│   ├── input/          # Input data for workflows
│   │   ├── document_example.txt   # Sample documents for testing
│   │   ├── document_example.pdf   # (.txt, .pdf, .docx supported)
│   │   ├── document_example.docx  # Replace with your real files
│   │   └── document_example.jpg   #
│   └── output/         # Workflow results saved here
└── audit/              # Security audit logs and reports
```

**Note**: AKIOS organizes outputs in timestamped directories (like `run_20240124_143022`) to keep each workflow run separate and prevent accidental overwrites. Use `run_*` wildcards to access the latest results.

## 🚀 Available Templates

AKIOS comes with 4 pre-built workflow templates. Here's what each one does:

| Template | Purpose | Input Required | Output | Network Access | Security Features |
|----------|---------|----------------|--------|---------------|-------------------|
| **hello-workflow.yml** | Generate creative AI greetings | None (uses prompt only) | `data/output/run_*/hello-ai.txt` | LLM API calls | LLM sandboxing, audit logging |
| **document_ingestion.yml** | Analyze documents with PII redaction | `data/input/[filename]` (.txt, .pdf, .docx supported) | `data/output/run_*/summary.txt` + audit | LLM API calls | PII redaction, Merkle audit trail |
| **file_analysis.yml** | Analyze files with container isolation | `data/input/[filename]` | `data/output/run_*/analysis.txt` | None | Container sandboxing, safe tool execution |
| **batch_processing.yml** | Multi-file AI analysis with aggregation | `data/input/batch/` (directory) | `data/output/run_*/batch-summary.json` | LLM API calls | Cost tracking, batch PII protection |

### Quick Start Examples

```bash
# Hello world example
{HELLO_WORKFLOW_COMMAND}

# Batch processing workflow
{BATCH_PROCESSING_COMMAND}

# Document analysis
{FILE_ANALYSIS_COMMAND}

# Direct Docker (if you do not have {get_command_prefix()})
docker run --rm -v "$(pwd):/app" -w /app akiosai/akios:v1.0.3 run templates/hello-workflow.yml
```

### Creating Custom Workflows

1. Run a template: {HELLO_WORKFLOW_COMMAND}
2. Edit the created workflow.yml: `nano workflow.yml`
3. Run your customized version: {get_command_prefix()} run workflow.yml

## 🔑 API Configuration

**Environment Setup:**
- `.env.example` - Template file with placeholder keys (safe to commit)
- `.env` - Your working file with real API keys (NEVER commit this!)

Copy `.env.example` to `.env` and fill in your real API keys:

```bash
cp .env.example .env
# Then edit .env with your actual keys
```

Edit the `.env` file to configure your LLM provider:

### OpenAI
```bash
OPENAI_API_KEY=sk-your-openai-key-here
AKIOS_LLM_PROVIDER=openai
AKIOS_LLM_MODEL=gpt-4o-mini  # or gpt-4o
```

### Anthropic
```bash
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
AKIOS_LLM_PROVIDER=anthropic
AKIOS_LLM_MODEL=claude-3.5-sonnet  # or claude-3.5-haiku
```

### Grok (xAI)
```bash
GROK_API_KEY=xai-your-grok-key-here
AKIOS_LLM_PROVIDER=grok
AKIOS_LLM_MODEL=grok-3  # or grok-4.1
```

### Mistral AI
```bash
MISTRAL_API_KEY=your-mistral-key-here
AKIOS_LLM_PROVIDER=mistral
AKIOS_LLM_MODEL=mistral-small  # or mistral-medium
```

### Gemini (Google)
```bash
GEMINI_API_KEY=your-gemini-key-here
AKIOS_LLM_PROVIDER=gemini
AKIOS_LLM_MODEL=gemini-1.5-flash  # or gemini-1.5-pro
```

## 🚨 PRODUCTION WARNING: Mock Mode

**⚠️ NEVER use AKIOS_MOCK_LLM=1 in production environments!**

Mock mode provides simulated AI responses for **testing only**. Production deployments must use real API keys and disable mock mode:

### ❌ What Mock Mode Does:
- Returns fake AI responses instead of real LLM calls
- Bypasses actual API authentication and costs
- Provides no real AI intelligence or analysis
- Audit logs will show mock mode usage warnings

### ✅ Production Requirements:
- Set `AKIOS_MOCK_LLM=0` in `.env`
- Configure real API keys for your chosen provider
- Enable `network_access_allowed: true` in `config.yaml`
- Monitor actual API costs and usage

### 🔍 How to Verify Production Readiness:
```bash
# Check configuration
{suggest_command('status')}

# Look for:
# ✅ Real API keys detected
# ❌ Mock mode: Disabled (should NOT appear)
# ✅ Network access: Enabled
```

## ⚙️ Configuration Settings

AKIOS uses a `config.yaml` file to control security and runtime behavior. **Edit this file carefully** - these settings control your security cage.

### 🔐 Network Access Control

**`network_access_allowed`** - Controls ALL external network access:
- `false` (default): **Blocks all external API calls** (HTTP + LLM)
- `true`: **Allows external API calls** (required for most workflows)

```yaml
# Security-first default - no external access
network_access_allowed: false
```

**When to change:**
- Set to `true` if using templates that call external APIs (batch_processing.yml)
- Keep `false` for maximum security when only processing local data

**Security Impact:**
- `false`: Complete network isolation, maximum security
- `true`: Allows HTTP requests and LLM API calls

### 🛡️ Other Security Settings

```yaml
# Process isolation and resource limits
sandbox_enabled: true          # Required for security
cpu_limit: 0.8                 # CPU usage limit (0.0-1.0)
memory_limit_mb: 256          # Memory limit in MB
max_open_files: 100           # Maximum open file descriptors

# Data protection
pii_redaction_enabled: true    # Auto PII masking
redaction_strategy: "mask"     # How to redact sensitive data

# Cost protection (LLM calls)
cost_kill_enabled: true        # Enable cost limits
max_tokens_per_call: 1000      # Token limit per LLM call
budget_limit_per_run: 1.0      # Max cost per workflow ($)

# Audit and compliance
audit_enabled: true           # Enable audit logging
audit_storage_path: "./audit/" # Where to store audit logs
audit_export_format: "pdf"    # Audit report format
```

### 🚨 Critical Security Notes

1. **Never set `network_access_allowed: true` unnecessarily** - it allows external API calls
2. **Keep `sandbox_enabled: true`** - this provides process isolation
3. **Monitor costs** - set reasonable `budget_limit_per_run` values
4. **PII redaction is automatic** - sensitive data is masked in logs and responses

### 📋 Configuration Examples

**Maximum Security** (default):
```yaml
network_access_allowed: false  # No external access
sandbox_enabled: true
pii_redaction_enabled: true
budget_limit_per_run: 1.0
```

**API Workflows** (required for batch_processing.yml):
```yaml
network_access_allowed: true   # Allow external API calls
sandbox_enabled: true
pii_redaction_enabled: true
budget_limit_per_run: 5.0     # Higher budget for API work
```

## 🏃 Running Workflows

### Using Templates
```bash
# Hello world example
{HELLO_WORKFLOW_COMMAND}

# Batch processing workflow
{BATCH_PROCESSING_COMMAND}

# Document analysis
{FILE_ANALYSIS_COMMAND}
```

### Creating Custom Workflows
1. Run a template: {HELLO_WORKFLOW_COMMAND}
2. Edit the created workflow.yml: `nano workflow.yml`
3. Run your customized version: {get_command_prefix()} run workflow.yml

### Workflow Format
```yaml
name: "My Workflow"
description: "What this workflow does"

steps:
  - name: "LLM Task"
    type: "llm"
    prompt: "Your prompt here"
    model: "grok-3"  # optional, uses AKIOS_LLM_MODEL if not set

  - name: "Save Result"
    type: "save"
    path: "data/output/result.txt"
```

## 🔒 Security Features

AKIOS provides **military-grade security**:

- **Sandboxing**: Complete process isolation
- **PII Redaction**: Automatic sensitive data masking
- **Audit Logging**: Cryptographic audit trail
- **Resource Limits**: CPU, memory, and cost controls
- **Command Allowlisting**: Only approved operations permitted

### Deployment Options

**🐳 Docker (Cross-platform)**: Policy-based security, recommended for most users
- Works on macOS, Windows, Linux
- Command allowlisting + PII redaction
- No kernel modifications needed

**🐧 Native Linux (Maximum Security)**: Full kernel-hard sandboxing
- Linux-only, maximum protection
- cgroups v2 + seccomp-bpf syscall filtering
- For production/high-security environments

## 📊 Monitoring & Status

```bash
# Check system status
{suggest_command('status')}

# View audit logs
{suggest_command('audit')}

# Export audit reports
{suggest_command('audit export --format pdf')}
```

## 🆘 Troubleshooting

### Common Issues

**"API key not found"**
- Check that you've uncommented and set the correct API key in `.env`
- Verify the key format (starts with `sk-` for OpenAI, `sk-ant-` for Anthropic, `xai-` for Grok, or provider-specific formats for Mistral/Gemini)

**"Workflow not found"**
- Use relative paths: `templates/hello-workflow.yml`
- Check that the file exists in the `templates/` directory or that `workflow.yml` exists in the project root

**"Permission denied"**
- Check that Docker is running

**"Security warnings"**
- These are normal - AKIOS shows security status
- Docker deployment uses policy-based security (weaker than native Linux)
- For maximum security, deploy on native Linux

### Getting Help

- **Documentation**: Check `templates/README.md` for workflow examples
- **Status Check**: Run `{suggest_command('status')}` for system diagnostics
- **Logs**: Recent activity in `audit/` directory

## 🎯 Next Steps

1. **Test the templates**: Try all workflows with mock responses
2. **Explore multi-format support**: Test with sample files (document_example.*) in .txt, .pdf, or .docx formats
3. **Configure real API keys** in `.env` (set `AKIOS_MOCK_LLM=0`)
4. **Customize workflows** by editing `workflow.yml` after running templates
5. **Check security status**: `{suggest_command('status')}`

Happy AI workflow building with AKIOS! 🚀🤖
"""


def create_sample_document() -> str:
    """Create sample document content for testing document_ingestion template"""
    return """Sample Business Document - Q4 2025 Financial Report

Dear Mr. John Smith,

This confidential document contains sensitive information about our company's Q4 2025 performance.

Contact Information:
- Email: john.smith@company.com
- Phone: (555) 123-4567
- Address: 123 Business Street, Suite 456, New York, NY 10001

Financial Summary:
Revenue: $2.5 million
Expenses: $1.8 million
Net Profit: $700,000

Key Achievements:
1. Increased market share by 15%
2. Launched 3 new products
3. Expanded to 5 new international markets

Employee Information:
- CEO: Sarah Johnson (sarah.johnson@company.com)
- CFO: Michael Davis (michael.davis@company.com, phone: 555-987-6543)
- HR Director: Emily Chen (emily.chen@company.com)

Strategic Initiatives for 2026:
- AI implementation across all departments
- Expansion into European markets
- Development of sustainable product lines
- Digital transformation completion

Please treat this information as confidential and do not share with unauthorized personnel.

Best regards,
Board of Directors
Company Inc.
Date: January 4, 2026"""


def create_sample_analysis_file() -> str:
    """Create sample file content for testing file_analysis template"""
    return """Sample Analysis Target File - Security Intelligence Test Data

Contact Information:
Email: john.doe@company.com
Phone: (555) 123-4567
Backup Email: admin@security.example.org

Network Data:
IP Address: 192.168.1.100
External IP: 203.0.113.45
Domain: https://secure-api.company.com/v1/data
URL: http://malicious-site.ru/download.exe

Financial Data:
Credit Card: 4111 1111 1111 1111 (Visa test card)
Account Number: 1234567890123456
Transaction Amount: $2,459.99

System Logs:
Timestamp: 2024-01-15 14:30:22 UTC
Error Code: 500
User ID: 987654
Session ID: abc123def456

Security Events:
Login attempt from IP 10.0.0.1 at 2024-01-15 09:15:33
Suspicious activity detected: 47 failed login attempts
File hash: a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3

Business Metrics:
Total Revenue: $1,250,000
Active Users: 15,432
Conversion Rate: 3.45%
Growth Rate: 127.8%

This file contains various patterns for testing automated security analysis, pattern detection, and threat assessment capabilities."""
