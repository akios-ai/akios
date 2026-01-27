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
OpenAI LLM Provider

Implements the LLMProvider interface for OpenAI's API.
Supports GPT models with real token counting and error handling.
"""

import openai
from typing import Dict, Any, List
from .base import LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider implementation.

    Supports GPT-4, GPT-4-turbo, GPT-4o, and GPT-4o-mini models.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(api_key, model, **kwargs)

        # Validate API key format
        if not api_key.startswith('sk-'):
            raise ProviderError("OpenAI API key should start with 'sk-'")

        # Validate model support
        allowed_models = [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4"
        ]

        if model not in allowed_models:
            raise ProviderError(f"Unsupported OpenAI model: {model}. Supported: {allowed_models}")

        # Initialize OpenAI client
        try:
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            raise ProviderError(f"Failed to initialize OpenAI client: {str(e)}")

    def complete(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion using OpenAI API.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional OpenAI parameters

        Returns:
            Dict with completion results and token usage
        """
        # Validate input for safety and size limits
        self.validate_input(prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30,  # 30 second timeout for consistency
                **kwargs
            )

            # Extract response data
            choice = response.choices[0]
            usage = response.usage

            return {
                'text': choice.message.content,
                'tokens_used': usage.total_tokens,
                'finish_reason': choice.finish_reason,
                'model': response.model,
                'usage': {
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                    'total_tokens': usage.total_tokens
                }
            }

        except openai.APIError as e:
            raise ProviderError(f"OpenAI API error: {str(e)}")
        except openai.AuthenticationError as e:
            raise ProviderError(f"OpenAI authentication failed: {str(e)}")
        except openai.RateLimitError as e:
            raise ProviderError(f"OpenAI rate limit exceeded: {str(e)}")
        except Exception as e:
            raise ProviderError(f"OpenAI request failed: {str(e)}")

    def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using OpenAI API.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional OpenAI parameters

        Returns:
            Dict with chat response and token usage
        """
        # Validate all message contents for safety and size limits
        for message in messages:
            if 'content' in message:
                self.validate_input(message['content'])

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30,  # 30 second timeout for consistency
                **kwargs
            )

            # Extract response data
            choice = response.choices[0]
            usage = response.usage

            return {
                'response': choice.message.content,
                'tokens_used': usage.total_tokens,
                'finish_reason': choice.finish_reason,
                'model': response.model,
                'usage': {
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                    'total_tokens': usage.total_tokens,
                    'messages': messages  # Include for audit logging
                }
            }

        except openai.APIError as e:
            raise ProviderError(f"OpenAI chat API error: {str(e)}")
        except openai.AuthenticationError as e:
            raise ProviderError(f"OpenAI authentication failed: {str(e)}")
        except openai.RateLimitError as e:
            raise ProviderError(f"OpenAI rate limit exceeded: {str(e)}")
        except Exception as e:
            raise ProviderError(f"OpenAI chat request failed: {str(e)}")

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported OpenAI models.

        Returns:
            List of supported model names
        """
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4"
        ]

    def validate_config(self) -> None:
        """
        Validate OpenAI-specific configuration.
        """
        super().validate_config()

        # Additional validation for OpenAI
        if not self.model.startswith('gpt-'):
            raise ProviderError(f"Invalid OpenAI model format: {self.model}")

        # Test API key format (basic validation)
        if not self.api_key.startswith('sk-'):
            raise ProviderError("OpenAI API key should start with 'sk-'")
