# DataLens

**Upload or connect any dataset — get auto-profiling, analytics dashboards, ML forecasts, and GenAI-powered insights from one place.**

> 🚧 Work in progress — Week 1 of a 6-week build. Follow along: [task list](docs/TASK_LIST.md).

## What this is

A pluggable data intelligence platform built as a production-grade portfolio project:

- **Lakehouse pipeline** — medallion architecture (bronze/silver/gold) on S3 + Parquet + DuckDB + dbt, orchestrated by Apache Airflow
- **Connectors** — plugin architecture; MVP ships with CSV upload and a daily AU job-market ingestion (Adzuna API)
- **ML layer** — time-series forecasting and anomaly detection
- **GenAI layer** — narrative insights and guarded NL→SQL chat-with-your-data
- **Stack** — FastAPI · Next.js/TypeScript · PostgreSQL · Airflow · dbt · DuckDB · AWS · Terraform · GitHub Actions

Full design: [PRD](docs/PRD.md) · [Architecture](docs/ARCHITECTURE.md) · [Tech stack & rationale](docs/TECH_STACK.md)

## Quickstart (local dev)

Requires Docker and `make`.

```bash
cp .env.example .env          # add your free Adzuna API keys
make dev                      # Postgres + MinIO + Airflow + API
```

| Service | URL |
|---|---|
| API docs | http://localhost:8000/docs |
| Airflow | http://localhost:8080 (admin/admin) |
| MinIO console | http://localhost:9001 (minioadmin/minioadmin) |

Run backend tests:

```bash
make setup   # one-time: create venv + install dev deps (uses uv)
make test
make lint
```

## Repository layout

```
backend/     FastAPI app, connectors, ML & GenAI services
frontend/    Next.js dashboard (Week 3)
pipelines/   Airflow DAGs + dbt project
infra/       Terraform (Week 6)
docker/      Docker Compose dev/prod stacks
docs/        PRD, architecture, ADRs, task list
```

## License

MIT
