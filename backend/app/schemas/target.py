from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TargetProvider


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    provider: TargetProvider = TargetProvider.MOCK
    model_name: str = "mock-model"
    configuration: dict[str, Any] = Field(default_factory=dict)


class TargetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    provider: TargetProvider | None = None
    model_name: str | None = None
    configuration: dict[str, Any] | None = None


class TargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    provider: str
    model_name: str
    configuration: dict[str, Any]
    created_at: datetime
    updated_at: datetime
