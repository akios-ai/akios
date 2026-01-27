"""
Google Gemini LLM Provider

Implements the LLMProvider interface for Google's Gemini API.
Supports Gemini models with real token counting and error handling.
"""

from typing import Dict, Any, List
from .base import LLMProvider, ProviderError

# Lazy import to avoid issues when library not installed
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider implementation.

    Supports Gemini 1.5 Pro, Gemini 1.5 Flash, and Gemini 1.0 Pro models.
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", **kwargs):
        super().__init__(api_key, model, **kwargs)

        # Check if Gemini library is available
        if not GEMINI_AVAILABLE:
            raise ProviderError("Gemini provider requires 'google-generativeai' library. Install with: pip install google-generativeai")

        # Validate API key format (Google API keys are typically long alphanumeric)
        if len(api_key) < 20:
            raise ProviderError("Invalid Gemini API key format - Google API keys should be longer")

        # Validate model support
        allowed_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro"
        ]

        if model not in allowed_models:
            raise ProviderError(f"Unsupported Gemini model: {model}. Supported: {allowed_models}")

        # Initialize Google AI client
        try:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model_name=model)
        except Exception as e:
            raise ProviderError(f"Failed to initialize Gemini client: {str(e)}")

    def complete(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate completion using Gemini API.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Gemini parameters

        Returns:
            Dict with completion results
        """
        # Validate input for safety and size limits
        self.validate_input(prompt)

        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **kwargs
            )

            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Extract response text
            text = response.text if hasattr(response, 'text') else str(response)

            # Estimate token usage using tiktoken (Gemini uses similar tokenization to GPT)
            prompt_tokens = self.estimate_tokens(prompt, model_family="gpt")
            completion_tokens = self.estimate_tokens(text, model_family="gpt")
            tokens_used = prompt_tokens + completion_tokens

            return {
                "text": text,
                "tokens_used": tokens_used,
                "finish_reason": "completed",
                "model": self.model,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": tokens_used
                }
            }

        except Exception as e:
            error_str = str(e).lower()
            if "api_key" in error_str or "authentication" in error_str:
                raise ProviderError("Invalid Gemini API key")
            elif "quota" in error_str or "rate" in error_str:
                raise ProviderError("Gemini API quota exceeded")
            elif "safety" in error_str or "blocked" in error_str:
                raise ProviderError("Content blocked by Gemini safety filters")
            else:
                raise ProviderError(f"Gemini API request failed: {str(e)}")

    def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using Gemini API.

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

        try:
            # Convert messages to Gemini format
            gemini_messages = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')

                # Gemini uses 'model' for assistant messages
                if role == 'assistant':
                    role = 'model'

                gemini_messages.append({
                    "role": role,
                    "parts": [content]
                })

            # Start chat session
            chat = self.client.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])

            # Send the last message
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""

            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                **kwargs
            )

            response = chat.send_message(
                last_message,
                generation_config=generation_config
            )

            # Extract response
            text = response.text if hasattr(response, 'text') else str(response)

            # Estimate token usage using tiktoken
            prompt_text = " ".join([msg.get('content', '') for msg in messages])
            prompt_tokens = self.estimate_tokens(prompt_text, model_family="gpt")
            completion_tokens = self.estimate_tokens(text, model_family="gpt")
            tokens_used = prompt_tokens + completion_tokens

            return {
                "response": text,
                "tokens_used": tokens_used,
                "finish_reason": "completed",
                "model": self.model,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": tokens_used
                }
            }

        except Exception as e:
            error_str = str(e).lower()
            if "api_key" in error_str or "authentication" in error_str:
                raise ProviderError("Invalid Gemini API key")
            elif "quota" in error_str or "rate" in error_str:
                raise ProviderError("Gemini API quota exceeded")
            elif "safety" in error_str or "blocked" in error_str:
                raise ProviderError("Content blocked by Gemini safety filters")
            else:
                raise ProviderError(f"Gemini API request failed: {str(e)}")

    def validate_config(self) -> None:
        """Validate provider configuration by making a small test request."""
        try:
            # Make a minimal completion request to validate API key
            self.complete("test", max_tokens=1)
        except ProviderError:
            raise  # Re-raise provider errors
        except Exception as e:
            raise ProviderError(f"Gemini configuration validation failed: {str(e)}")

    def estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost for token usage.

        Gemini pricing (approximate):
        - gemini-1.0-pro: $0.0005 per 1K characters (roughly $0.0015 per 1K tokens)
        - gemini-1.5-pro: $0.00125 per 1K characters (roughly $0.00375 per 1K tokens)
        - gemini-1.5-flash: $0.000075 per 1K characters (roughly $0.000225 per 1K tokens)
        """
        # Gemini pricing is per character, but we estimate based on tokens
        # Rough conversion: 1 token ≈ 3-4 characters
        pricing = {
            "gemini-1.0-pro": 0.0015,      # $0.0015 per 1K tokens
            "gemini-1.5-pro": 0.00375,     # $0.00375 per 1K tokens
            "gemini-1.5-flash": 0.000225   # $0.000225 per 1K tokens
        }

        cost_per_1k = pricing.get(self.model, 0.000225)  # Default to flash pricing
        return (tokens / 1000) * cost_per_1k
