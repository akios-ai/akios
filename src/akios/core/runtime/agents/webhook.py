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
Webhook Agent — Send notifications to Slack, Discord, Teams, or generic webhooks.

Added in v1.1.0. Built on the same security patterns as HTTPAgent:
PII redaction, HTTPS enforcement, rate limiting, and audit logging.
"""

import json
import logging
import os
import time
import threading
from typing import Any, Dict, List
from urllib.parse import urlparse

from .base import BaseAgent, AgentError
from akios.core.audit import append_audit_event

try:
    from akios.security.pii import apply_pii_redaction
except Exception:
    import logging as _logging
    _logging.getLogger(__name__).critical(
        "PII redaction module failed to import — all content will be masked"
    )
    apply_pii_redaction = lambda x: "[PII_REDACTION_UNAVAILABLE]"

logger = logging.getLogger(__name__)

# Platform-specific payload builders
PLATFORM_BUILDERS = {}


def _build_slack_payload(message: str, channel: str = None,
                         username: str = None, **kwargs) -> Dict[str, Any]:
    payload = {"text": message}
    if channel:
        payload["channel"] = channel
    if username:
        payload["username"] = username
    return payload


def _build_discord_payload(message: str, username: str = None, **kwargs) -> Dict[str, Any]:
    payload = {"content": message}
    if username:
        payload["username"] = username
    return payload


def _build_teams_payload(message: str, **kwargs) -> Dict[str, Any]:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": message[:50],
        "text": message,
    }


def _build_generic_payload(message: str, **kwargs) -> Dict[str, Any]:
    return {"message": message, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


PLATFORM_BUILDERS = {
    "slack": _build_slack_payload,
    "discord": _build_discord_payload,
    "teams": _build_teams_payload,
    "generic": _build_generic_payload,
}


class WebhookAgent(BaseAgent):
    """
    Webhook agent for sending notifications to external services.

    Supports Slack, Discord, Microsoft Teams, and generic HTTP POST webhooks.
    All messages are PII-redacted before sending.
    """

    def __init__(self, webhook_url: str = None, platform: str = "generic",
                 timeout: int = 10, rate_limit_window: int = 60,
                 max_requests_per_window: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.webhook_url = webhook_url
        self.platform = platform.lower() if platform else "generic"
        self.timeout = min(timeout, 30)
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_window = rate_limit_window
        self.max_requests_per_window = max_requests_per_window
        self._rate_limit_lock = threading.Lock()

    def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_parameters(action, parameters)

        # Resolve webhook URL from parameters, config, or env
        url = self._resolve_webhook_url(parameters)

        # HTTPS enforcement
        parsed = urlparse(url)
        if parsed.scheme != "https" and self.settings.sandbox_enabled:
            raise AgentError(
                f"HTTPS required: plain HTTP webhooks are blocked when the security cage is active. "
                f"Use https:// for '{url}'"
            )

        # Rate limiting
        self._check_rate_limits()

        # Get message and redact PII
        message = parameters.get("message", "")
        original_message = message
        message = apply_pii_redaction(str(message))

        # Log PII redaction if content changed
        workflow_id = parameters.get("workflow_id", "unknown")
        step = parameters.get("step", 0)
        if message != original_message:
            append_audit_event({
                "workflow_id": workflow_id,
                "step": step,
                "agent": "webhook",
                "action": "pii_redaction",
                "result": "success",
                "metadata": {
                    "field": "message",
                    "original_length": len(original_message),
                    "redacted_length": len(message),
                },
            })

        # Check mock mode
        if os.getenv("AKIOS_MOCK_LLM") == "1":
            return self._mock_response(action, url, message, workflow_id, step)

        # Build platform-specific payload
        builder = PLATFORM_BUILDERS.get(self.platform, _build_generic_payload)
        payload = builder(
            message=message,
            channel=parameters.get("channel"),
            username=parameters.get("username"),
        )

        # Send webhook
        start_time = time.time()
        result = self._send_webhook(url, payload, workflow_id, step)
        execution_time = time.time() - start_time

        # Update rate limiter
        with self._rate_limit_lock:
            self.request_count += 1
            self.last_request_time = time.time()

        # Audit
        append_audit_event({
            "workflow_id": workflow_id,
            "step": step,
            "agent": "webhook",
            "action": action,
            "result": "success" if result.get("status_code", 0) < 400 else "error",
            "metadata": {
                "platform": self.platform,
                "status_code": result.get("status_code"),
                "execution_time": execution_time,
            },
        })

        return result

    def _resolve_webhook_url(self, parameters: Dict[str, Any]) -> str:
        url = parameters.get("webhook_url") or self.webhook_url
        if not url:
            raise AgentError(
                "Webhook URL required. Set in config.webhook_url, parameters.webhook_url, "
                "or AKIOS_WEBHOOK_URL environment variable."
            )
        return url

    def _send_webhook(self, url: str, payload: Dict[str, Any],
                      workflow_id: str, step: int) -> Dict[str, Any]:
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                return {
                    "status_code": response.status_code,
                    "content": response.text[:500],
                    "platform": self.platform,
                    "delivered": response.status_code < 400,
                }
        except ImportError:
            raise AgentError("httpx library required for webhook requests")
        except Exception as e:
            raise AgentError(f"Webhook delivery failed: {e}") from e

    def _mock_response(self, action: str, url: str, message: str,
                       workflow_id: str, step: int) -> Dict[str, Any]:
        logger.info("MOCK MODE: Simulating webhook %s to %s", action, self.platform)
        append_audit_event({
            "workflow_id": workflow_id,
            "step": step,
            "agent": "webhook",
            "action": action,
            "result": "success",
            "metadata": {"mock": True, "platform": self.platform},
        })
        return {
            "status_code": 200,
            "content": "ok",
            "platform": self.platform,
            "delivered": True,
            "mock": True,
        }

    def _check_rate_limits(self) -> None:
        with self._rate_limit_lock:
            current_time = time.time()
            if current_time - self.last_request_time > self.rate_limit_window:
                self.request_count = 0
            if self.request_count >= self.max_requests_per_window:
                raise AgentError(
                    f"Webhook rate limit exceeded: {self.max_requests_per_window} "
                    f"requests per {self.rate_limit_window}s"
                )

    def validate_parameters(self, action: str, parameters: Dict[str, Any]) -> None:
        if action not in self.get_supported_actions():
            raise AgentError(f"Unsupported webhook action: {action}. Use: {self.get_supported_actions()}")
        if "message" not in parameters:
            raise AgentError("Webhook requires 'message' parameter")

    def get_supported_actions(self) -> List[str]:
        return ["notify", "send"]
