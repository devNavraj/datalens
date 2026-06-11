# Tech Stack & Rationale — DataLens

Every choice maps to a skill screened in AU Data/AI Engineer job ads.

| Area | Choice | Why (and the resume keyword it buys) |
|---|---|---|
| Language (data/backend) | Python 3.12 | Universal data/AI requirement |
| Backend framework | FastAPI + Pydantic v2 | "API development", async, OpenAPI docs for free |
| App DB | PostgreSQL 16 (Docker) | The default relational DB in AU ads |
| ORM | SQLAlchemy 2 (async) + Alembic | Migrations discipline |
| Lakehouse storage | S3 + Parquet, medallion layout | "Data lake", "lakehouse", "S3" |
| Query engine | DuckDB (`dbt-duckdb`) | Warehouse SQL at $0; talking point vs Snowflake/Redshift |
| Transformations | dbt-core | Top-3 data keyword in AU ads; tests + lineage docs |
| Orchestration | Apache Airflow 2.x (Docker, LocalExecutor) | #1 orchestrator keyword |
| Data validation | pandera + dbt tests | "Data quality" |
| Classic ML | scikit-learn, statsmodels | Forecasting, anomaly detection |
| GenAI | OpenAI API (existing credits) behind internal `LLMClient` abstraction; sqlglot for SQL guardrails | "GenAI", "LLM integration", "agentic" without lock-in |
| Frontend | Next.js 15 + TypeScript + Tailwind + shadcn/ui + Recharts | Full-stack TS differentiation |
| Frontend hosting | Vercel (free) | Zero cost, CI built in |
| Cloud | AWS: EC2 t3.small, S3, IAM, Route53, Budgets | Most-demanded cloud in AU |
| IaC | Terraform | "IaC/Terraform" keyword |
| Containers | Docker + Docker Compose | Baseline expectation |
| CI/CD | GitHub Actions (lint, mypy, pytest ≥80% cov, dbt build, deploy) | "CI/CD" with public proof (badges) |
| Testing | pytest + pytest-asyncio (backend), Vitest + Playwright smoke (frontend) | TDD story for interviews |
| Lint/format | ruff + mypy (py), eslint + prettier (ts) | Code-quality signal |
| Job data | Adzuna API (free tier, AU coverage) | Legal, stable; no scraping risk |

## Repo layout (monorepo)

```
datalens/
├── backend/          # FastAPI app (routers/services/repositories/connectors/ml/genai)
├── frontend/         # Next.js app
├── pipelines/
│   ├── dags/         # Airflow DAGs
│   └── dbt/          # dbt project (bronze→silver→gold models, tests, docs)
├── infra/            # Terraform
├── docker/           # compose files (dev, prod)
├── docs/             # PRD, architecture, ADRs, blog drafts
└── .github/workflows/
```

## Cost ledger (target ≤ $30/mo)

EC2 t3.small ~$15 · S3 <$1 · Route53 ~$0.50 · domain ~$1.50/mo amortised · Vercel $0 · OpenAI $0 cash (credits) → **~$18/month**, alarm at $25.
