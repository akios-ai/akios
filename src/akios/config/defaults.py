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
Default configuration values for AKIOS

Security-conservative defaults that prioritize safety over convenience.
"""

from .settings import Settings


# Default settings instance with security-first values
DEFAULT_SETTINGS = Settings(
    # Security cage - maximum protection
    sandbox_enabled=True,
    cpu_limit=0.8,  # Conservative CPU limit
    memory_limit_mb=256,  # Small memory footprint
    max_open_files=100,
    max_file_size_mb=10,  # 10MB file size limit
    network_access_allowed=False,  # No network by default

    # PII protection - always enabled
    pii_redaction_enabled=True,
    redaction_strategy="mask",  # Safe default

    # Cost control - strict limits
    cost_kill_enabled=True,
    max_tokens_per_call=1000,  # Allow PDF/DOCX analysis
    budget_limit_per_run=1.0,  # $1 per run default

    # Audit - comprehensive by default
    audit_enabled=True,
    audit_export_enabled=True,
    audit_storage_path="./audit/",
    audit_export_format="json",

    # LLM provider controls
    allowed_providers=["openai", "anthropic", "grok", "mistral", "gemini"],

    # General - safe defaults
    environment="development",
    log_level="INFO"
)


def get_default_settings() -> Settings:
    """Get default settings instance"""
    return DEFAULT_SETTINGS.copy()
