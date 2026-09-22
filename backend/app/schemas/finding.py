from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    audit_id: str
    probe_id: str
    probe_name: str
    attribute: str
    evaluator_id: str
    metric: str
    severity: str
    disparity_score: float
    confidence: float
    arm_count: int = 0
    low_signal: bool = False
    summary: str
    metrics: dict[str, Any]
    evidence: dict[str, Any]
    created_at: datetime


class ProbeResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    audit_id: str
    probe_id: str
    attribute: str
    prompts: dict[str, Any]
    responses: dict[str, Any]
    errors: dict[str, Any]
    created_at: datetime
