from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentTaskType(StrEnum):
    GENERATE_PROBES = "generate_probes"
    EXECUTE_PROBES = "execute_probes"
    EVALUATE_RESPONSES = "evaluate_responses"
    AGGREGATE_FINDINGS = "aggregate_findings"
    GENERATE_REPORT = "generate_report"
    NOTIFY_USER = "notify_user"


class AgentTask(BaseModel):
    type: AgentTaskType
    audit_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    task_type: AgentTaskType
    audit_id: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class Agent(ABC):
    id: str
    name: str
    supported_tasks: set[AgentTaskType]

    def can_handle(self, task: AgentTask) -> bool:
        return task.type in self.supported_tasks

    @abstractmethod
    async def run(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError
