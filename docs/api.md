# API Reference

Base path: `/api/v1`. Interactive documentation: `/docs`.

## Health

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness plus registry sizes |

## Targets

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/targets` | Register a model under audit |
| GET | `/targets` | List targets |
| GET | `/targets/{target_id}` | Read one target |
| PATCH | `/targets/{target_id}` | Update a target |
| DELETE | `/targets/{target_id}` | Delete a target |

## Probes And Evaluators

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/probes` | List probes, optionally filtered by `?attribute=gender` |
| GET | `/evaluators` | List evaluators |
| POST | `/probes/{probe_id}/run` | Run one probe standalone, no audit created |

## Audits

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/audits` | Create an audit. Empty `probe_ids` means every registered probe |
| GET | `/audits` | List audits |
| GET | `/audits/{audit_id}` | Read one audit |
| PATCH | `/audits/{audit_id}` | Update an audit |
| DELETE | `/audits/{audit_id}` | Delete an audit |
| POST | `/audits/{audit_id}/run` | Execute the audit and persist results |
| GET | `/audits/{audit_id}/findings` | Findings, highest disparity first |
| GET | `/audits/{audit_id}/results` | Raw prompts and responses behind the findings |

## Reports

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/reports` | Render a report (`json`, `markdown`, `html`) |
| GET | `/reports?audit_id=` | List reports |
| GET | `/reports/{report_id}` | Read one report |
| GET | `/reports/{report_id}/download` | Download with the right content type |

## Dashboard

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/dashboard` | Counts, severity breakdown, per-attribute rollup, recent audits |
| GET | `/agents` | Registered agents and the task types each accepts |

## Worked Example

```bash
curl -X POST localhost:8002/api/v1/targets \
  -H 'Content-Type: application/json' \
  -d '{"name":"Mock model","provider":"mock","model_name":"mock-model"}'

curl -X POST localhost:8002/api/v1/audits \
  -H 'Content-Type: application/json' \
  -d '{"name":"Baseline sweep","target_id":"<TARGET_ID>","probe_ids":[]}'

curl -X POST localhost:8002/api/v1/audits/<AUDIT_ID>/run

curl -X POST localhost:8002/api/v1/reports \
  -H 'Content-Type: application/json' \
  -d '{"audit_id":"<AUDIT_ID>","format":"markdown"}'
```
