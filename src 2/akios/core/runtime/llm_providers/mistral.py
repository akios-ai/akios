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
Mistral LLM Provider

Implements the LLMProvider interface for Mistral AI's API.
Supports Mistral models with real token counting and error handling.
"""

import requests
from typing import Dict, Any, List
from .base import LLMProvider, ProviderError


class MistralProvider(LLMProvider):
    """
    Mistral provider implementation.

    Supports Mistral small, medium, and large models.
    """

    def __init__(self, api_key: str, model: str = "mistral-small", **kwargs):
        super().__init__(api_key, model, **kwargs)

        # Validate model support
        allowed_models = [
            "mistral-small",
            "mistral-medium",
            "mistral-large"
        ]

        if model not in allowed_models:
            raise ProviderError(f"Unsupported Mistral model: {model}. Supported: {allowed_models}")

        # Validate API key format (Mistral keys are typically alphanumeric)
        if not api_key or not isinstance(api_key, str) or len(api_key.strip()) == 0:
            raise ProviderError("Mistral API key cannot be empty")

        # Set API endpoint
        self.base_url = "https://api.mistral.ai/v1"

    def complete(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion using Mistral API.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Mistral parameters

        Returns:
            Dict with completion results
        """
        # Validate input for safety and size limits
        self.validate_input(prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # 120s for large prompts with high max_tokens
            )
            response.raise_for_status()

            result = response.json()
            choice = result["choices"][0]
            message = choice["message"]

            # Extract token usage
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", usage.get("completion_tokens", 0) + usage.get("prompt_tokens", self.estimate_tokens(prompt, model_family="mistral")))

            return {
                "text": message["content"],
                "tokens_used": tokens_used,
                "model": result.get("model", self.model),
                "finish_reason": choice.get("finish_reason", "completed"),
                "usage": usage
            }

        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code'):
                if e.response.status_code == 401:
                    raise ProviderError("Invalid Mistral API key")
                elif e.response.status_code == 429:
                    raise ProviderError("Mistral API rate limit exceeded")
                elif e.response.status_code == 400:
                    raise ProviderError(f"Invalid request to Mistral API: {e.response.text}")
            raise ProviderError(f"Mistral API request failed: {str(e)}")

    def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using Mistral API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Dict with completion results
        """
        # Validate all message contents for safety and size limits
        for message in messages:
            if 'content' in message:
                self.validate_input(message['content'])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # 120s for large prompts with high max_tokens
            )
            response.raise_for_status()

            result = response.json()
            choice = result["choices"][0]
            message = choice["message"]
            response_text = message["content"]

            # Extract token usage
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", self.estimate_tokens(" ".join([msg.get('content', '') for msg in messages]) + " " + response_text, model_family="mistral"))

            return {
                "response": message["content"],
                "tokens_used": tokens_used,
                "model": result.get("model", self.model),
                "finish_reason": choice.get("finish_reason", "completed"),
                "usage": usage
            }

        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code'):
                if e.response.status_code == 401:
                    raise ProviderError("Invalid Mistral API key")
                elif e.response.status_code == 429:
                    raise ProviderError("Mistral API rate limit exceeded")
                elif e.response.status_code == 400:
                    raise ProviderError(f"Invalid request to Mistral API: {e.response.text}")
            raise ProviderError(f"Mistral API request failed: {str(e)}")

    def validate_config(self) -> None:
        """Validate provider configuration by making a small test request."""
        try:
            # Make a minimal completion request to validate API key
            self.complete("test", max_tokens=1)
        except ProviderError:
            raise  # Re-raise provider errors
        except Exception as e:
            raise ProviderError(f"Mistral configuration validation failed: {str(e)}")

    def estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost for token usage.

        Mistral pricing (approximate):
        - mistral-small: $0.0002 per token
        - mistral-medium: $0.00027 per token
        - mistral-large: $0.0004 per token
        """
        # Convert to cost per 1K tokens for consistency
        pricing = {
            "mistral-small": 0.20,     # $0.20 per 1K tokens
            "mistral-medium": 0.27,    # $0.27 per 1K tokens
            "mistral-large": 0.40      # $0.40 per 1K tokens
        }

        cost_per_1k = pricing.get(self.model, 0.20)
        return (tokens / 1000) * cost_per_1k
