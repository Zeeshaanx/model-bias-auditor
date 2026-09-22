# Milestones

## Milestone 1: Backend Foundation

Status: delivered

- Repository structure and FastAPI application factory
- Settings and structured logging
- Async SQLAlchemy base, session and table creation
- Domain models: target, audit, probe result, finding, report, audit log
- Health endpoint and initial tests

## Milestone 2: Counterfactual Probe Layer

Status: delivered

- `BiasProbe` interface and `ProbeCase` / `ProbeObservation` contracts
- Generic `CounterfactualProbe`
- 18 built-in probes across 8 attributes, in three jurisdiction packs (US, EU, cross-jurisdiction)
- Probe registry and standalone probe execution endpoint

## Milestone 3: Disparity Evaluators

Status: delivered

- Pure, unit-tested metric functions and editable lexicons
- Refusal, sentiment, stereotype-association and response-effort evaluators
- Composite evaluator with severity and confidence
- Evaluator registry

## Milestone 4: Agent Runtime

Status: delivered

- Agent interface, six specialist agents, orchestrator with bounded concurrency
- Target adapters: mock, OpenAI, OpenAI-compatible, Anthropic, Gemini
- Per-arm error capture

## Milestone 5: Audit APIs And Reporting

Status: delivered

- Target and audit CRUD, audit execution, findings and raw results endpoints
- JSON, Markdown and HTML reports with download
- Dashboard metrics

## Milestone 6: Dashboard

Status: delivered

- React/Vite/Tailwind interface over the existing API
- Overview, targets, audits, probes, findings and reports views
- Side-by-side comparison of the prompts and responses behind each finding
- Standalone probe runner for probe development
- Served by nginx, which proxies the API

## Milestone 7: Statistical Rigour

Planned

- Repeated sampling per arm with mean and variance
- Significance testing so a gap can be distinguished from sampling noise
- Effect-size reporting alongside the raw disparity score
- Calibration of each metric's scale against observed model behaviour
- Per-arm-count thresholds, so probes with different arm counts can be ranked together

## Milestone 8: Evaluation Quality

Planned

- Replace lexicon counting with a validated lexicon or a trained classifier
- A pre-tested European name set, and European-language lexicons (DE, FR, NL, ES)
- LLM-as-judge evaluator with its own bias controls
- Inter-metric agreement analysis

## Milestone 9: Scheduling And Continuous Auditing

Planned

- APScheduler integration with PostgreSQL persistence
- Recurring audits and drift detection across runs
- Alerting when a previously fair probe starts showing disparity

## Milestone 10: Authentication And Hardening

Planned

- JWT/OAuth2 password flow and role-based authorization
- Rate limiting, narrowed CORS, encrypted storage of target API keys
- Alembic migrations
- Kubernetes manifests

## Milestone 11: Dashboard Depth

Planned

- Trend view across repeated audits
- Filtering findings by attribute and severity
- Inline editing of probe group definitions
