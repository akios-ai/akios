# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
CLI serve command — ``akios serve``

Starts a local REST API server powered by FastAPI + Uvicorn.
Requires: ``pip install akios[api]``
"""

import argparse
import sys


def register_serve_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``serve`` subcommand."""
    parser = subparsers.add_parser(
        "serve",
        help="Start the AKIOS REST API server",
        description=(
            "Launch a local HTTP server exposing the AKIOS runtime as a REST API.\n\n"
            "Endpoints:\n"
            "  GET  /api/v1/health           Liveness probe\n"
            "  GET  /api/v1/status           Configuration snapshot\n"
            "  GET  /api/v1/workflows        List available workflows\n"
            "  POST /api/v1/workflows/run    Execute a workflow\n"
            "  GET  /api/v1/audit/events     Paginated audit events\n"
            "  GET  /api/v1/audit/verify     Verify audit integrity\n"
            "  GET  /api/v1/docs             Interactive Swagger UI\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Listen port (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Auto-reload on code changes (development mode)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )
    parser.set_defaults(func=run_serve_command)


def run_serve_command(args: argparse.Namespace) -> None:
    """Entry point for ``akios serve``."""
    # Guard: check for optional deps
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        print(
            "❌ The API server requires extra dependencies.\n"
            "   Install them with:\n\n"
            "     pip install akios[api]\n\n"
            "   (This adds fastapi and uvicorn.)",
            file=sys.stderr,
        )
        sys.exit(1)

    host = args.host
    port = args.port

    print(
        f"🚀 AKIOS API server starting on http://{host}:{port}\n"
        f"   Swagger UI: http://{host}:{port}/api/v1/docs\n"
        f"   OpenAPI:    http://{host}:{port}/api/v1/openapi.json\n",
        file=sys.stderr,
    )

    uvicorn.run(
        "akios.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=args.reload,
        workers=args.workers,
        log_level="info",
    )
