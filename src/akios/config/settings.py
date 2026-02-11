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
Pydantic settings model for AKIOS configuration

Defines all configurable parameters for the security cage.
"""

from typing import List, Dict, Optional
import logging

from pydantic import Field, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    AKIOS Configuration Settings

    Security-first defaults with conservative values.
    """

    # Security cage essentials
    sandbox_enabled: bool = Field(True, description="Enable kernel-level sandboxing")
    cpu_limit: float = Field(0.8, gt=0.0, le=1.0, description="CPU usage limit (fraction)")
    memory_limit_mb: int = Field(256, gt=0, description="Memory limit in MB")
    max_open_files: int = Field(100, gt=10, description="Maximum open file descriptors")
    max_file_size_mb: int = Field(10, gt=0, description="Maximum file size in MB for writes")
    network_access_allowed: bool = Field(False, description="Allow network access")
    allowed_domains: List[str] = Field(
        [],
        description="Allowed domains for HTTP agent in strict mode (e.g. ['api.salesforce.com'])"
    )

    # PII & compliance
    pii_redaction_enabled: bool = Field(True, description="Enable real-time PII redaction")
    redaction_strategy: str = Field(
        "mask",
        pattern="^(mask|hash|remove)$",
        description="PII redaction strategy"
    )
    pii_redaction_outputs: bool = Field(True, description="Enable PII redaction on LLM outputs")
    pii_redaction_aggressive: bool = Field(False, description="Use aggressive PII redaction rules")

    # Cost & loop protection
    cost_kill_enabled: bool = Field(True, description="Enable cost kill-switches")
    max_tokens_per_call: int = Field(1000, gt=0, description="Maximum tokens per LLM call")
    budget_limit_per_run: float = Field(1.0, gt=0.0, description="Budget limit per run in USD")

    # Audit & paths
    audit_enabled: bool = Field(True, description="Enable audit logging")
    audit_export_enabled: bool = Field(False, description="Enable audit export functionality")
    audit_storage_path: str = Field("./audit/", description="Audit log storage path")
    audit_export_format: str = Field(
        default="json",
        pattern="^(json)$",
        description="Audit export format"
    )

    # UI & Theming
    ui_theme: str = Field(
        default="default",
        description="UI color theme (default, dark, light, custom)"
    )
    ui_custom_theme: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom theme color overrides"
    )

    # LLM provider controls
    allowed_providers: List[str] = Field(
        ["openai", "anthropic", "grok", "mistral", "gemini"],
        description="Allowed LLM providers for security"
    )
    mock_llm: bool = Field(False, description="Enable mock LLM mode for testing")

    # Tool executor controls
    allowed_commands: List[str] = Field(
        ["echo", "cat", "grep", "head", "tail", "wc", "ls", "pwd", "date"],
        description="Globally allowed commands for tool_executor agent"
    )

    # General
    environment: str = Field(
        "development",
        pattern="^(development|testing|production)$",
        description="Runtime environment"
    )
    log_level: str = Field(
        "INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR)$",
        description="Logging level"
    )

    @model_validator(mode='after')
    def validate_sandbox_in_production(self) -> 'Settings':
        """Prevent disabling sandbox in production"""
        if not self.sandbox_enabled and self.environment == 'production':
            raise ValueError(
                "sandbox_enabled cannot be False in production environment. "
                "Disabling sandbox removes ALL security (PII, audit, command restrictions, resource limits). "
                "This is only allowed in development/testing environments."
            )
        
        if not self.sandbox_enabled:
            # Log loud warning even in non-production
            logger = logging.getLogger(__name__)
            logger.warning(
                "⚠️  SECURITY WARNING: Sandbox is DISABLED! "
                "This removes ALL security protections including PII redaction, "
                "audit logging, command restrictions, and resource limits. "
                "This should ONLY be used for local development/testing."
            )
        
        return self

    model_config = SettingsConfigDict(
        env_prefix="AKIOS_",
        env_file=None,  # Disable .env file loading to avoid permission issues
        extra="forbid",  # Forbid extra configuration to catch typos/nesting errors
    )

