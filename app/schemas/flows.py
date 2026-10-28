"""Scenario runner schemas (flows + simulation)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class FlowRunRequest(BaseModel):
    flow_id: str = Field(..., pattern=r"^(flow1|flow2|flow3|simulation)$")
    seed: int | None = None
    params: Dict[str, Any] = Field(default_factory=dict)


class FlowArtifactRef(BaseModel):
    kind: str
    id: str
    url: str | None = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class FlowRunResponse(BaseModel):
    flow_id: str
    ok: bool
    started_at: datetime
    finished_at: datetime
    summary: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[FlowArtifactRef] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

