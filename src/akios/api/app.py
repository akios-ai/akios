# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
FastAPI application factory for the AKIOS REST API.

Usage::

    akios serve                        # start on 127.0.0.1:8000
    akios serve --host 0.0.0.0 --port 9000
    akios serve --reload               # auto-reload on code changes
"""

from __future__ import annotations

import json
import os
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    AuditEvent,
    AuditEventsResponse,
    AuditVerifyResponse,
    ErrorResponse,
    HealthResponse,
    StatusResponse,
    WorkflowListItem,
    WorkflowListResponse,
    WorkflowResult,
    WorkflowRunRequest,
)

logger = logging.getLogger(__name__)

# ── Version ──────────────────────────────────────────────────────────

def _get_version() -> str:
    try:
        from akios._version import __version__
        return __version__
    except ImportError:
        return "unknown"


# ── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("AKIOS API starting — version %s", _get_version())
    yield
    logger.info("AKIOS API shutting down")


# ── App factory ──────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title="AKIOS API",
        description="Security-first AI agent runtime — REST interface",
        version=_get_version(),
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # CORS — local-only by default, configurable via env
    origins = os.getenv("AKIOS_CORS_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ── Health ────────────────────────────────────────────────────

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
    async def health():
        """Lightweight liveness probe."""
        return HealthResponse(status="ok", version=_get_version())

    # ── Status ────────────────────────────────────────────────────

    @app.get("/api/v1/status", response_model=StatusResponse, tags=["system"])
    async def status():
        """Return current AKIOS configuration snapshot."""
        from akios.config import get_settings
        settings = get_settings()
        return StatusResponse(
            version=_get_version(),
            sandbox_enabled=getattr(settings, "sandbox_enabled", True),
            pii_redaction_enabled=getattr(settings, "pii_redaction_enabled", True),
            audit_enabled=getattr(settings, "audit_enabled", True),
            budget_limit=getattr(settings, "budget_limit_per_run", 1.0),
            network_access_allowed=getattr(settings, "network_access_allowed", False),
        )

    # ── Workflows ─────────────────────────────────────────────────

    @app.get("/api/v1/workflows", response_model=WorkflowListResponse, tags=["workflows"])
    async def list_workflows():
        """List available workflow YAML files in templates/ and workflows/."""
        items: List[WorkflowListItem] = []
        search_dirs = ["templates", "workflows"]
        for d in search_dirs:
            p = Path(d)
            if not p.is_dir():
                continue
            for f in sorted(p.rglob("*.y*ml")):
                items.append(WorkflowListItem(
                    name=f.stem,
                    path=str(f),
                    description=_extract_workflow_description(f),
                ))
        return WorkflowListResponse(workflows=items, count=len(items))

    @app.post(
        "/api/v1/workflows/run",
        response_model=WorkflowResult,
        responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
        tags=["workflows"],
    )
    async def run_workflow(req: WorkflowRunRequest):
        """Execute a workflow and return the result synchronously."""
        from akios.core.runtime import RuntimeEngine

        wf_path = Path(req.workflow_path)
        if not wf_path.exists():
            raise HTTPException(status_code=400, detail=f"Workflow file not found: {req.workflow_path}")

        start = time.time()
        try:
            engine = RuntimeEngine()
            engine.reset()
            result = engine.run(str(wf_path), context=req.context or {})
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        elapsed = time.time() - start

        return WorkflowResult(
            workflow_id=result.get("workflow_id"),
            status=result.get("status", "unknown"),
            steps_executed=result.get("steps_executed", 0),
            total_steps=result.get("total_steps", 0),
            output_directory=result.get("output_directory"),
            error=result.get("error"),
            results=result.get("results", []),
            execution_time=round(elapsed, 3),
        )

    # ── Audit ─────────────────────────────────────────────────────

    @app.get("/api/v1/audit/events", response_model=AuditEventsResponse, tags=["audit"])
    async def audit_events(
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        """Return paginated audit events (most recent first)."""
        events = _load_audit_events()
        total = len(events)
        page = events[offset: offset + limit]
        return AuditEventsResponse(events=page, total=total)

    @app.get("/api/v1/audit/verify", response_model=AuditVerifyResponse, tags=["audit"])
    async def audit_verify():
        """Verify audit log integrity."""
        try:
            from akios.core.audit.ledger import get_ledger
            ledger = get_ledger()
            is_valid = ledger.verify_integrity()
            total = ledger.size()
            errors: List[str] = [] if is_valid else ["Integrity verification failed"]
            return AuditVerifyResponse(valid=is_valid, total_events=total, errors=errors)
        except Exception as exc:
            return AuditVerifyResponse(valid=False, total_events=0, errors=[str(exc)])

    return app


# ── Helpers ──────────────────────────────────────────────────────────

def _extract_workflow_description(path: Path) -> str | None:
    """Read the first ``description:`` field from a YAML workflow."""
    try:
        import yaml
        with open(path) as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, dict):
            return data.get("description")
    except Exception:
        pass
    return None


def _load_audit_events() -> list[AuditEvent]:
    """Load audit events from the JSONL ledger file."""
    audit_path = Path("audit/audit_events.jsonl")
    if not audit_path.exists():
        return []
    events: list[AuditEvent] = []
    try:
        with open(audit_path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    events.append(AuditEvent(**data))
                except Exception:
                    continue
    except Exception:
        pass
    events.reverse()  # most recent first
    return events
