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
Ollama LLM Provider

Implements the LLMProvider interface for locally-hosted Ollama models.
Connects to the Ollama REST API (default: http://localhost:11434).
No API key required — runs entirely on local hardware.
"""

import os
import requests
from typing import Dict, Any, List
from .base import LLMProvider, ProviderError


class OllamaProvider(LLMProvider):
    """
    Ollama provider implementation for locally-hosted open-source models.

    Connects to an Ollama server via its OpenAI-compatible REST API.
    Supports Llama, Mistral, Gemma, Phi, and any model available through Ollama.
    """

    def __init__(self, api_key: str = "", model: str = "llama3.2", **kwargs):
        # Ollama doesn't need an API key — pass empty string to satisfy base class
        super().__init__(api_key or "", model, **kwargs)

        # Resolve Ollama base URL from environment or default to localhost
        self.base_url = (
            os.getenv("OLLAMA_HOST")
            or os.getenv("OLLAMA_BASE_URL")
            or "http://localhost:11434"
        ).rstrip("/")

    def complete(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion using Ollama's OpenAI-compatible API.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters (top_p, etc.)

        Returns:
            Dict with completion results and token usage
        """
        self.validate_input(prompt)

        headers = {"Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        # Pass through optional sampling parameters
        if "top_p" in kwargs:
            payload["options"]["top_p"] = kwargs["top_p"]

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("message", {}).get("content", "")

            # Ollama returns eval_count / prompt_eval_count for token usage
            prompt_tokens = data.get("prompt_eval_count", self.estimate_tokens(prompt, model_family="ollama"))
            completion_tokens = data.get("eval_count", self.estimate_tokens(content, model_family="ollama"))
            total_tokens = prompt_tokens + completion_tokens

            return {
                "text": content,
                "tokens_used": total_tokens,
                "finish_reason": "stop",
                "model": data.get("model", self.model),
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }

        except requests.ConnectionError:
            raise ProviderError(
                "Cannot connect to Ollama server. "
                f"Ensure Ollama is running at {self.base_url}\n"
                "Install: https://ollama.com  |  Start: ollama serve"
            )
        except requests.Timeout:
            raise ProviderError(f"Ollama request timed out after 120s (model: {self.model})")
        except requests.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                status = e.response.status_code
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("error", e.response.text)
                except Exception:
                    error_message = e.response.text

                if status == 404:
                    raise ProviderError(
                        f"Model '{self.model}' not found in Ollama. "
                        f"Pull it first: ollama pull {self.model}"
                    )
                raise ProviderError(f"Ollama API error ({status}): {error_message}")
            raise ProviderError(f"Ollama request failed: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Ollama request failed: {str(e)}")

    def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using Ollama's chat API.

        Args:
            messages: List of chat messages [{'role': 'user', 'content': '...'}]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Dict with chat response and token usage
        """
        for message in messages:
            if "content" in message:
                self.validate_input(message["content"])

        headers = {"Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        if "top_p" in kwargs:
            payload["options"]["top_p"] = kwargs["top_p"]

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("message", {}).get("content", "")

            prompt_text = " ".join(msg.get("content", "") for msg in messages)
            prompt_tokens = data.get("prompt_eval_count", self.estimate_tokens(prompt_text, model_family="ollama"))
            completion_tokens = data.get("eval_count", self.estimate_tokens(content, model_family="ollama"))
            total_tokens = prompt_tokens + completion_tokens

            return {
                "response": content,
                "tokens_used": total_tokens,
                "finish_reason": "stop",
                "model": data.get("model", self.model),
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
                "messages": messages,
            }

        except requests.ConnectionError:
            raise ProviderError(
                "Cannot connect to Ollama server. "
                f"Ensure Ollama is running at {self.base_url}\n"
                "Install: https://ollama.com  |  Start: ollama serve"
            )
        except requests.Timeout:
            raise ProviderError(f"Ollama chat request timed out after 120s (model: {self.model})")
        except requests.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                status = e.response.status_code
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("error", e.response.text)
                except Exception:
                    error_message = e.response.text

                if status == 404:
                    raise ProviderError(
                        f"Model '{self.model}' not found in Ollama. "
                        f"Pull it first: ollama pull {self.model}"
                    )
                raise ProviderError(f"Ollama API error ({status}): {error_message}")
            raise ProviderError(f"Ollama chat request failed: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Ollama chat request failed: {str(e)}")

    def get_supported_models(self) -> List[str]:
        """
        Get list of commonly-used Ollama models.

        Note: Ollama supports any model from its registry.
        This returns popular defaults for documentation purposes.
        """
        return [
            "llama3.2",
            "llama3.1",
            "mistral",
            "gemma2",
            "phi3",
            "qwen2.5",
            "codellama",
        ]

    def validate_config(self) -> None:
        """
        Validate Ollama configuration.

        Unlike cloud providers, Ollama doesn't require an API key.
        We only verify that the base URL looks reasonable.
        """
        if not self.base_url.startswith(("http://", "https://")):
            raise ProviderError(
                f"Invalid Ollama base URL: {self.base_url}. "
                "Must start with http:// or https://"
            )
