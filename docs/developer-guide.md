# Developer Guide

## Layout

```
backend/app/
  agents/       specialist agents and the orchestrator
  api/routes/   FastAPI endpoints
  core/         settings and logging
  db/           declarative base, session, table creation
  evaluators/   metrics, lexicons, disparity and composite evaluators
  models/       SQLAlchemy tables and enums
  probes/       probe interface, built-in probes, registry
  reports/      JSON, Markdown and HTML rendering
  schemas/      pydantic request and response models
  services/     audit, target, report, dashboard workflows; target adapters
  utils/        text normalisation helpers
backend/tests/  unit and end-to-end tests
backend/scripts/demo_audit.py
frontend/src/
  main.tsx      the whole dashboard: six views plus shared components
  api/client.ts fetch wrapper with error unwrapping
```

## Tests

```
cd backend
pytest
```

Covers metric arithmetic, probe construction invariants, each evaluator's behaviour, and a
full audit through the API with the mock target.

## Where To Add Things

| Change | Place |
| --- | --- |
| A new question to ask | `app/probes/builtins.py` - see [probe-guide.md](probe-guide.md) |
| A new way to compare answers | `app/evaluators/` - see [evaluator-guide.md](evaluator-guide.md) |
| A new model provider | `app/services/target_adapters.py` - see [target-adapters.md](target-adapters.md) |
| A new workflow stage | A new agent in `app/agents/specialists.py`, added to `DEFAULT_AGENTS` |
| A new endpoint | `app/api/routes/`, then include the router in `app/api/router.py` |
| A new dashboard view | `frontend/src/main.tsx` - add a tab to `tabs` and a component |

Workflow services should never import a specific agent, and routes should never contain
workflow logic. Keeping those two rules is what makes new probes and evaluators cheap.

## Style

Ruff, line length 140, target Python 3.11+. The frontend builds with `tsc` in strict mode before
Vite bundles it, so a type error fails the build rather than reaching the image.
