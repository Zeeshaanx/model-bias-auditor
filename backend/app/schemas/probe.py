from typing import Any

from pydantic import BaseModel, Field


class ProbeRead(BaseModel):
    id: str
    name: str
    description: str
    attribute: str
    groups: list[str]
    jurisdiction: str = "cross"
    source: str = ""
    legal_basis: str = ""


class EvaluatorRead(BaseModel):
    id: str
    name: str
    description: str
    metric: str


class ProbeRunRequest(BaseModel):
    target_id: str | None = None
    provider: str = "mock"
    model_name: str = "mock-model"
    configuration: dict[str, Any] = Field(default_factory=dict)
    evaluator_id: str = "composite-disparity"


class ProbeRunResponse(BaseModel):
    probe_id: str
    attribute: str
    prompts: dict[str, str]
    responses: dict[str, str]
    evaluation: dict[str, Any]
