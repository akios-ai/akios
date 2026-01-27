"""
Anthropic LLM Provider

Implements the LLMProvider interface for Anthropic's Claude API.
Supports Claude models with estimated token counting.
"""

import anthropic
from typing import Dict, Any, List
from .base import LLMProvider, ProviderError

# Try to import Anthropic's token counting (optional)
try:
    import anthropic_tokenizer
    ANTHROPIC_TOKENIZER_AVAILABLE = True
except ImportError:
    ANTHROPIC_TOKENIZER_AVAILABLE = False


class AnthropicProvider(LLMProvider):
    """
    Anthropic provider implementation for Claude models.

    Supports Claude 3.5 Opus, Sonnet, and Haiku models.
    """

    def __init__(self, api_key: str, model: str = "claude-3.5-haiku", **kwargs):
        super().__init__(api_key, model, **kwargs)

        # Validate API key format
        if not api_key.startswith('sk-ant-'):
            raise ProviderError("Anthropic API key should start with 'sk-ant-'")

        # Validate model support
        allowed_models = [
            "claude-3.5-haiku",
            "claude-3.5-sonnet",
            "claude-3-opus"
        ]

        if model not in allowed_models:
            raise ProviderError(f"Unsupported Anthropic model: {model}. Supported: {allowed_models}")

        # Initialize Anthropic client
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            raise ProviderError(f"Failed to initialize Anthropic client: {str(e)}")

    def complete(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion using Anthropic Claude API.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Anthropic parameters

        Returns:
            Dict with completion results and estimated token usage
        """
        # Validate input for safety and size limits
        self.validate_input(prompt)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0,  # 30 second timeout for consistency
                **kwargs
            )

            # Extract response data
            content = response.content[0].text if response.content else ""

            # Estimate token usage (Anthropic doesn't provide exact counts)
            prompt_tokens_est = self.estimate_tokens(prompt, model_family="claude")
            completion_tokens_est = self.estimate_tokens(content, model_family="claude")
            total_tokens_est = prompt_tokens_est + completion_tokens_est

            return {
                'text': content,
                'tokens_used': total_tokens_est,
                'finish_reason': response.stop_reason or 'stop',
                'model': response.model,
                'usage': {
                    'prompt_tokens': prompt_tokens_est,
                    'completion_tokens': completion_tokens_est,
                    'total_tokens': total_tokens_est,
                    'estimated': True  # Mark as estimated
                }
            }

        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic API error: {str(e)}")
        except anthropic.AuthenticationError as e:
            raise ProviderError(f"Anthropic authentication failed: {str(e)}")
        except anthropic.RateLimitError as e:
            raise ProviderError(f"Anthropic rate limit exceeded: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Anthropic request failed: {str(e)}")

    def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using Anthropic Claude API.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Anthropic parameters

        Returns:
            Dict with chat response and estimated token usage
        """
        # Validate all message contents for safety and size limits
        for message in messages:
            if 'content' in message:
                self.validate_input(message['content'])

        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')

                # Anthropic uses 'assistant' instead of 'system' for system messages
                if role == 'system':
                    # Prepend system message to first user message
                    if anthropic_messages and anthropic_messages[0]['role'] == 'user':
                        anthropic_messages[0]['content'] = f"System: {content}\n\n{anthropic_messages[0]['content']}"
                    else:
                        anthropic_messages.insert(0, {"role": "user", "content": f"System: {content}"})
                else:
                    anthropic_messages.append({"role": role, "content": content})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=anthropic_messages,
                timeout=30.0,  # 30 second timeout for consistency
                **kwargs
            )

            # Extract response data
            content = response.content[0].text if response.content else ""

            # Estimate token usage for all messages
            prompt_text = " ".join([msg.get('content', '') for msg in messages])
            prompt_tokens_est = self.estimate_tokens(prompt_text, model_family="claude")
            completion_tokens_est = self.estimate_tokens(content, model_family="claude")
            total_tokens_est = prompt_tokens_est + completion_tokens_est

            return {
                'response': content,
                'tokens_used': total_tokens_est,
                'finish_reason': response.stop_reason or 'stop',
                'model': response.model,
                'usage': {
                    'prompt_tokens': prompt_tokens_est,
                    'completion_tokens': completion_tokens_est,
                    'total_tokens': total_tokens_est,
                    'estimated': True,
                    'messages': messages  # Include for audit logging
                }
            }

        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic chat API error: {str(e)}")
        except anthropic.AuthenticationError as e:
            raise ProviderError(f"Anthropic authentication failed: {str(e)}")
        except anthropic.RateLimitError as e:
            raise ProviderError(f"Anthropic rate limit exceeded: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Anthropic chat request failed: {str(e)}")

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported Anthropic models.

        Returns:
            List of supported model names
        """
        return [
            "claude-3.5-haiku",
            "claude-3.5-sonnet",
            "claude-3-opus"
        ]

    def validate_config(self) -> None:
        """
        Validate Anthropic-specific configuration.
        """
        super().validate_config()

        # Additional validation for Anthropic
        if not self.model.startswith('claude-'):
            raise ProviderError(f"Invalid Anthropic model format: {self.model}")

        # Test API key format (basic validation)
        if not self.api_key.startswith('sk-ant-'):
            raise ProviderError("Anthropic API key should start with 'sk-ant-'")
