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
