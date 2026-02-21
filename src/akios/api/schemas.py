# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Pydantic schemas for the AKIOS REST API request/response models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Request models ───────────────────────────────────────────────────

class WorkflowRunRequest(BaseModel):
    """POST /api/v1/workflows/run body."""
    workflow_path: str = Field(..., description="Path to workflow YAML file")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional execution context")


# ── Response models ──────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """GET /api/v1/health."""
    status: str = "ok"
    version: str


class StatusResponse(BaseModel):
    """GET /api/v1/status."""
    version: str
    sandbox_enabled: bool
    pii_redaction_enabled: bool
    audit_enabled: bool
    budget_limit: float
    network_access_allowed: bool


class WorkflowResult(BaseModel):
    """Result of a workflow execution."""
    workflow_id: Optional[str] = None
    status: str
    steps_executed: int = 0
    total_steps: int = 0
    output_directory: Optional[str] = None
    error: Optional[str] = None
    results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time: Optional[float] = None


class WorkflowListItem(BaseModel):
    """Single workflow entry for listing."""
    name: str
    path: str
    description: Optional[str] = None


class WorkflowListResponse(BaseModel):
    """GET /api/v1/workflows."""
    workflows: List[WorkflowListItem]
    count: int


class AuditEvent(BaseModel):
    """Single audit event."""
    workflow_id: Optional[str] = None
    step: Optional[int] = None
    agent: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None


class AuditEventsResponse(BaseModel):
    """GET /api/v1/audit/events."""
    events: List[AuditEvent]
    total: int


class AuditVerifyResponse(BaseModel):
    """GET /api/v1/audit/verify."""
    valid: bool
    total_events: int
    errors: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    error: str
    detail: Optional[str] = None
