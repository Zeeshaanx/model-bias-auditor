# Deployment

## Docker Compose

```
docker compose up --build
```

Starts PostgreSQL, the backend and the dashboard.

| Service | URL | Container port |
| --- | --- | --- |
| Dashboard | `http://localhost:8082` | 80 |
| Backend API | `http://localhost:8002` | 8000 |
| PostgreSQL | `localhost:5442` | 5432 |

Ports 8002 and 8082 are chosen so the auditor runs alongside the AI Red Teaming Platform,
which uses 8001 and 8081.

Stop with `Ctrl+C`, then `docker compose down`. Add `-v` to drop the database volume too.

## Configuration

Every setting is an environment variable with the `MBA_` prefix. See `backend/.env.example`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MBA_DATABASE_URL` | `sqlite+aiosqlite:///./model_bias_auditor.db` | Async SQLAlchemy URL |
| `MBA_LOG_LEVEL` | `INFO` | Log level |
| `MBA_WORKER_CONCURRENCY` | `4` | Concurrent requests to the target |
| `MBA_DEFAULT_EVALUATOR_ID` | `composite-disparity` | Evaluator used when none is given |
| `MBA_DISPARITY_WARNING_THRESHOLD` | `0.15` | Below this, nothing is recorded as a finding |
| `MBA_DISPARITY_CRITICAL_THRESHOLD` | `0.35` | Anchors the severity bands |

Tables are created on startup, so no migration step is needed for a first run. Alembic
migrations are planned for the point where the schema starts changing under real data.

## Running Without Docker

```
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8002
```

```
cd frontend
npm install
npm run dev
```

SQLite is the default, so no database server is needed. The Vite dev server runs on port 5174 and
proxies `/api` to `http://localhost:8002`.

## Auditing A Model On Your Own Machine

A model served locally (Ollama, LM Studio, vLLM) is reached from inside the backend container at
`http://host.docker.internal:11434/v1`, not `http://localhost:11434/v1` - inside a container,
`localhost` means the container itself. Use provider `openai_compatible` and set that base URL.

## Hardening Before Any Shared Deployment

Not yet implemented, and required before this is exposed beyond a laptop:
authentication and authorization, rate limiting, CORS narrowed from `*`, and secret
handling for target API keys, which are currently stored in the target configuration as
plain JSON.
