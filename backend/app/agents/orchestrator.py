import asyncio

from app.agents.base import Agent, AgentResult, AgentTask
from app.agents.specialists import DEFAULT_AGENTS
from app.core.config import get_settings


class AgentOrchestrator:
    """Routes each task to the agent that declares support for it.

    Workflow services call the orchestrator; they never import a specific agent. Adding a
    stage therefore means adding an agent, not editing the workflow.
    """

    def __init__(self, agents: list[Agent] | None = None, concurrency: int | None = None) -> None:
        self.agents = agents or DEFAULT_AGENTS
        self.concurrency = concurrency or get_settings().worker_concurrency

    def select_agent(self, task: AgentTask) -> Agent:
        for agent in self.agents:
            if agent.can_handle(task):
                return agent
        raise ValueError(f"No agent available for task type: {task.type}")

    def describe(self) -> list[dict[str, object]]:
        return [
            {"id": agent.id, "name": agent.name, "supported_tasks": sorted(str(task) for task in agent.supported_tasks)}
            for agent in self.agents
        ]

    async def dispatch(self, task: AgentTask) -> AgentResult:
        agent = self.select_agent(task)
        return await agent.run(task)

    async def dispatch_many(self, tasks: list[AgentTask]) -> list[AgentResult]:
        semaphore = asyncio.Semaphore(self.concurrency)

        async def guarded(task: AgentTask) -> AgentResult:
            async with semaphore:
                return await self.dispatch(task)

        return await asyncio.gather(*(guarded(task) for task in tasks))


agent_orchestrator = AgentOrchestrator()
