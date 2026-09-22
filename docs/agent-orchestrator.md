# Agent And Orchestrator

The agent layer lives in `backend/app/agents`.

## Agents

| Agent | Task type | Responsibility |
| --- | --- | --- |
| `probe-generation-agent` | `generate_probes` | Build the counterfactual prompt sets |
| `probe-execution-agent` | `execute_probes` | Send every arm to the target, with bounded concurrency |
| `bias-evaluation-agent` | `evaluate_responses` | Score each observation with the chosen evaluator |
| `finding-aggregation-agent` | `aggregate_findings` | Filter by threshold and roll up per attribute |
| `report-agent` | `generate_report` | Render JSON, Markdown or HTML |
| `notification-agent` | `notify_user` | Delivery boundary (channel wiring is planned work) |

Each agent declares `supported_tasks` and returns an `AgentResult`.

## Orchestrator

`AgentOrchestrator` picks the first agent that declares support for a task and can dispatch
many tasks concurrently under a semaphore sized by `MBA_WORKER_CONCURRENCY`. Workflow
services call the orchestrator, never a specific agent, so adding a stage means adding an
agent rather than editing the workflow.

`GET /api/v1/agents` lists the registered agents and the tasks each accepts.

## Failure Handling

A target error on one arm is captured into `observation.errors` and the audit continues -
one unreachable variant should not discard the other arms. If the audit itself fails, the
status is set to `failed` and the exception text is stored on the audit record.
