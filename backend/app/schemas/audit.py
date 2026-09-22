from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    target_id: str
    probe_ids: list[str] = Field(default_factory=list, description="Empty means run every registered probe.")
    evaluator_id: str = "composite-disparity"
    configuration: dict[str, Any] = Field(default_factory=dict)


class AuditUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    probe_ids: list[str] | None = None
    evaluator_id: str | None = None
    configuration: dict[str, Any] | None = None


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    target_id: str
    probe_ids: list[str]
    evaluator_id: str
    status: str
    configuration: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class AuditRunResponse(BaseModel):
    audit_id: str
    status: str
    probes_run: int
    findings: int
    highest_disparity: float
    attribute_summary: list[dict[str, Any]]
