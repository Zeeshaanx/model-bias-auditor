# Model Bias Auditor

AI Safety and Security Compliance agent that automatically detects and reports bias, fairness
and ethical issues in AI model outputs.

Where a red teaming agent asks *"can this model be broken?"*, this agent asks
*"does this model treat matched requests differently depending on who is asking?"*

---

## How It Works

A bias probe never sends one prompt. It sends a **counterfactual set**: prompts that are
identical apart from a single protected attribute.

```
"Write a short hiring summary for Greg Baker, a project manager with eight years..."
"Write a short hiring summary for Jamal Jones, a project manager with eight years..."
```

The responses are then compared against each other on four measures — refusal, sentiment,
stereotype framing and answer effort. A systematic gap between groups is a finding, stored
together with the prompts and responses that produced it.

Bias cannot be detected the way a vulnerability is. No single answer is wrong on its own;
what may be wrong is the relationship between one answer and the answer to an equivalent
request. That is why the smallest unit of testing here is a set, not a single prompt.

## Scope

The built-in suite targets **English-language models in a United States or European Union
context**, and probes are tagged with the jurisdiction they are valid for.

This is a design constraint, not a gap. A probe is not portable: a name that signals a
minority group in Germany signals nothing in the United States, the decisions that are
consequential differ, and so does the law that makes a disparity actionable. The probes
whose signal is stated in the prompt rather than carried by a name — an age, a declared
disability, a partner's gender — are tagged `cross` and run under either jurisdiction.

Where a probe's group markers come from a published correspondence study, the citation is
on the probe itself. The US pack uses the name set from Bertrand & Mullainathan (2004);
the EU pack follows the GEMM study's procedure. Probes whose markers were constructed for
this project say so. See [docs/regulatory-mapping.md](docs/regulatory-mapping.md).

## What Is Included

- Python 3.13 FastAPI backend
- Async SQLAlchemy model layer (SQLite by default, PostgreSQL under Docker Compose)
- Counterfactual bias probe architecture with 18 built-in probes in three jurisdiction packs (US, EU, cross-jurisdiction)
- Eight attributes: ethnicity, gender, age, religion, disability, sexual orientation, nationality, socioeconomic background
- Each probe carries the provenance of its group markers and the statute that makes a disparity on it relevant
- Four disparity evaluators plus a composite evaluator
- Agent and agent orchestrator runtime with bounded concurrency
- Target adapters for a built-in mock, OpenAI, OpenAI-compatible, Anthropic and Google Gemini
- Target, audit, probe, finding, report and dashboard APIs
- Markdown/HTML/JSON report generator
- React/TypeScript/Vite/Tailwind dashboard with side-by-side response comparison
- Docker Compose deployment
- Architecture, methodology, probe, evaluator, adapter and API docs
- Unit and end-to-end tests

## Quick Start

```
docker compose up --build
```

| Service | URL |
| --- | --- |
| Dashboard | `http://localhost:8082` |
| Backend API | `http://localhost:8002` |
| OpenAPI / Swagger | `http://localhost:8002/docs` |

Ports 8002 and 8082 are chosen so this runs alongside the AI Red Teaming Platform
(8001 and 8081) without a clash.

Stop with `Ctrl+C`, then `docker compose down`. Add `-v` to drop the database volume too.

## Try It Without Any API Key

```
cd backend
python scripts/demo_audit.py
```

Registers the built-in mock target, runs every probe, and prints a full Markdown report.
No API key, no database server and no network access required.

## Does The Measurement Work?

A disparity score is worth nothing until something shows the scores respond to a disparity
that is really there. The mock target has calibration modes with planted ground truth:

```
cd backend
python scripts/calibrate.py
```

| Mock mode | Expected | Actual |
| --- | --- | --- |
| `fair` — identical reply to every arm | zero findings | 0 / 18 |
| `biased` — degraded reply for planted groups | findings on exactly the planted probes | 8 / 8, 0 stray |
| `refusing` — declines for planted groups | `refusal_rate` dominant on those probes | 8 / 8 |
| `noisy` — hash-seeded variation (default) | findings, all of them artifacts | 18 / 18 |

`backend/tests/test_calibration.py` asserts this, so a change that breaks the measurement
fails the build.

**What this proves:** the evaluators stay silent on identical output and fire on a planted
gap, naming the right group. **What it does not prove:** that the metrics are meaningful on
real model output. That needs a real target and a human reading the stored evidence.

The `noisy` row is the useful warning: the default mock produces a finding on every single
probe, and not one of them is bias. See [docs/methodology.md](docs/methodology.md) for the
two effects — short responses and arm count — that move a score with no bias present.

## Running Without Docker

Backend:

```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload --port 8002
```

Frontend, in a separate shell:

```
cd frontend
npm install
npm run dev
```

The Vite dev server runs on port 5174 and proxies `/api` to `http://localhost:8002`.

## Auditing A Real Model

The `mock` provider is the default so the pipeline can be exercised offline. Its answers are
synthetic; any disparity it produces is an artifact of that synthesis and is not a finding
about any model. To audit a real model, register a target with a real provider:

| Provider | `provider` value | Notes |
| --- | --- | --- |
| Built-in mock | `mock` | Offline, deterministic, no API key |
| Google Gemini | `google_gemini` | `api_key` required |
| OpenAI | `openai` | `api_key` required |
| OpenAI-compatible | `openai_compatible` | `api_key` and `base_url`; use for Ollama, vLLM, LM Studio |
| Anthropic | `anthropic` | `api_key` required |

```json
{
  "name": "Local Llama",
  "provider": "openai_compatible",
  "model_name": "llama3.1:8b",
  "configuration": {
    "api_key": "ollama",
    "base_url": "http://host.docker.internal:11434/v1",
    "temperature": 0
  }
}
```

Four things worth knowing before auditing a real model.

**Temperature 0.** Counterfactual comparison assumes the only variable that changes is the
attribute token, and sampling noise at a higher temperature is indistinguishable from bias.

**Thinking tokens.** Gemini 2.5 and 3 models think by default, and thinking counts against
`max_tokens`. Left alone, the budget is spent before a word is emitted and the visible
answer is cut at a different point on every call, which an evaluator reads as a length
disparity. The Gemini adapter therefore sends `thinkingBudget: 0` unless you set
`thinking_budget` yourself.

**Truncation is an error.** Every adapter now raises when the provider reports the response
was cut off at the token limit, and the arm is dropped instead of measured. A response that
stopped early is not comparable with one that finished.

**Local models.** A model running on your own machine is reached from inside the backend
container at `host.docker.internal`, not `localhost`.

## A Full Audit In Four Calls

The dashboard does all of this with buttons. The raw calls are:

```
POST /api/v1/targets        {"name": "My model", "provider": "mock", "model_name": "mock-model"}
POST /api/v1/audits         {"name": "Baseline sweep", "target_id": "<id>", "probe_ids": []}
POST /api/v1/audits/<id>/run
POST /api/v1/reports        {"audit_id": "<id>", "format": "markdown"}
```

An empty `probe_ids` means "run every registered probe".

## Configuration

Every setting is an environment variable prefixed `MBA_`. See `backend/.env.example`.
Under Docker, add them to `docker-compose.yml` under `backend:` → `environment:`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MBA_DATABASE_URL` | `sqlite+aiosqlite:///./model_bias_auditor.db` | Async SQLAlchemy URL |
| `MBA_LOG_LEVEL` | `INFO` | Log verbosity |
| `MBA_WORKER_CONCURRENCY` | `4` | Concurrent requests to the target |
| `MBA_DEFAULT_EVALUATOR_ID` | `composite-disparity` | Evaluator used when none is given |
| `MBA_DISPARITY_WARNING_THRESHOLD` | `0.15` | Below this, nothing is recorded as a finding |
| `MBA_DISPARITY_CRITICAL_THRESHOLD` | `0.35` | Anchors the severity bands |
| `MBA_MIN_COMPARABLE_TOKENS` | `150` | Below this, findings are flagged `low_signal` |
| `MBA_LOW_SIGNAL_CONFIDENCE_CAP` | `0.4` | Confidence ceiling for a low-signal finding |

## Repository Layout

```
backend/app/
  probes/         probe interface, counterfactual probe, packs/ (us, eu, cross), registry
  evaluators/     metrics, lexicons, disparity and composite evaluators
  agents/         6 specialist agents and the orchestrator
  services/       audit, target, report, dashboard workflows; target adapters
  api/routes/     FastAPI endpoints
  models/         SQLAlchemy tables and enums
  schemas/        pydantic request and response models
  reports/        JSON, Markdown and HTML rendering
  core/, db/, utils/
backend/tests/    unit and end-to-end tests
backend/scripts/  demo_audit.py, calibrate.py
frontend/src/     the dashboard (main.tsx) and the API client
docker/           backend and frontend images, nginx config
docs/             documentation
```

## Tests

```
cd backend
pytest
```

36 tests covering metric arithmetic, probe construction invariants, jurisdiction and
provenance checks on every probe, the four calibration assertions, adapter truncation guards, each evaluator's
behaviour, and a full audit through the API against the mock target.

## Documentation

| Document | Contents |
| --- | --- |
| [docs/white-paper.md](docs/white-paper.md) | Method, metrics, architecture, limitations and future work |
| [docs/architecture.md](docs/architecture.md) | Layers, data flow, persistence |
| [docs/methodology.md](docs/methodology.md) | How disparity is measured, and what the numbers do not mean |
| [docs/regulatory-mapping.md](docs/regulatory-mapping.md) | Each attribute against US and EU law; why probes are not portable |
| [docs/probe-guide.md](docs/probe-guide.md) | Writing a new bias probe |
| [docs/evaluator-guide.md](docs/evaluator-guide.md) | Writing a new evaluator |
| [docs/agent-orchestrator.md](docs/agent-orchestrator.md) | The agent runtime |
| [docs/target-adapters.md](docs/target-adapters.md) | Connecting the model under audit |
| [docs/api.md](docs/api.md) | Endpoint reference |
| [docs/deployment.md](docs/deployment.md) | Docker and configuration |
| [docs/developer-guide.md](docs/developer-guide.md) | Where to add things |
| [docs/milestones.md](docs/milestones.md) | Delivered and planned scope |

## Project Status

**Delivered:** backend, probe layer, evaluator layer, agent runtime, audit and report APIs,
dashboard, Docker Compose, documentation, 17 passing tests.

**Planned:** repeated sampling with significance
testing, a pre-tested European name set, validated lexicons, scheduled recurring audits,
authentication and authorization, Kubernetes manifests. See
[docs/milestones.md](docs/milestones.md) for the full scope list.

## Responsible Use

A disparity score measures that a model produced systematically different output for matched
prompts. It is evidence for human review, not a legal determination of discrimination, and
the lexicon-based metrics are heuristics with known limits — including one sample per group,
English-only word lists, and names that may signal more than one attribute at once.

Read [docs/methodology.md](docs/methodology.md) before quoting any number from a report.
