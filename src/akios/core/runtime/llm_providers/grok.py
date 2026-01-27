"""
Grok/xAI LLM Provider

Implements the LLMProvider interface for Grok API (xAI).
Supports Grok models with real token counting.
"""

import requests
from typing import Dict, Any, List
from .base import LLMProvider, ProviderError


class GrokProvider(LLMProvider):
    """
    Grok provider implementation for xAI's Grok models.

    Supports Grok-4.1, Grok-4, and Grok-3 family models.
    """

    def __init__(self, api_key: str, model: str = "grok-3", **kwargs):
        super().__init__(api_key, model, **kwargs)

        # Validate API key format
        if not api_key.startswith('xai-'):
            raise ProviderError("Grok API key should start with 'xai-'")

        # Validate model support
        allowed_models = [
            "grok-4.1-fast",
            "grok-4.1",
            "grok-3"
        ]

        if model not in allowed_models:
            raise ProviderError(f"Unsupported Grok model: {model}. Supported: {allowed_models}")

        # Set API endpoint
        self.base_url = "https://api.x.ai/v1"

    def _filter_model_parameters(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter parameters based on what the current model supports.

        Different Grok models have different parameter support:
        - grok-4: Limited parameter support (no presencePenalty, frequencyPenalty)
        - grok-3: Full parameter support
        - grok-4.1*: Full parameter support
        """
        # Define supported parameters for each model family
        # Based on Grok API documentation and testing
        model_param_support = {
            "grok-4.1-fast": {"top_p", "frequencyPenalty", "presencePenalty"},
            "grok-4.1": {"top_p", "frequencyPenalty", "presencePenalty"},
            "grok-3": {"top_p", "frequencyPenalty", "presencePenalty"}
        }

        # Get supported parameters for current model
        supported_params = model_param_support.get(self.model, {"top_p"})

        # Filter kwargs to only include supported parameters
        filtered = {}
        for param, value in kwargs.items():
            # Convert snake_case to camelCase for Grok API
            if param == "top_p":
                filtered[param] = value
            elif param == "frequency_penalty" and "frequencyPenalty" in supported_params:
                filtered["frequencyPenalty"] = value
            elif param == "presence_penalty" and "presencePenalty" in supported_params:
                filtered["presencePenalty"] = value

        return filtered

    def complete(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion using Grok API.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Grok parameters

        Returns:
            Dict with completion results and token usage
        """
        # Validate input for safety and size limits
        self.validate_input(prompt)

        # Filter parameters based on model capabilities
        filtered_kwargs = self._filter_model_parameters(kwargs)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **filtered_kwargs
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # Extract response data
            choice = data['choices'][0]
            usage = data.get('usage', {})

            return {
                'text': choice['message']['content'],
                'tokens_used': usage.get('total_tokens', self.estimate_tokens(prompt + choice['message']['content'], model_family="grok")),
                'finish_reason': choice.get('finish_reason', 'stop'),
                'model': data.get('model', self.model),
                'usage': usage or {
                    'prompt_tokens': self.estimate_tokens(prompt, model_family="grok"),
                    'completion_tokens': self.estimate_tokens(choice['message']['content'], model_family="grok"),
                    'total_tokens': self.estimate_tokens(prompt + choice['message']['content'], model_family="grok")
                }
            }

        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                # Parse error message from response JSON
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error', e.response.text)
                except:
                    error_message = e.response.text

                if e.response.status_code == 400:
                    raise ProviderError(f"Grok API error: {error_message}")
                elif e.response.status_code == 401:
                    raise ProviderError(f"Grok authentication failed: {error_message}")
                elif e.response.status_code == 429:
                    raise ProviderError(f"Grok rate limit exceeded: {error_message}")
                elif e.response.status_code >= 500:
                    raise ProviderError(f"Grok server error: {e.response.status_code} - {error_message}")
                else:
                    raise ProviderError(f"Grok API error ({e.response.status_code}): {error_message}")
            else:
                raise ProviderError(f"Grok request failed: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Grok request failed: {str(e)}")

    def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using Grok API.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Grok parameters

        Returns:
            Dict with chat response and token usage
        """
        # Validate all message contents for safety and size limits
        for message in messages:
            if 'content' in message:
                self.validate_input(message['content'])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # Extract response data
            choice = data['choices'][0]
            usage = data.get('usage', {})

            # Estimate token usage if not provided
            prompt_text = " ".join([msg.get('content', '') for msg in messages])
            if not usage:
                response_text = choice['message']['content']
                usage = {
                    'prompt_tokens': self.estimate_tokens(prompt_text, model_family="grok"),
                    'completion_tokens': self.estimate_tokens(response_text, model_family="grok"),
                    'total_tokens': self.estimate_tokens(prompt_text + response_text, model_family="grok")
                }

            return {
                'response': choice['message']['content'],
                'tokens_used': usage.get('total_tokens', self.estimate_tokens(prompt_text + choice['message']['content'], model_family="grok")),
                'finish_reason': choice.get('finish_reason', 'stop'),
                'model': data.get('model', self.model),
                'usage': usage,
                'messages': messages  # Include for audit logging
            }

        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                # Parse error message from response JSON
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error', e.response.text)
                except:
                    error_message = e.response.text

                if e.response.status_code == 400:
                    raise ProviderError(f"Grok API error: {error_message}")
                elif e.response.status_code == 401:
                    raise ProviderError(f"Grok authentication failed: {error_message}")
                elif e.response.status_code == 429:
                    raise ProviderError(f"Grok rate limit exceeded: {error_message}")
                elif e.response.status_code >= 500:
                    raise ProviderError(f"Grok server error: {e.response.status_code} - {error_message}")
                else:
                    raise ProviderError(f"Grok API error ({e.response.status_code}): {error_message}")
            else:
                raise ProviderError(f"Grok chat request failed: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Grok chat request failed: {str(e)}")

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported Grok models.

        Returns:
            List of supported model names
        """
        return [
            "grok-4.1-fast",
            "grok-4.1",
            "grok-4",
            "grok-3"
        ]

    def validate_config(self) -> None:
        """
        Validate Grok-specific configuration.
        """
        super().validate_config()

        # Additional validation for Grok
        if not self.model.startswith('grok-'):
            raise ProviderError(f"Invalid Grok model format: {self.model}")

        # Test API key format (basic validation)
        if not self.api_key.startswith('xai-'):
            raise ProviderError("Grok API key should start with 'xai-'")
