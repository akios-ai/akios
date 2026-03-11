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
AWS Bedrock LLM Provider

Implements the LLMProvider interface for AWS Bedrock.
Supports Anthropic Claude, Meta Llama, and Amazon Titan models
via the Bedrock Runtime invoke_model API.

Authentication uses AWS IAM credentials (AWS_ACCESS_KEY_ID,
AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN) or instance profiles —
no traditional API key required.

Install the optional dependency:
    pip install akios[bedrock]
"""

import json
import os
import time
import logging
from typing import Dict, Any, List

from .base import LLMProvider, ProviderError

logger = logging.getLogger(__name__)

# Retry configuration for throttled requests
_MAX_RETRIES = 3
_BASE_DELAY = 1.0  # seconds

# Lazy boto3 import — only loaded when BedrockProvider is instantiated
try:
    import boto3
    import botocore.exceptions
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    botocore = None
    BOTO3_AVAILABLE = False


# -------------------------------------------------------------------
# Bedrock model catalogue
# -------------------------------------------------------------------

# Default model when none specified
DEFAULT_BEDROCK_MODEL = "anthropic.claude-3-5-haiku-20241022-v1:0"

# Models supported by this provider
SUPPORTED_MODELS = [
    # Anthropic Claude on Bedrock
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    "anthropic.claude-3-opus-20240229-v1:0",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    # Meta Llama on Bedrock
    "meta.llama3-1-8b-instruct-v1:0",
    "meta.llama3-1-70b-instruct-v1:0",
    "meta.llama3-1-405b-instruct-v1:0",
    # Amazon Titan
    "amazon.titan-text-express-v1",
    "amazon.titan-text-lite-v1",
]


class BedrockProvider(LLMProvider):
    """
    AWS Bedrock provider implementation.

    Uses the Bedrock Runtime ``invoke_model`` API with IAM authentication.
    Supports Anthropic Claude, Meta Llama, and Amazon Titan model families.

    Environment variables:
        AKIOS_BEDROCK_MODEL_ID   – Override the model ID
        AKIOS_BEDROCK_REGION     – AWS region (default: us-east-1)
        AWS_ACCESS_KEY_ID        – IAM access key
        AWS_SECRET_ACCESS_KEY    – IAM secret key
        AWS_SESSION_TOKEN        – Optional session token
    """

    def __init__(self, api_key: str = "", model: str = DEFAULT_BEDROCK_MODEL, **kwargs):
        # Bedrock uses IAM auth, not API keys.  We pass an empty string to
        # satisfy the base-class signature, then override validate_config().
        super().__init__(api_key or "", model, **kwargs)

        if not BOTO3_AVAILABLE:
            raise ProviderError(
                "AWS Bedrock provider requires boto3. "
                "Install with: pip install akios[bedrock]"
            )

        # Allow env-var overrides for model and region
        self.model = os.getenv("AKIOS_BEDROCK_MODEL_ID", model)
        self.region = os.getenv("AKIOS_BEDROCK_REGION", "us-east-1")

        # Validate model is in the supported catalogue
        if self.model not in SUPPORTED_MODELS:
            raise ProviderError(
                f"Unsupported Bedrock model: {self.model}. "
                f"Supported: {SUPPORTED_MODELS}"
            )

        # Determine the model family once for request/response formatting
        self._model_family = self._detect_model_family(self.model)

        # Build the Bedrock Runtime client
        try:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
            )
        except Exception as e:
            raise ProviderError(f"Failed to create Bedrock client: {e}")

    # ----- helpers -------------------------------------------------------

    @staticmethod
    def _detect_model_family(model_id: str) -> str:
        """Return 'anthropic', 'meta', or 'amazon' based on model ID prefix."""
        if model_id.startswith("anthropic."):
            return "anthropic"
        if model_id.startswith("meta."):
            return "meta"
        if model_id.startswith("amazon."):
            return "amazon"
        return "unknown"

    def _build_request_body(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Build the JSON request body appropriate for the model family."""

        if self._model_family == "anthropic":
            # Anthropic Messages API envelope for Bedrock
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
        elif self._model_family == "meta":
            # Llama models use a simple prompt format
            prompt = self._messages_to_prompt(messages)
            body = {
                "prompt": prompt,
                "max_gen_len": max_tokens,
                "temperature": temperature,
            }
        elif self._model_family == "amazon":
            # Amazon Titan text models
            prompt = self._messages_to_prompt(messages)
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                },
            }
        else:
            raise ProviderError(f"Unsupported model family for: {self.model}")

        return json.dumps(body)

    @staticmethod
    def _messages_to_prompt(messages: List[Dict[str, str]]) -> str:
        """Convert a chat-messages list into a flat prompt string."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"System: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
            else:
                parts.append(f"User: {content}")
        return "\n\n".join(parts)

    def _parse_response(self, response_body: dict) -> tuple:
        """
        Parse the Bedrock response body according to model family.

        Returns:
            (content_text, prompt_tokens, completion_tokens)
        """
        if self._model_family == "anthropic":
            content = ""
            if "content" in response_body and response_body["content"]:
                for block in response_body["content"]:
                    if block.get("type") == "text":
                        content += block.get("text", "")
            usage = response_body.get("usage", {})
            prompt_tokens = usage.get("input_tokens", 0)
            completion_tokens = usage.get("output_tokens", 0)
            return content, prompt_tokens, completion_tokens

        elif self._model_family == "meta":
            content = response_body.get("generation", "")
            prompt_tokens = response_body.get("prompt_token_count", 0)
            completion_tokens = response_body.get("generation_token_count", 0)
            return content, prompt_tokens, completion_tokens

        elif self._model_family == "amazon":
            results = response_body.get("results", [{}])
            content = results[0].get("outputText", "") if results else ""
            # Titan reports token counts at the top level
            prompt_tokens = response_body.get("inputTextTokenCount", 0)
            completion_tokens = response_body.get("results", [{}])[0].get("tokenCount", 0) if results else 0
            return content, prompt_tokens, completion_tokens

        return "", 0, 0

    def _get_stop_reason(self, response_body: dict) -> str:
        """Extract the stop/finish reason from the response."""
        if self._model_family == "anthropic":
            return response_body.get("stop_reason", "end_turn")
        elif self._model_family == "meta":
            return response_body.get("stop_reason", "stop")
        elif self._model_family == "amazon":
            results = response_body.get("results", [{}])
            return results[0].get("completionReason", "FINISH") if results else "FINISH"
        return "stop"

    # ----- LLMProvider interface -----------------------------------------

    def validate_config(self) -> None:
        """
        Validate Bedrock configuration.

        Overrides the base class to skip API-key validation — Bedrock
        authenticates via IAM credentials resolved by the boto3 credential
        chain (env vars, instance profile, SSO, etc.).
        """
        # Do NOT call super().validate_config() — it would reject empty api_key
        if self.model not in SUPPORTED_MODELS:
            raise ProviderError(f"Unsupported Bedrock model: {self.model}")

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate completion using AWS Bedrock invoke_model.

        Args:
            prompt: Text prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters (ignored)

        Returns:
            Dict with completion results and token usage
        """
        self.validate_input(prompt)

        messages = [{"role": "user", "content": prompt}]
        request_body = self._build_request_body(messages, max_tokens, temperature)

        last_error = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = self.client.invoke_model(
                    modelId=self.model,
                    contentType="application/json",
                    accept="application/json",
                    body=request_body,
                )

                response_body = json.loads(response["body"].read())
                content, prompt_tokens, completion_tokens = self._parse_response(response_body)
                total_tokens = prompt_tokens + completion_tokens

                # Fall back to estimation if the model didn't return counts
                if total_tokens == 0:
                    prompt_tokens = self.estimate_tokens(prompt, model_family="claude")
                    completion_tokens = self.estimate_tokens(content, model_family="claude")
                    total_tokens = prompt_tokens + completion_tokens
                    estimated = True
                else:
                    estimated = False

                return {
                    "text": content,
                    "tokens_used": total_tokens,
                    "finish_reason": self._get_stop_reason(response_body),
                    "model": self.model,
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "estimated": estimated,
                    },
                }

            except botocore.exceptions.ClientError as e:
                error_code = e.response["Error"]["Code"]
                error_msg = e.response["Error"]["Message"]
                if error_code == "AccessDeniedException":
                    raise ProviderError(
                        f"Bedrock access denied: {error_msg}. "
                        "Ensure your IAM role has bedrock:InvokeModel permission."
                    )
                if error_code == "ThrottlingException":
                    last_error = e
                    if attempt < _MAX_RETRIES:
                        delay = _BASE_DELAY * (2 ** attempt)
                        logger.warning(f"Bedrock throttled (attempt {attempt + 1}/{_MAX_RETRIES + 1}), retrying in {delay:.1f}s")
                        time.sleep(delay)
                        continue
                    raise ProviderError(f"Bedrock rate limit exceeded after {_MAX_RETRIES + 1} attempts: {error_msg}")
                raise ProviderError(f"Bedrock API error ({error_code}): {error_msg}")
            except Exception as e:
                err_type = type(e).__name__
                # Credential/auth errors — clear message, no retry
                if err_type in ('NoCredentialsError', 'PartialCredentialsError'):
                    raise ProviderError(
                        f"AWS credentials not found or incomplete: {e}. "
                        "Set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY, or configure an IAM role."
                    )
                if err_type == 'TokenRetrievalError':
                    raise ProviderError(
                        f"AWS STS token expired or retrieval failed: {e}. "
                        "Refresh your session credentials or use long-term IAM credentials."
                    )
                # Connection errors — retry with backoff
                if err_type in ('EndpointConnectionError', 'ConnectionError', 'ConnectTimeoutError'):
                    last_error = e
                    if attempt < _MAX_RETRIES:
                        delay = _BASE_DELAY * (2 ** attempt)
                        logger.warning(f"Bedrock connection error (attempt {attempt + 1}/{_MAX_RETRIES + 1}), retrying in {delay:.1f}s: {e}")
                        time.sleep(delay)
                        continue
                    raise ProviderError(f"Bedrock connection failed after {_MAX_RETRIES + 1} attempts: {e}")
                # All other errors
                raise ProviderError(f"Bedrock request failed: {err_type}: {e}")

    def chat_complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate chat completion using AWS Bedrock invoke_model.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters (ignored)

        Returns:
            Dict with chat response and token usage
        """
        for msg in messages:
            if "content" in msg:
                self.validate_input(msg["content"])

        # For Anthropic models, extract system message if present
        anthropic_messages = []
        system_prompt = None
        if self._model_family == "anthropic":
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content", "")
                else:
                    anthropic_messages.append(msg)
            send_messages = anthropic_messages if anthropic_messages else messages
        else:
            send_messages = messages

        # Build request body
        if self._model_family == "anthropic" and system_prompt:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": send_messages,
            }
            request_body = json.dumps(body)
        else:
            request_body = self._build_request_body(send_messages, max_tokens, temperature)

        try:
            last_error = None
            for attempt in range(_MAX_RETRIES + 1):
                try:
                    response = self.client.invoke_model(
                        modelId=self.model,
                        contentType="application/json",
                        accept="application/json",
                        body=request_body,
                    )

                    response_body = json.loads(response["body"].read())
                    content, prompt_tokens, completion_tokens = self._parse_response(response_body)
                    total_tokens = prompt_tokens + completion_tokens

                    # Fall back to estimation if the model didn't return counts
                    if total_tokens == 0:
                        prompt_text = " ".join(msg.get("content", "") for msg in messages)
                        prompt_tokens = self.estimate_tokens(prompt_text, model_family="claude")
                        completion_tokens = self.estimate_tokens(content, model_family="claude")
                        total_tokens = prompt_tokens + completion_tokens
                        estimated = True
                    else:
                        estimated = False

                    return {
                        "response": content,
                        "tokens_used": total_tokens,
                        "finish_reason": self._get_stop_reason(response_body),
                        "model": self.model,
                        "usage": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                            "estimated": estimated,
                            "messages": messages,
                        },
                    }

                except botocore.exceptions.ClientError as e:
                    error_code = e.response["Error"]["Code"]
                    error_msg = e.response["Error"]["Message"]
                    if error_code == "AccessDeniedException":
                        raise ProviderError(
                            f"Bedrock access denied: {error_msg}. "
                            "Ensure your IAM role has bedrock:InvokeModel permission."
                        )
                    if error_code == "ThrottlingException":
                        last_error = e
                        if attempt < _MAX_RETRIES:
                            delay = _BASE_DELAY * (2 ** attempt)
                            logger.warning(f"Bedrock chat throttled (attempt {attempt + 1}/{_MAX_RETRIES + 1}), retrying in {delay:.1f}s")
                            time.sleep(delay)
                            continue
                        raise ProviderError(f"Bedrock rate limit exceeded after {_MAX_RETRIES + 1} attempts: {error_msg}")
                    raise ProviderError(f"Bedrock chat API error ({error_code}): {error_msg}")
                except Exception as e:
                    err_type = type(e).__name__
                    if err_type in ('NoCredentialsError', 'PartialCredentialsError'):
                        raise ProviderError(
                            f"AWS credentials not found or incomplete: {e}. "
                            "Set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY, or configure an IAM role."
                        )
                    if err_type == 'TokenRetrievalError':
                        raise ProviderError(
                            f"AWS STS token expired or retrieval failed: {e}. "
                            "Refresh your session credentials or use long-term IAM credentials."
                        )
                    if err_type in ('EndpointConnectionError', 'ConnectionError', 'ConnectTimeoutError'):
                        last_error = e
                        if attempt < _MAX_RETRIES:
                            delay = _BASE_DELAY * (2 ** attempt)
                            logger.warning(f"Bedrock chat connection error (attempt {attempt + 1}/{_MAX_RETRIES + 1}), retrying in {delay:.1f}s: {e}")
                            time.sleep(delay)
                            continue
                        raise ProviderError(f"Bedrock connection failed after {_MAX_RETRIES + 1} attempts: {e}")
                    raise ProviderError(f"Bedrock chat request failed: {err_type}: {e}")
        except ProviderError:
            raise

    def get_supported_models(self) -> List[str]:
        """Get list of supported Bedrock models."""
        return list(SUPPORTED_MODELS)

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "bedrock"
