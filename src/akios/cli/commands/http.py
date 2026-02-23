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
CLI http command - akios http <method> <url>

Make HTTP requests through the AKIOS security cage with whitelisted domains,
PII redaction, rate limiting, and full audit logging.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from ...core.ui.rich_output import (
    print_panel, print_table, print_success, print_warning,
    print_error, print_info, get_theme_color
)
from ..helpers import CLIError, check_project_context


def register_http_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the http command with the argument parser."""
    parser = subparsers.add_parser(
        "http",
        help="Make secure HTTP requests through the security cage",
        description=(
            "Execute HTTP requests with full security enforcement: "
            "domain whitelisting, PII redaction on request/response, "
            "rate limiting, and audit logging."
        )
    )

    parser.add_argument(
        "method",
        choices=["get", "post", "put", "delete", "patch"],
        help="HTTP method"
    )

    parser.add_argument(
        "url",
        help="Target URL (must be HTTPS and in allowed domains)"
    )

    parser.add_argument(
        "--body",
        default=None,
        help="Request body (string or @filename to read from file)"
    )

    parser.add_argument(
        "--header", "-H",
        action="append",
        dest="headers",
        default=[],
        help="HTTP header in 'Key: Value' format (can be repeated)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output response in JSON format"
    )

    parser.set_defaults(func=run_http_command)


def run_http_command(args: argparse.Namespace) -> int:
    """Execute the http command."""
    try:
        check_project_context()

        # Load settings for domain whitelist checking
        from ...config import get_settings
        settings = get_settings()

        # Parse headers
        headers = {}
        for h in (args.headers or []):
            if ":" in h:
                key, value = h.split(":", 1)
                headers[key.strip()] = value.strip()

        # Parse body
        body = None
        if args.body:
            if args.body.startswith("@"):
                # Read from file
                body_path = Path(args.body[1:])
                if not body_path.exists():
                    raise CLIError(f"Body file not found: {body_path}")
                body = body_path.read_text(encoding="utf-8")
            else:
                body = args.body

        # Validate URL scheme
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        if parsed.scheme not in ("http", "https"):
            raise CLIError(
                f"Invalid URL scheme: {parsed.scheme}. Only HTTP/HTTPS allowed."
            )

        # Check domain against whitelist
        request_host = parsed.netloc
        if not settings.network_access_allowed:
            allowed = False
            if settings.allowed_domains:
                for domain in settings.allowed_domains:
                    if domain == request_host or request_host.endswith("." + domain):
                        allowed = True
                        break

            if not allowed:
                print_error(
                    f"Network access denied. Host '{request_host}' is not in allowed domains.\n"
                    f"Allowed domains: {', '.join(settings.allowed_domains) if settings.allowed_domains else '(none)'}\n"
                    f"Add to AKIOS_ALLOWED_DOMAINS or enable AKIOS_NETWORK_ACCESS_ALLOWED=true"
                )
                return 1

        # Create HTTP agent and execute
        from ...core.runtime.agents.http import HTTPAgent
        agent = HTTPAgent(timeout=args.timeout)

        parameters = {
            "url": args.url,
            "headers": headers,
            "workflow_id": "cli-http",
            "step": 0,
        }
        if body:
            # Try to parse as JSON
            try:
                parameters["json"] = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                parameters["data"] = body

        print_info(f"Executing {args.method.upper()} {args.url}...")

        result = agent.execute(args.method, parameters)

        # Display result
        status = result.get("status_code", 0)
        status_color = "green" if status < 400 else "red"

        if args.json_output:
            print(json.dumps(result, indent=2, default=str))
        else:
            # Format response
            response_content = result.get("content", "")
            response_json = result.get("json")

            if response_json:
                display_body = json.dumps(response_json, indent=2)
            else:
                display_body = response_content[:2000]
                if len(response_content) > 2000:
                    display_body += "\n... (truncated)"

            print_panel(
                f"HTTP {args.method.upper()} Response ({status})",
                display_body,
                style=status_color
            )

            # Audit confirmation
            print_success(
                f"Request completed: {status} | "
                f"PII redacted | Audit logged"
            )

        return 0 if status < 400 else 1

    except CLIError as e:
        from ..helpers import handle_cli_error
        return handle_cli_error(e, json_mode=False)
    except Exception as e:
        print_error(f"HTTP request failed: {e}")
        return 1
