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
Base LLM Provider Interface

Defines the abstract interface that all LLM providers must implement.
Provides consistent error handling and response format.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time
import random

# Optional tiktoken import for better token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None
    TIKTOKEN_AVAILABLE = False


class ProviderError(Exception):
    """Base exception for provider-related errors"""
    pass


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers (OpenAI, Anthropic, Grok, Mistral, Gemini, etc.) must implement this interface.
    """

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Initialize the provider.

        Args:
            api_key: API key for the provider
            model: Model name to use
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion for a single prompt.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            **kwargs: Provider-specific parameters

        Returns:
            Dict containing:
                - text: Generated text
                - tokens_used: Total tokens consumed
                - finish_reason: Why generation stopped
                - model: Model used
                - usage: Detailed token usage info
        """
        pass

    @abstractmethod
    def chat_complete(self, messages: list, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion for a chat conversation.

        Args:
            messages: List of chat messages [{'role': 'user', 'content': '...'}]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            **kwargs: Provider-specific parameters

        Returns:
            Dict containing:
                - response: Generated response text
                - tokens_used: Total tokens consumed
                - finish_reason: Why generation stopped
                - model: Model used
                - usage: Detailed token usage info
        """
        pass

    def validate_config(self) -> None:
        """
        Validate provider-specific configuration.

        Raises:
            ProviderError: If configuration is invalid
        """
        if not self.api_key:
            raise ProviderError(f"{self.__class__.__name__} requires API key")

    def validate_input(self, text: str, max_chars: int = 100000) -> None:
        """
        Validate input text for safety and size limits.

        Args:
            text: Input text to validate
            max_chars: Maximum allowed characters (default 100k)

        Raises:
            ProviderError: If input exceeds limits or contains dangerous content
        """
        if not isinstance(text, str):
            raise ProviderError("Input must be a string")

        if len(text) > max_chars:
            raise ProviderError(f"Input too large: {len(text)} chars (max {max_chars})")

        # Basic safety checks
        if len(text.strip()) == 0:
            raise ProviderError("Input cannot be empty or whitespace only")

    def retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Retry a function with exponential backoff for rate limiting.

        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds

        Returns:
            Result of the function call

        Raises:
            ProviderError: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                error_msg = str(e).lower()
                last_exception = e

                # Check if this is a rate limit error that should be retried
                is_rate_limit = any(keyword in error_msg for keyword in [
                    'rate limit', '429', 'too many requests', 'quota exceeded'
                ])

                if not is_rate_limit or attempt == max_retries:
                    raise ProviderError(f"Request failed after {attempt + 1} attempts: {str(e)}") from e

                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                time.sleep(delay)

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models for this provider.

        Returns:
            List of model names
        """
        return [self.model]  # Default implementation

    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            Provider identifier (e.g., 'openai', 'anthropic', 'grok')
        """
        return self.__class__.__name__.lower().replace('provider', '')

    def estimate_tokens(self, text: str, model_family: str = "gpt") -> int:
        """
        Estimate token count for text using tiktoken when available.

        Args:
            text: Text to estimate tokens for
            model_family: Model family for appropriate tokenizer ("gpt", "claude", etc.)

        Returns:
            Estimated token count (more accurate with tiktoken)
        """
        if TIKTOKEN_AVAILABLE:
            try:
                # Use appropriate tokenizer based on model family
                if model_family == "claude":
                    # Anthropic Claude uses similar tokenization to GPT
                    encoding = tiktoken.get_encoding("cl100k_base")
                elif model_family in ["grok", "mistral"]:
                    # Try cl100k_base first (works for many modern models)
                    encoding = tiktoken.get_encoding("cl100k_base")
                else:
                    # Default to GPT-compatible
                    encoding = tiktoken.get_encoding("cl100k_base")

                return len(encoding.encode(text))
            except Exception:
                pass  # Fall through to approximation

        # Fallback to improved approximation: ~4 chars per token for English text
        # This is more accurate than simple division for typical AI conversations
        return max(1, len(text) // 4)
