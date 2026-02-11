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
LLM Agent - LLM call agent with token counting + cost kill hook

Makes LLM API calls while tracking token usage and enforcing cost limits.
"""

import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from .base import BaseAgent, AgentError
# Module-level import for test patching and consistent access
from akios.config import get_settings
# Delay security imports to avoid validation during package import
from akios.core.audit import append_audit_event

# Allow tests to patch OpenAI even if provider is abstracted
try:
    from openai import OpenAI
except Exception:  # pragma: no cover - fallback for environments without openai
    OpenAI = None

# Pre-import PII redaction to avoid import hangs during agent execution
try:
    from akios.security.pii import apply_pii_redaction as _pii_redaction_func
except Exception:
    # Fallback if PII import fails
    _pii_redaction_func = lambda x: x


class LLMAgent(BaseAgent):
    """
    LLM agent for making API calls to language models.

    Tracks token usage and enforces cost kill-switches.
    """

    def __init__(self, provider: str = "openai", model: Optional[str] = None, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)

        # Ensure configuration is loaded (loads .env if present)
        settings = get_settings()

        # Check for mock fallback FIRST - bypasses all validation
        # Use settings object to ensure .env is loaded and parsed correctly
        self.use_mock = settings.mock_llm

        if self.use_mock:
            # Mock mode - no validation, no API key required
            # Brief confirmation (detailed messaging handled at workflow level)
            pass
            self.provider_name = "mock"
            self.model = "mock-model"
            self.api_key = "mock-key"
            # Initialize with mock provider
            self.provider = None
            self.api_available = True
            self.session_tokens = 0
            self.session_cost = 0.0
            return

        # Real mode - check environment variable overrides first
        settings = get_settings()

        # Environment variable overrides (highest priority)
        env_provider = os.getenv('AKIOS_LLM_PROVIDER')
        env_model = os.getenv('AKIOS_LLM_MODEL')

        # Use env vars if set, otherwise use config values, otherwise use defaults
        self.provider_name = env_provider or provider or "openai"
        self.model = env_model or model or self._get_default_model(self.provider_name)

        # Validate provider against config allowlist
        if self.provider_name not in settings.allowed_providers:
            raise AgentError(f"Unsupported provider: {self.provider_name}. Allowed: {settings.allowed_providers}")

        # Real mode - require actual API key (unless mock mode)

        # Get API key for the provider (auto-detect if not provided)
        self.api_key = api_key or self._get_api_key_for_provider(self.provider_name)

        # Validate we have an API key
        if not self.api_key:
            required_var = self._get_required_env_var(self.provider_name)
            provider_name, api_url = self._get_provider_info(self.provider_name)
            raise AgentError(
                f"🤖 AKIOS v1.0 requires a real {provider_name} API key for AI workflows.\n\n"
                f"🚀 Quick Setup:\n"
                f"1. Visit: {api_url}\n"
                f"2. Create an API key\n"
                f"3. Set: export {required_var}='your-key-here'\n"
                f"4. Run your workflow again\n\n"
                f"💡 For testing only: Set AKIOS_MOCK_LLM=1 (not recommended for production)"
            )

        # Initialize provider instance
        self.provider = None
        self.api_available = False

        try:
            self.provider = self._create_provider(self.provider_name, self.api_key, self.model)
            # Validate provider configuration
            self.provider.validate_config()
            self.api_available = True
        except Exception as e:
            # Provider creation failed - this is a hard error now
            raise AgentError(f"LLM Provider initialization failed: {str(e)}")

        # Initialize session tracking for cost and token monitoring
        self.session_tokens = 0
        self.session_cost = 0.0

    def _get_default_model(self, provider: str) -> str:
        """Get default model for a provider"""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3.5-haiku",
            "grok": "grok-3",
            "mistral": "mistral-small",
            "gemini": "gemini-1.5-flash"
        }
        return defaults.get(provider, "gpt-4o-mini")

    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider"""
        import os

        # Provider-specific environment variables
        key_mapping = {
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "grok": ["GROK_API_KEY"],
            "mistral": ["MISTRAL_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
        }

        env_vars = key_mapping.get(provider, [])
        for env_var in env_vars:
            key = os.getenv(env_var)
            if key:
                return key

        return None

    def _get_required_env_var(self, provider: str) -> str:
        """Get required env var name for provider"""
        mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "grok": "GROK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "gemini": "GEMINI_API_KEY"
        }
        return mapping.get(provider, f"{provider.upper()}_API_KEY")

    def _get_provider_info(self, provider: str) -> tuple[str, str]:
        """Get provider display name and API key URL"""
        info = {
            "openai": ("OpenAI", "https://platform.openai.com/api-keys"),
            "anthropic": ("Anthropic", "https://console.anthropic.com/"),
            "grok": ("Grok/xAI", "https://console.x.ai/"),
            "mistral": ("Mistral AI", "https://console.mistral.ai/"),
            "gemini": ("Google Gemini", "https://makersuite.google.com/app/apikey")
        }
        return info.get(provider, (provider.title(), f"https://{provider}.com"))

    def _create_provider(self, provider_name: str, api_key: str, model: str):
        """Create provider instance with lazy imports"""
        try:
            if provider_name == "openai":
                from akios.core.runtime.llm_providers.openai import OpenAIProvider
                return OpenAIProvider(api_key, model)
            elif provider_name == "anthropic":
                from akios.core.runtime.llm_providers.anthropic import AnthropicProvider
                return AnthropicProvider(api_key, model)
            elif provider_name == "grok":
                from akios.core.runtime.llm_providers.grok import GrokProvider
                return GrokProvider(api_key, model)
            elif provider_name == "mistral":
                from akios.core.runtime.llm_providers.mistral import MistralProvider
                return MistralProvider(api_key, model)
            elif provider_name == "gemini":
                try:
                    from akios.core.runtime.llm_providers.gemini import GeminiProvider
                    return GeminiProvider(api_key, model)
                except ImportError:
                    raise AgentError("Gemini provider requires 'google-generativeai' library. Install with: pip install google-generativeai")
            else:
                raise AgentError(f"Unsupported provider: {provider_name}")
        except ImportError as e:
            raise AgentError(f"Provider library not available: {str(e)}")
        except Exception as e:
            raise AgentError(f"Provider initialization failed: {str(e)}")

    def _ensure_api_available(self) -> None:
        """Ensure API is available, raise AgentError if not"""
        if not self.api_available or not self.provider:
            # NO MOCK FALLBACK IN PRODUCTION - EVER
            required_var = self._get_required_env_var(self.provider_name)
            provider_name, api_url = self._get_provider_info(self.provider_name)
            raise AgentError(
                f"🤖 AKIOS v1.0 requires a real {provider_name} API key for AI workflows.\n\n"
                f"🚀 Quick Setup (choose one):\n"
                f"• Guided wizard: Run 'akios setup'\n"
                f"• Manual setup:\n"
                f"  1. Visit: {api_url}\n"
                f"  2. Create an API key\n"
                f"  3. Set: export {required_var}='your-key-here'\n"
                f"  4. Run your workflow again\n\n"
                f"💡 For testing only: Set AKIOS_MOCK_LLM=1 (not recommended for production)"
            )

    def _get_api_key(self) -> str:
        """Get API key from environment or config"""
        import os

        # Check environment variable first
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key

        # In a real implementation, this would get from secure config
        # For testing, raise an informative error
        raise AgentError(
            "OpenAI API key not found. Set OPENAI_API_KEY environment variable or run 'akios setup' to configure. "
            "Get a key from https://platform.openai.com/api-keys"
        )

    def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LLM action.

        Args:
            action: Action to perform ('generate', 'complete', 'chat')
            parameters: Action parameters

        Returns:
            Action result
        """
        self.validate_parameters(action, parameters)

        # Apply security before making any external calls (delayed import)
        from akios.security import enforce_sandbox
        from akios.security.syscall.policy import AgentType
        enforce_sandbox(agent_type=AgentType.LLM)

        # Use pre-imported PII redaction function
        enterprise_pii_redaction = _pii_redaction_func

        # Apply PII redaction to input prompts
        if 'prompt' in parameters:
            original_prompt = parameters['prompt']

            # Ensure prompt is a string
            if not isinstance(original_prompt, str):
                original_prompt = str(original_prompt)
                parameters['prompt'] = original_prompt

            # Log debug info
            append_audit_event({
                'workflow_id': parameters.get('workflow_id', 'unknown'),
                'step': parameters.get('step', 0),
                'agent': 'llm',
                'action': 'pii_debug',
                'result': 'info',
                'metadata': {
                    'prompt_type': type(original_prompt).__name__,
                    'prompt_length': len(original_prompt),
                    'has_template_subs': '{' in original_prompt and '}' in original_prompt
                }
            })

            try:
                parameters['prompt'] = enterprise_pii_redaction(parameters['prompt'])
            except Exception as e:
                # Fallback: Comprehensive regex-based redaction if library fails
                import re
                try:
                    # Comprehensive PII redaction covering all major types
                    original_prompt = parameters['prompt']

                    # Email addresses
                    parameters['prompt'] = re.sub(
                        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                        '[EMAIL_REDACTED]',
                        parameters['prompt']
                    )

                    # Phone numbers (US format)
                    parameters['prompt'] = re.sub(
                        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                        '[PHONE_REDACTED]',
                        parameters['prompt']
                    )

                    # Social Security Numbers
                    parameters['prompt'] = re.sub(
                        r'\b\d{3}-\d{2}-\d{4}\b',
                        '[SSN_REDACTED]',
                        parameters['prompt']
                    )

                    # Credit card numbers (basic pattern)
                    parameters['prompt'] = re.sub(
                        r'\b(?:\d{4}[ -]?){3}\d{4}\b',
                        '[CC_REDACTED]',
                        parameters['prompt']
                    )

                    fallback_applied = parameters['prompt'] != original_prompt
                except Exception:
                    fallback_applied = False

                # Log PII redaction failure
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'llm',
                    'action': 'pii_input_failure',
                    'result': 'warning',
                    'metadata': {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'fallback_applied': fallback_applied,
                        'prompt_sample': str(parameters['prompt'])[:200]
                    }
                })
            if parameters['prompt'] != original_prompt:
                # Log PII redaction event
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'llm',
                    'action': 'pii_redaction',
                    'result': 'success',
                    'metadata': {
                        'field': 'prompt',
                        'original_length': len(original_prompt),
                        'redacted_length': len(parameters['prompt'])
                    }
                })

        if 'messages' in parameters:
            # Redact each message
            for i, msg in enumerate(parameters['messages']):
                if 'content' in msg:
                    original_content = msg['content']
                    msg['content'] = enterprise_pii_redaction(msg['content'])
                    if msg['content'] != original_content:
                        # Log PII redaction event
                        append_audit_event({
                            'workflow_id': parameters.get('workflow_id', 'unknown'),
                            'step': parameters.get('step', 0),
                            'agent': 'llm',
                            'action': 'pii_redaction',
                            'result': 'success',
                            'metadata': {
                                'field': f'message_{i}',
                                'original_length': len(original_content),
                                'redacted_length': len(msg['content'])
                            }
                        })

        # Check cost limits before proceeding
        self._check_cost_limits(parameters)

        # Execute the action
        start_time = time.time()
        result = self._execute_action(action, parameters)
        execution_time = time.time() - start_time

        # Track usage
        tokens_used = result.get('tokens_used', 0)
        self.session_tokens += tokens_used
        cost_incurred = self._calculate_cost(tokens_used)
        self.session_cost += cost_incurred

        # Apply PII redaction to LLM output before returning
        try:
            result = self._apply_output_pii_filtering(result, parameters)
        except Exception as e:
            # If PII filtering fails, log error but don't break the workflow
            # This ensures security filtering never prevents successful operation
            append_audit_event({
                'workflow_id': parameters.get('workflow_id', 'unknown'),
                'step': parameters.get('step', 0),
                'agent': 'llm',
                'action': 'pii_output_filtering_error',
                'result': 'warning',
                'metadata': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            })

        # Add cost data to result for template access (rounded for clean display)
        result['cost_incurred'] = round(cost_incurred, 6)

        # Add processing timestamp for template access
        result['processing_timestamp'] = datetime.now(timezone.utc).isoformat()

        # Audit the action with mock mode warning if applicable
        audit_metadata = {
            'model': self.model,
            'tokens_used': tokens_used,
            'cost_incurred': cost_incurred,
            'execution_time': execution_time,
            'session_tokens': self.session_tokens,
            'session_cost': self.session_cost
        }

        if self.use_mock:
            audit_metadata['warning'] = 'MOCK_MODE_USED: This workflow used simulated AI responses, not real API calls. Disable AKIOS_MOCK_LLM for production use.'

        append_audit_event({
            'workflow_id': parameters.get('workflow_id', 'unknown'),
            'step': parameters.get('step', 0),
            'agent': 'llm',
            'action': action,
            'result': 'success',
            'metadata': audit_metadata
        })

        return result

    def _apply_output_pii_filtering(self, result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply PII filtering to LLM output before returning to user.

        Args:
            result: Raw LLM result from _execute_action
            parameters: Original execution parameters

        Returns:
            Result with PII-filtered output
        """
        # Check if PII output filtering is enabled
        if not self._is_output_pii_filtering_enabled():
            return result

        # Extract the text content from the result
        output_text = self._extract_output_text(result)
        if not output_text:
            return result

        # Apply PII filtering
        try:
            from akios.security.pii.output_filter import filter_llm_output

            context = {
                'workflow_id': parameters.get('workflow_id'),
                'agent': 'llm',
                'model': self.model,
                'action': parameters.get('action', 'complete')
            }

            # Get aggressive mode setting
            aggressive = self._get_aggressive_pii_mode()

            filtered_result = filter_llm_output(output_text, context, aggressive)

            # Update result with filtered text
            result = self._update_result_with_filtered_output(result, filtered_result)

            # Add PII filtering metadata to audit
            if filtered_result.get('redactions_applied', 0) > 0:
                self._log_pii_filtering_audit(filtered_result, parameters)

        except Exception as e:
            # If PII filtering fails, log error but don't break the workflow
            # This ensures security filtering never prevents successful operation
            try:
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'llm',
                    'action': 'pii_output_filter_error',
                    'result': 'warning',
                    'metadata': {
                        'error': str(e),
                        'filter_failed': True,
                        'output_protected': False
                    }
                })
            except Exception:
                # If even audit logging fails, silently continue
                pass

        return result

    def _is_output_pii_filtering_enabled(self) -> bool:
        """
        Check if PII output filtering is enabled in configuration.

        Returns:
            True if output filtering should be applied
        """
        try:
            from akios.config import get_settings
            settings = get_settings()
            # Check for pii_redaction.outputs setting (default to True for security)
            return getattr(settings, 'pii_redaction_outputs', True)
        except Exception:
            # Default to enabled for security
            return True

    def _get_aggressive_pii_mode(self) -> bool:
        """
        Get aggressive PII filtering mode setting.

        Returns:
            True if aggressive filtering should be used
        """
        try:
            from akios.config import get_settings
            settings = get_settings()
            return getattr(settings, 'pii_redaction_aggressive', False)
        except Exception:
            return False

    def _extract_output_text(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Extract text content from LLM result for filtering.

        Args:
            result: LLM execution result

        Returns:
            Text content to filter, or None if no text found
        """
        # Check common result fields for text content
        text_fields = ['content', 'text', 'response', 'output', 'result']

        for field in text_fields:
            if field in result and isinstance(result[field], str):
                return result[field]

        # Check for nested content (e.g., in choices array from OpenAI)
        if 'choices' in result and isinstance(result['choices'], list):
            for choice in result['choices']:
                if isinstance(choice, dict):
                    if 'message' in choice and 'content' in choice['message']:
                        return choice['message']['content']
                    elif 'text' in choice:
                        return choice['text']

        return None

    def _update_result_with_filtered_output(self, result: Dict[str, Any],
                                          filtered_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the result with filtered output text.

        Args:
            result: Original LLM result
            filtered_result: PII filtering result

        Returns:
            Updated result with filtered content
        """
        filtered_text = filtered_result['filtered_text']

        # Update the original text field in result
        text_fields = ['content', 'text', 'response', 'output', 'result']

        for field in text_fields:
            if field in result and isinstance(result[field], str):
                result[field] = filtered_text
                break

        # Handle nested content (e.g., OpenAI choices)
        if 'choices' in result and isinstance(result['choices'], list):
            for choice in result['choices']:
                if isinstance(choice, dict):
                    if 'message' in choice and 'content' in choice['message']:
                        choice['message']['content'] = filtered_text
                        break
                    elif 'text' in choice:
                        choice['text'] = filtered_text
                        break

        # Add PII filtering metadata to result
        result['pii_filtering_applied'] = True
        result['pii_redactions_applied'] = filtered_result.get('redactions_applied', 0)
        result['pii_patterns_found'] = filtered_result.get('patterns_found', [])

        return result

    def _log_pii_filtering_audit(self, filtered_result: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        """
        Log PII filtering actions to audit trail.

        Args:
            filtered_result: Result from PII filtering
            parameters: Original execution parameters
        """
        try:
            append_audit_event({
                'workflow_id': parameters.get('workflow_id', 'unknown'),
                'step': parameters.get('step', 0),
                'agent': 'llm',
                'action': 'pii_output_filtered',
                'result': 'success',
                'metadata': {
                    'redactions_applied': filtered_result.get('redactions_applied', 0),
                    'patterns_found': filtered_result.get('patterns_found', []),
                    'aggressive_mode': filtered_result.get('aggressive_mode', False),
                    'output_protected': True
                }
            })
        except Exception:
            # Audit logging should not break workflow execution
            pass

    def _execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the specific LLM action"""
        if action == 'generate':
            return self._generate_text(parameters)
        elif action == 'complete':
            return self._complete_text(parameters)
        elif action == 'chat':
            return self._chat_completion(parameters)
        else:
            raise AgentError(f"Unsupported LLM action: {action}")

    def _generate_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text using real LLM provider or mock responses"""
        if self.use_mock:
            # Mock mode - return simulated response
            prompt = params.get('prompt', '')
            max_tokens = params.get('max_tokens', 1000)

            # Generate mock response based on prompt content
            mock_response = self._generate_mock_response(prompt, max_tokens)
            tokens_used = min(len(mock_response.split()) * 2, max_tokens)
            cost_incurred = self._calculate_cost(tokens_used)

            return {
                'text': mock_response,
                'tokens_used': tokens_used,
                'model': 'mock-model',
                'cost_incurred': round(cost_incurred, 6),
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'finish_reason': 'completed'
            }

        # Real LLM API call
        # LLM agent always has network access to its configured provider APIs.
        # The security cage protects data (PII redaction, audit, budget limits),
        # it does not block AI orchestration calls. The network_access_allowed
        # setting controls the HTTP agent for arbitrary web requests only.
        # Provider must still be in allowed_providers list (validated at init).

        self._ensure_api_available()

        prompt = params.get('prompt', '')
        max_tokens = params.get('max_tokens', 1000)

        # Real LLM API call - single consolidated implementation
        try:
            # Extract parameters for the provider call
            temperature = params.get('temperature', 0.7)
            top_p = params.get('top_p', 1.0)
            frequency_penalty = params.get('frequency_penalty', 0.0)
            presence_penalty = params.get('presence_penalty', 0.0)

            # Call provider with all supported parameters
            # Only allow known LLM API parameters to prevent passing internal data
            allowed_params = {'top_p', 'frequency_penalty', 'presence_penalty'}
            api_params = {k: v for k, v in params.items() if k in allowed_params}
            result = self.provider.complete(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                **api_params
            )

            # Add metadata fields for template access (same as mock responses)
            tokens_used = result.get('tokens_used', 0)
            cost_incurred = self._calculate_cost(tokens_used)

            # Return in standardized format + metadata
            return {
                'text': result.get('text', ''),
                'tokens_used': tokens_used,
                'model': result.get('model', self.model),
                'finish_reason': result.get('finish_reason', 'unknown'),
                'cost_incurred': round(cost_incurred, 6),
                'processing_timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            raise AgentError(f"LLM API call failed: {str(e)}")

    def _complete_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Complete partial text using real provider"""
        # For completion, we'll use the same logic as generate_text
        # but return in the expected format
        result = self._generate_text(params)

        # Add metadata fields for template access (same as mock responses)
        tokens_used = result.get('tokens_used', 0)
        cost_incurred = self._calculate_cost(tokens_used)

        return {
            'text': result['text'],  # FIXED: Use 'text' key for template substitution compatibility
            'tokens_used': tokens_used,
            'model': result.get('model', self.model),
            'cost_incurred': round(cost_incurred, 6),
            'processing_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _chat_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat-style completion using real LLM provider or mock"""
        if self.use_mock:
            # Mock chat response
            messages = params.get('messages', [])
            max_tokens = params.get('max_tokens', 1000)

            # Extract last user message for context
            last_message = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    last_message = msg.get('content', '')
                    break

            mock_response = self._generate_mock_response(last_message, max_tokens)
            tokens_used = min(len(mock_response.split()) * 2, max_tokens)
            cost_incurred = self._calculate_cost(tokens_used)

            return {
                'completion': mock_response,
                'tokens_used': tokens_used,
                'model': 'mock-model',
                'cost_incurred': round(cost_incurred, 6),
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'finish_reason': 'completed'
            }

        # Real chat completion
        self._ensure_api_available()

        messages = params.get('messages', [])
        max_tokens = params.get('max_tokens', 1000)

        # Real LLM API call
        try:
            return self.provider.chat_complete(messages, max_tokens=max_tokens, **params)
        except Exception as e:
            raise AgentError(f"LLM API call failed: {str(e)}")

        # Use real provider
        temperature = params.get('temperature', 0.7)

        try:
            result = self.provider.chat_complete(messages, max_tokens, temperature)

            # Add metadata fields for template access (same as mock responses)
            tokens_used = result.get('tokens_used', 0)
            cost_incurred = self._calculate_cost(tokens_used)

            # Return in format expected by existing code + metadata
            return {
                'response': result['response'],
                'tokens_used': tokens_used,
                'model': result.get('model', self.model),
                'usage': result.get('usage', {}),
                'cost_incurred': round(cost_incurred, 6),
                'processing_timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            raise AgentError(f"Chat completion failed: {str(e)}")

    def _check_cost_limits(self, params: Dict[str, Any]) -> None:
        """Check if this request would exceed cost limits"""
        # Estimate token usage
        estimated_tokens = self._estimate_tokens(params)

        estimated_cost = self._calculate_cost(estimated_tokens)

        # Enhanced cost checking with more detailed validation
        budget_limit = self.settings.budget_limit_per_run
        current_session_cost = self.session_cost
        projected_total_cost = current_session_cost + estimated_cost

        # Check if cost kill switch is enabled
        if not self.settings.cost_kill_enabled:
            # Log warning but allow execution
            print(f"⚠️  Warning: Cost controls disabled. Estimated cost: ${estimated_cost:.6f}", file=__import__('sys').stderr)
            return

        # Validate budget limit is reasonable (not extremely low for testing)
        if budget_limit < 0.00001:  # Cost validation works consistently in both mock and real modes
            print(f"⚠️  Warning: Very low budget limit (${budget_limit:.6f}) detected. "
                  f"Estimated cost: ${estimated_cost:.6f}.", file=__import__('sys').stderr)

        # Main cost limit check
        if projected_total_cost > budget_limit:
            raise AgentError(f"Cost limit exceeded. Session cost: ${current_session_cost:.6f}, "
                           f"Estimated additional: ${estimated_cost:.6f}, "
                           f"Projected total: ${projected_total_cost:.6f}, "
                           f"Limit: ${budget_limit:.6f}")

        if estimated_tokens > self.settings.max_tokens_per_call:
            raise AgentError(f"Token limit exceeded. Estimated: {estimated_tokens}, "
                           f"Limit: {self.settings.max_tokens_per_call}")

    def _estimate_tokens(self, params: Dict[str, Any]) -> int:
        """Estimate token usage for a request using accurate tokenization"""
        text_content = ""

        if 'prompt' in params:
            text_content += params['prompt']
        if 'messages' in params:
            for msg in params['messages']:
                text_content += msg.get('content', '')

        # Use tiktoken for accurate token counting (required for production)
        try:
            import tiktoken
        except ImportError:
            raise AgentError("tiktoken library required for accurate token counting. Install with: pip install tiktoken")

        # Use appropriate encoding based on provider and model
        try:
            if self.provider_name == 'openai':
                # Use model-specific encoding for OpenAI
                if 'gpt-4' in self.model:
                    encoding = tiktoken.encoding_for_model("gpt-4")
                elif 'gpt-3.5' in self.model:
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                else:
                    # Default to GPT-3.5-turbo encoding
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            elif self.provider_name == 'anthropic':
                # Claude uses similar tokenization to GPT, use cl100k_base
                encoding = tiktoken.get_encoding("cl100k_base")
            elif self.provider_name in ['grok', 'mistral', 'gemini']:
                # These providers use similar tokenization, use cl100k_base as approximation
                encoding = tiktoken.get_encoding("cl100k_base")
            else:
                # Fallback encoding
                encoding = tiktoken.get_encoding("cl100k_base")

            token_count = len(encoding.encode(text_content))
            return max(10, token_count)

        except Exception as e:
            # If tokenization fails, provide a reasonable estimate
            # Rough approximation: ~1 token per 4 characters for English text
            char_count = len(text_content)
            estimated_tokens = max(10, char_count // 4)
            # Log the fallback but don't fail
            import logging
            logging.warning(f"Token estimation using fallback for {self.provider_name}/{self.model}: {estimated_tokens} tokens (error: {e})")
            return estimated_tokens

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate cost for token usage"""
        # No cost in mock mode
        if self.use_mock:
            return 0.0

        pricing = {
            "openai": {
                "gpt-4o-mini": 0.00015,  # $0.00015 per 1K tokens
                "gpt-4o": 0.005,         # $0.005 per 1K tokens
                "gpt-4-turbo": 0.01,     # $0.01 per 1K tokens
                "gpt-4": 0.03            # $0.03 per 1K tokens
            },
            "anthropic": {
                "claude-3.5-haiku": 0.00025,  # $0.00025 per 1K tokens
                "claude-3.5-sonnet": 0.003,   # $0.003 per 1K tokens
                "claude-3-opus": 0.015        # $0.015 per 1K tokens
            },
            "grok": {
                "grok-4.1-fast": 0.006,  # Estimated $0.006 per 1K tokens
                "grok-4.1": 0.008,       # Estimated $0.008 per 1K tokens
                "grok-4": 0.012,         # Estimated $0.012 per 1K tokens
                "grok-3": 0.005          # Estimated $0.005 per 1K tokens
            },
            "mistral": {
                "mistral-small": 0.20,     # $0.20 per 1K tokens
                "mistral-medium": 0.27,    # $0.27 per 1K tokens
                "mistral-large": 0.40      # $0.40 per 1K tokens
            },
            "gemini": {
                "gemini-1.5-flash": 0.000225,  # $0.000225 per 1K tokens
                "gemini-1.5-pro": 0.00375,     # $0.00375 per 1K tokens
                "gemini-1.0-pro": 0.0015       # $0.0015 per 1K tokens
            }
        }

        # Get pricing for current provider/model
        provider_pricing = pricing.get(self.provider_name, {})
        cost_per_1k = provider_pricing.get(self.model, 0.002)  # Default fallback

        return (tokens / 1000) * cost_per_1k

    def validate_parameters(self, action: str, parameters: Dict[str, Any]) -> None:
        """Validate action parameters"""
        if action in ['generate', 'complete']:
            if 'prompt' not in parameters:
                raise AgentError("LLM actions require 'prompt' parameter")
        elif action == 'chat':
            if 'messages' not in parameters:
                raise AgentError("Chat action requires 'messages' parameter")

    def get_supported_actions(self) -> List[str]:
        """Get supported actions"""
        return ['generate', 'complete', 'chat']

    def _generate_mock_response(self, prompt: str, max_tokens: int) -> str:
        """Generate a realistic mock response for testing"""
        prompt_lower = prompt.lower()

        # Check if JSON structure is requested (for file analysis)
        if 'output only valid json' in prompt_lower and ('summary' in prompt_lower or 'patterns_found' in prompt_lower):
            # Generate structured JSON response for file analysis
            import json

            mock_analysis = {
                "summary": "Mock analysis: File contains business document with contact and financial information. Entropy level suggests normal text content with moderate complexity.",
                "patterns_found": "Emails: 1 (redacted for privacy), IPs: 0, URLs: 0, Credit Cards: 0, Numbers: 12 (including financial figures), Dates: 2 (Q4 2025 references)",
                "threat_level": "Low - Mock assessment indicates standard business document with no immediate security concerns",
                "recommendations": "Mock recommendations: Verify email context for business legitimacy, ensure file permissions restrict unauthorized access, consider encryption for sensitive financial data, monitor for unusual access patterns"
            }

            # Add mock disclaimer
            mock_analysis["_mock_disclaimer"] = "This is a FAKE AI response generated by AKIOS for testing purposes only. No real API was called."

            return json.dumps(mock_analysis, indent=2)

        # All other mock responses clearly indicate they are demo responses
        mock_header = """🎭 ════════════════════════════════════════════════════════════════════════════════
🎭                              MOCK MODE RESPONSE
🎭 ════════════════════════════════════════════════════════════════════════════════
🎭 This is a SIMULATED AI response for safe testing
🎭 • NO real AI API was called
🎭 • NO costs incurred
🎭 • NO external network connections
🎭 • Results are for testing AKIOS security features only
🎭
🎭 For real AI responses: Add API keys to .env and set AKIOS_MOCK_LLM=0
🎭 ════════════════════════════════════════════════════════════════════════════════

"""

        if 'analyze' in prompt_lower and 'document' in prompt_lower:
            response = mock_header + "FAKE ANALYSIS: This document appears to be a technical specification containing approximately 2,500 words. Key topics include system architecture, security protocols, and implementation guidelines. The document demonstrates good structure with clear sections on requirements, design, and testing procedures."
        elif 'summarize' in prompt_lower:
            response = mock_header + "FAKE SUMMARY: The provided content discusses advanced topics in AI workflow execution, focusing on security, sandboxing, and multi-provider integration. Key points include kernel-level isolation, cryptographic audit trails, and production-ready templates for common use cases."
        elif 'enrich' in prompt_lower:
            response = mock_header + "FAKE ENRICHMENT: The input data has been processed and enhanced with additional context. This appears to be a UUID-based identifier with potential applications in distributed systems, session management, or secure token generation. Recommended next steps include validation against known patterns and integration with existing authentication frameworks."
        elif 'hello' in prompt_lower or 'greet' in prompt_lower:
            response = mock_header + "Hello! This is a sample greeting from AKIOS demo mode. No real AI API was called - this is safe testing with no costs. To experience creative AI greetings, add your API keys to the .env file!"
        else:
            response = mock_header + "This is a sample AI response from AKIOS demo mode. The system is working correctly with full security and sandboxing - you're seeing safe test data with no external API calls or costs."

        # Truncate to approximate token limit
        words = response.split()
        if len(words) > max_tokens // 2:  # Rough approximation
            response = ' '.join(words[:max_tokens // 2]) + "..."

        return response

    @property
    def current_session_usage(self) -> Dict[str, Any]:
        """Get current session usage statistics"""
        return {
            'tokens': self.session_tokens,
            'cost': self.session_cost,
            'model': self.model
        }
