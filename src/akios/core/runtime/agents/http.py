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
HTTP Agent - HTTP/web service agent with rate limiting + secure requests

Makes HTTP requests while enforcing security and rate limits.
"""

import time
import json
import threading
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import httpx

from .base import BaseAgent, AgentError
# Delay security imports to avoid validation during package import
from akios.core.audit import append_audit_event

# Pre-import PII redaction to avoid import hangs during agent execution
try:
    from akios.security.pii import apply_pii_redaction as _pii_redaction_func
except Exception:
    # Fallback if PII import fails
    _pii_redaction_func = lambda x: x


class HTTPAgent(BaseAgent):
    """
    HTTP agent for making web service calls.

    Enforces rate limits, security checks, and audit logging.
    """

    def __init__(self, timeout: int = 30, max_redirects: int = 5,
                 rate_limit_window: int = 60, max_requests_per_window: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_window = rate_limit_window
        self.max_requests_per_window = max_requests_per_window
        self._rate_limit_lock = threading.Lock()  # Thread-safe rate limiting

    def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute HTTP action.

        Args:
            action: HTTP method ('get', 'post', 'put', 'delete', 'patch')
            parameters: Request parameters

        Returns:
            HTTP response data
        """
        self.validate_parameters(action, parameters)

        # Apply security before making network calls (delayed import)
        from akios.security import enforce_sandbox, apply_pii_redaction
        from akios.security.syscall.policy import AgentType
        enforce_sandbox(agent_type=AgentType.HTTP)

        # Check network access is allowed
        if not self.settings.network_access_allowed:
            # MANAGED ACCESS: Check allowlist if global access is disabled
            allowed = False
            request_host = urlparse(parameters.get('url', '')).netloc
            
            if self.settings.allowed_domains:
                for domain in self.settings.allowed_domains:
                    if domain == request_host or request_host.endswith('.' + domain):
                        allowed = True
                        break
            
            if not allowed:
                raise AgentError(
                    f"Network access denied. Host '{request_host}' is not in allowed_domains. "
                    f"Enable AKIOS_NETWORK_ACCESS_ALLOWED=true or add to AKIOS_ALLOWED_DOMAINS."
                )

        # Check rate limits
        self._check_rate_limits()

        # Validate and prepare request
        url = parameters.get('url', '')
        headers = parameters.get('headers', {})
        data = parameters.get('data', {})
        params = parameters.get('params', {})
        auth_params = parameters.get('auth')  # Basic auth tuple (username, password) or auth object

        # Redact PII from request data
        if isinstance(data, str):
            original_data = data
            data = apply_pii_redaction(data)
            if data != original_data:
                # Log PII redaction event
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'http',
                    'action': 'pii_redaction',
                    'result': 'success',
                    'metadata': {
                        'field': 'data',
                        'original_length': len(original_data),
                        'redacted_length': len(data)
                    }
                })
        elif isinstance(data, dict):
            original_data = data.copy()
            data = {k: apply_pii_redaction(str(v)) if isinstance(v, str) else v
                   for k, v in data.items()}
            # Check if any values were redacted
            if any(str(original_data.get(k, '')) != str(data.get(k, '')) for k in data.keys() if isinstance(data[k], str)):
                # Log PII redaction event
                append_audit_event({
                    'workflow_id': parameters.get('workflow_id', 'unknown'),
                    'step': parameters.get('step', 0),
                    'agent': 'http',
                    'action': 'pii_redaction',
                    'result': 'success',
                    'metadata': {
                        'field': 'data_dict',
                        'keys_affected': len([k for k in data.keys() if isinstance(data[k], str) and str(original_data.get(k, '')) != str(data[k])])
                    }
                })

        # Execute the request
        start_time = time.time()
        workflow_id = parameters.get('workflow_id', 'unknown')
        step = parameters.get('step', 0)
        result = self._execute_request(action, url, headers, data, params, auth_params, workflow_id, step)
        execution_time = time.time() - start_time

        # Update rate limiting (thread-safe)
        with self._rate_limit_lock:
            self.request_count += 1
            self.last_request_time = time.time()

        # Audit the request
        append_audit_event({
            'workflow_id': workflow_id,
            'step': step,
            'agent': 'http',
            'action': action,
            'result': 'success' if result.get('status_code', 0) < 400 else 'error',
            'metadata': {
                'url': self._sanitize_url(url),
                'method': action.upper(),
                'status_code': result.get('status_code'),
                'response_size': len(result.get('content', '')),
                'execution_time': execution_time,
                'rate_limited': False
            }
        })

        return result

    def _execute_request(self, method: str, url: str, headers: Dict[str, str],
                        data: Any, params: Dict[str, Any], auth_params: Any = None,
                        workflow_id: str = 'unknown', step: int = 0) -> Dict[str, Any]:
        """Execute the HTTP request using httpx"""
        try:
            import httpx

            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise AgentError(f"Invalid URL: {url}")

            # Prepare request data
            request_kwargs = {
                'url': url,
                'headers': headers or {},
                'params': params or {},
                'timeout': self.timeout
            }

            # Add authentication if provided
            if auth_params:
                if isinstance(auth_params, tuple) and len(auth_params) == 2:
                    # Basic auth tuple (username, password)
                    request_kwargs['auth'] = httpx.BasicAuth(auth_params[0], auth_params[1])
                else:
                    # Assume it's already a proper auth object
                    request_kwargs['auth'] = auth_params

            # Add data based on content type
            if data:
                if isinstance(data, dict):
                    request_kwargs['json'] = data
                else:
                    request_kwargs['content'] = str(data)

            # Make the request based on method
            # Configure redirects on the client
            with httpx.Client(follow_redirects=True, max_redirects=self.max_redirects) as client:
                if method.upper() == 'GET':
                    response = client.get(**request_kwargs)
                elif method.upper() == 'POST':
                    response = client.post(**request_kwargs)
                elif method.upper() == 'PUT':
                    response = client.put(**request_kwargs)
                elif method.upper() == 'DELETE':
                    response = client.delete(**request_kwargs)
                elif method.upper() == 'PATCH':
                    response = client.patch(**request_kwargs)
                else:
                    raise AgentError(f"Unsupported HTTP method: {method}")

                # Parse response
                response_content = response.text
                response_headers = dict(response.headers)

                # Apply PII redaction to response content and headers
                apply_pii_redaction = _pii_redaction_func

                original_content = response_content
                response_content = apply_pii_redaction(response_content)

                # Redact sensitive header values (but keep header names)
                redacted_headers = {}
                for header_name, header_value in response_headers.items():
                    redacted_headers[header_name] = apply_pii_redaction(str(header_value))

                # Audit PII redaction in response
                content_redacted = response_content != original_content
                headers_redacted = any(
                    str(original_value) != redacted_value
                    for original_value, redacted_value in zip(response_headers.values(), redacted_headers.values())
                )

                if content_redacted or headers_redacted:
                    append_audit_event({
                        'workflow_id': workflow_id,
                        'step': step,
                        'agent': 'http',
                        'action': 'pii_redaction_output',
                        'result': 'success',
                        'metadata': {
                            'content_redacted': content_redacted,
                            'headers_redacted': headers_redacted,
                            'response_size': len(response_content)
                        }
                    })

                try:
                    json_content = response.json()
                    # Also redact JSON content
                    json_str = json.dumps(json_content)
                    redacted_json_str = apply_pii_redaction(json_str)
                    if redacted_json_str != json_str:
                        json_content = json.loads(redacted_json_str)

                    return {
                        'status_code': response.status_code,
                        'content': response_content,
                        'json': json_content,
                        'headers': redacted_headers,
                        'url': str(response.url)
                    }
                except Exception:
                    return {
                        'status_code': response.status_code,
                        'content': response_content,
                        'text': response_content,
                        'headers': redacted_headers,
                        'url': str(response.url)
                    }

        except ImportError:
            raise AgentError("httpx library not available for HTTP requests")
        except Exception as e:
            raise AgentError(f"HTTP request failed: {e}") from e

    def _check_rate_limits(self) -> None:
        """Check and enforce rate limits (thread-safe)"""
        with self._rate_limit_lock:
            current_time = time.time()

            # Reset counter if window has passed
            if current_time - self.last_request_time > self.rate_limit_window:
                self.request_count = 0

            if self.request_count >= self.max_requests_per_window:
                raise AgentError(f"Rate limit exceeded: {self.max_requests_per_window} requests per {self.rate_limit_window}s")

    def reset_rate_limits(self) -> None:
        """Reset rate limiting counters (for testing) - thread-safe"""
        with self._rate_limit_lock:
            self.request_count = 0
            self.last_request_time = 0

    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL for audit logging (remove sensitive parts)"""
        # Remove API keys from query parameters
        parsed = urlparse(url)
        query_params = parsed.query

        # Simple sanitization - remove common sensitive parameter names
        sensitive_params = ['key', 'token', 'secret', 'password', 'api_key']
        sanitized_params = []

        if query_params:
            for param in query_params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key.lower() in sensitive_params:
                        sanitized_params.append(f"{key}=[REDACTED]")
                    else:
                        sanitized_params.append(param)
                else:
                    sanitized_params.append(param)

            sanitized_query = '&'.join(sanitized_params)
        else:
            sanitized_query = query_params

        # Reconstruct URL
        return parsed._replace(query=sanitized_query).geturl()

    def validate_parameters(self, action: str, parameters: Dict[str, Any]) -> None:
        """Validate HTTP action parameters"""
        if 'url' not in parameters:
            raise AgentError("HTTP requests require 'url' parameter")

        url = parameters['url']
        if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
            raise AgentError("URL must be a valid HTTP/HTTPS URL")

        # Validate method
        valid_methods = ['get', 'post', 'put', 'delete', 'patch']
        if action.lower() not in valid_methods:
            raise AgentError(f"Invalid HTTP method: {action}. Must be one of: {valid_methods}")

    def get_supported_actions(self) -> List[str]:
        """Get supported HTTP methods"""
        return ['get', 'post', 'put', 'delete', 'patch']

    @property
    def current_rate_stats(self) -> Dict[str, Any]:
        """Get current rate limiting statistics"""
        return {
            'requests_this_window': self.request_count,
            'window_start': self.last_request_time,
            'max_per_window': self.max_requests_per_window,
            'window_seconds': self.rate_limit_window
        }
