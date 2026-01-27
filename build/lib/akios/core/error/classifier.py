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
Error Classification System - Categorize and handle errors intelligently

Provides error categorization, fingerprinting, and severity assessment
for intelligent error handling and user guidance.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
import re

from ..ui.commands import suggest_command


class ErrorCategory(Enum):
    """Error categories for intelligent classification."""
    CONFIGURATION = "configuration"
    RUNTIME = "runtime"
    SECURITY = "security"
    NETWORK = "network"
    VALIDATION = "validation"
    RESOURCE = "resource"


class ErrorSeverity(Enum):
    """Error severity levels."""
    FATAL = "fatal"          # Cannot continue, requires immediate fix
    RECOVERABLE = "recoverable"  # Can continue with user intervention
    WARNING = "warning"      # Non-blocking, informational


class ErrorFingerprint:
    """
    Error fingerprinting for pattern recognition and intelligent handling.
    """

    def __init__(self, error_message: str, error_type: Optional[str] = None):
        self.message = error_message
        self.type = error_type
        self.category = self._categorize_error()
        self.severity = self._assess_severity()
        self.recovery_suggestions = self._generate_recovery_suggestions()

    def _categorize_error(self) -> ErrorCategory:
        """Categorize error based on message patterns."""
        message_lower = self.message.lower()

        # Configuration errors
        if any(keyword in message_lower for keyword in [
            'config', 'configuration', 'missing required field',
            'invalid agent', 'invalid action', 'workflow validation failed'
        ]):
            return ErrorCategory.CONFIGURATION

        # Security errors
        if any(keyword in message_lower for keyword in [
            'security', 'permission', 'access denied', 'syscall',
            'sandbox', 'isolation', 'seccomp'
        ]):
            return ErrorCategory.SECURITY

        # Network errors
        if any(keyword in message_lower for keyword in [
            'network', 'connection', 'timeout', 'api', 'http',
            'connection refused', 'network is unreachable'
        ]):
            return ErrorCategory.NETWORK

        # Validation errors
        if any(keyword in message_lower for keyword in [
            'validation', 'schema', 'json', 'yaml', 'parse'
        ]):
            return ErrorCategory.VALIDATION

        # Resource errors
        if any(keyword in message_lower for keyword in [
            'memory', 'disk', 'cpu', 'resource', 'limit', 'quota'
        ]):
            return ErrorCategory.RESOURCE

        # Default to runtime
        return ErrorCategory.RUNTIME

    def _assess_severity(self) -> ErrorSeverity:
        """Assess error severity based on category and content."""
        # Fatal errors
        if self.category == ErrorCategory.SECURITY:
            return ErrorSeverity.FATAL

        # Check for fatal keywords
        fatal_keywords = ['fatal', 'critical', 'cannot continue', 'aborted']
        if any(keyword in self.message.lower() for keyword in fatal_keywords):
            return ErrorSeverity.FATAL

        # Configuration errors are usually recoverable
        if self.category == ErrorCategory.CONFIGURATION:
            return ErrorSeverity.RECOVERABLE

        # Network errors might be recoverable
        if self.category == ErrorCategory.NETWORK:
            return ErrorSeverity.RECOVERABLE

        # Default to warning for unknown cases
        return ErrorSeverity.WARNING

    def _generate_recovery_suggestions(self) -> List[str]:
        """Generate context-aware recovery suggestions."""
        suggestions = []

        if self.category == ErrorCategory.CONFIGURATION:
            if 'missing required field' in self.message:
                field_match = re.search(r"missing required field '([^']+)'", self.message)
                if field_match:
                    field = field_match.group(1)
                    suggestions.append(f"Add '{field}' field to your workflow configuration")

            if 'invalid agent' in self.message:
                suggestions.append("Use one of: filesystem, http, llm, tool_executor")
                suggestions.append("Check agent spelling in your workflow.yml")

            if 'invalid action' in self.message:
                suggestions.append("Check the allowed actions for your agent type")
                suggestions.append("Review the workflow schema documentation")

        elif self.category == ErrorCategory.SECURITY:
            if 'syscall' in self.message or 'seccomp' in self.message:
                suggestions.append("This error indicates a security violation")
                suggestions.append("Contact system administrator for security policy review")

        elif self.category == ErrorCategory.NETWORK:
            if 'connection refused' in self.message:
                suggestions.append("Check network connectivity and firewall settings")
                suggestions.append("Verify API endpoints are accessible")

            if 'timeout' in self.message:
                suggestions.append("Increase timeout values in configuration")
                suggestions.append("Check network latency and stability")

        elif self.category == ErrorCategory.VALIDATION:
            if 'schema' in self.message:
                suggestions.append("Validate your workflow.yml syntax")
                suggestions.append("Compare with example templates in templates/ directory")
                suggestions.append("Use 'akios run workflow.yml --dry-run' to validate without execution")

        elif self.category == ErrorCategory.RESOURCE:
            if 'memory' in self.message:
                suggestions.append("Reduce workflow complexity or increase memory limits")
                suggestions.append("Check system memory availability")

            if 'disk' in self.message:
                suggestions.append("Free up disk space or reduce output file sizes")
                suggestions.append("Check disk space availability")

        # Context-aware suggestions for common user scenarios
        message_lower = self.message.lower()
        if 'permission denied' in message_lower or 'access denied' in message_lower:
            suggestions.append("This may be a Docker file permission issue. Try:")
            suggestions.append("• On macOS: Docker Desktop → Settings → Resources → File sharing")
            suggestions.append("• On Linux: Ensure current directory is accessible to Docker")
            suggestions.append("• Alternative: " + suggest_command("init ~/akios-project"))

        if 'api key' in message_lower or 'authentication' in message_lower:
            suggestions.append("You're in demo mode. Add API keys to .env for real AI:")
            suggestions.append("  GROK_API_KEY=your-key-here")
            suggestions.append("  OPENAI_API_KEY=your-key-here  # if using OpenAI")
            suggestions.append("  AKIOS_MOCK_LLM=0")
            suggestions.append("Then restart your workflow")

        if 'mock mode' in message_lower:
            suggestions.append("Demo mode is active - no real API calls are being made")
            suggestions.append("Add API keys to .env and set AKIOS_MOCK_LLM=0 for live AI")
            suggestions.append("Current results are sample responses for testing")

        # Generic suggestions
        if not suggestions:
            suggestions.append("Check the troubleshooting guide for this error type")
            suggestions.append("Review recent changes to workflow configuration")

        return suggestions

    def get_user_friendly_message(self) -> str:
        """Generate user-friendly error message with context."""
        category_names = {
            ErrorCategory.CONFIGURATION: "Configuration Error",
            ErrorCategory.RUNTIME: "Runtime Error",
            ErrorCategory.SECURITY: "Security Error",
            ErrorCategory.NETWORK: "Network Error",
            ErrorCategory.VALIDATION: "Validation Error",
            ErrorCategory.RESOURCE: "Resource Error"
        }

        severity_indicators = {
            ErrorSeverity.FATAL: "🚨",
            ErrorSeverity.RECOVERABLE: "⚠️",
            ErrorSeverity.WARNING: "ℹ️"
        }

        category_name = category_names.get(self.category, "Unknown Error")
        severity_indicator = severity_indicators.get(self.severity, "❓")

        message = f"{severity_indicator} {category_name}\n{self.message}"

        if self.recovery_suggestions:
            message += "\n\nSuggestions:"
            for suggestion in self.recovery_suggestions[:3]:  # Limit to top 3
                message += f"\n• {suggestion}"

        return message


def classify_error(error_message: str, error_type: Optional[str] = None) -> ErrorFingerprint:
    """
    Classify an error message and return fingerprint with metadata.

    Args:
        error_message: The error message to classify
        error_type: Optional error type for additional context

    Returns:
        ErrorFingerprint with categorization, severity, and suggestions
    """
    return ErrorFingerprint(error_message, error_type)


def get_error_category_stats(error_messages: List[str]) -> Dict[str, int]:
    """
    Analyze multiple error messages and return category statistics.

    Args:
        error_messages: List of error messages to analyze

    Returns:
        Dictionary with category counts
    """
    stats = {}
    for message in error_messages:
        fingerprint = classify_error(message)
        category_name = fingerprint.category.value
        stats[category_name] = stats.get(category_name, 0) + 1

    return stats
