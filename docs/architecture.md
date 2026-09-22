# Architecture

The auditor is cloud-agnostic: it runs on Docker Compose, Kubernetes, a public cloud or a
laptop, with no dependency on any managed service.

## Data Flow

```
Target (the AI under audit)
   ^
   | prompts, one per demographic arm
   |
Probe registry  ->  Probe generation agent  ->  Probe execution agent
                                                      |
                                                observations
                                                      v
                          Bias evaluation agent  ->  Finding aggregation agent
                                                      |
                                                      v
                                    Persistence  +  Report agent  +  Notification agent
```

## Layers

- **Dashboard** is a static React bundle served by nginx, which also proxies `/api/` to the backend. It holds no logic of its own beyond presentation.
- **API routes** validate transport concerns and delegate to services.
- **Services** own the audit, target, report and dashboard workflows, plus ordering and persistence.
- **Agents** perform one stage each and are selected by the orchestrator, never imported by name from a workflow.
- **Probes** define what is asked. **Evaluators** define how the answers are compared. Both are registries, so new ones are added without touching workflow code.
- **Target adapters** isolate provider-specific HTTP details behind one `complete(prompt, configuration)` call.

## Persistence

The database stores targets, audits, probe results (the raw prompts and responses that
back every finding), findings, reports and an append-only audit log. Probe results are
kept deliberately: a fairness finding that cannot be traced back to the exact prompts and
responses that produced it is not usable as compliance evidence.

SQLite is the default so the project runs with no server. Docker Compose points
`MBA_DATABASE_URL` at PostgreSQL; nothing else changes.

The dashboard reads those stored probe results directly: every finding can be expanded into a
side-by-side view of the prompts and responses that produced it. That view is the point of keeping
the raw evidence - a reviewer should be able to disagree with the score by reading the answers.

## Relationship To The Red Teaming Platform

This project deliberately mirrors the AI Red Teaming Platform's plugin, agent and
orchestrator shape so that engineers moving between the two find the same structure. The
one structural difference is in the probe: an attack plugin produces a single prompt and
judges the single response, while a bias probe produces a set of prompts and judges the
responses *against each other*. Everything downstream of that follows from it.
