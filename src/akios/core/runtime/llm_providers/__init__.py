"""
LLM Providers Package

Provides unified interface for multiple LLM providers (OpenAI, Anthropic, Grok, Mistral, Gemini, etc.)
with lazy loading to avoid import errors for unavailable providers.
"""

from .base import LLMProvider, ProviderError

# Lazy loading functions to avoid import errors for unavailable providers
def __getattr__(name):
    """Lazy import of providers to avoid import errors for unavailable libraries."""
    if name == 'OpenAIProvider':
        from .openai import OpenAIProvider
        return OpenAIProvider
    elif name == 'AnthropicProvider':
        from .anthropic import AnthropicProvider
        return AnthropicProvider
    elif name == 'GrokProvider':
        from .grok import GrokProvider
        return GrokProvider
    elif name == 'MistralProvider':
        from .mistral import MistralProvider
        return MistralProvider
    elif name == 'GeminiProvider':
        try:
            from .gemini import GeminiProvider
            return GeminiProvider
        except ImportError:
            raise ImportError("Gemini provider requires 'google-generativeai' library. Install with: pip install google-generativeai")
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'LLMProvider',
    'ProviderError',
    'OpenAIProvider',
    'AnthropicProvider',
    'GrokProvider',
    'MistralProvider',
    'GeminiProvider'
]
