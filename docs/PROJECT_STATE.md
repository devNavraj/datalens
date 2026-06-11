# PROJECT_STATE — DataLens development handoff

> **Purpose:** living context document. Read this first when resuming work — it captures
> what is built, how it is verified, the decisions behind it, and exactly where we are.
> Update at the end of every work session / merged PR.
>
> Last updated: **2026-06-11** (end of Week 2, PR open)

---

## 1. Project in one paragraph

**DataLens** is a portfolio project by Nawaraj Rai (GitHub: **devNavraj**) targeting hybrid
**Data + AI Engineer** roles in Australia. It is a pluggable data-intelligence platform:
connect or upload a dataset → auto-profiling, analytics dashboard, ML forecasting/anomaly
detection, and GenAI insights (narrative + guarded NL→SQL chat). Generic connector core,
demonstrated on two MVP sources: **CSV upload** and **AU tech job ads (Adzuna API)**.
6-week MVP plan, ~$20/month AWS budget, OpenAI API (existing credits) behind a provider
abstraction. Full design: [PRD](PRD.md) · [ARCHITECTURE](ARCHITECTURE.md) ·
[TECH_STACK](TECH_STACK.md) · [TASK_LIST](TASK_LIST.md) · [PORTFOLIO_PLAN](PORTFOLIO_PLAN.md).

## 2. Current status

| Item | State |
|---|---|
| Repo | https://github.com/devNavraj/datalens (public) |
| `main` | Week 1 complete (2 commits) |
| Open PR | `feat/week2-silver-dbt` → main: **open, awaiting user merge** — https://github.com/devNavraj/datalens/pull/new/feat/week2-silver-dbt |
| Tests | 50 backend tests, 93% coverage (gate 80%), ruff + mypy clean |
| dbt | `dbt build` 19/19 green (6 models + 13 tests) on fixture lake, runs in CI |
| Docker stack | Defined, **not yet booted by user** (needs Adzuna keys in `.env`, then `make dev`) |
| Adzuna keys | **User still needs to sign up** at https://developer.adzuna.com/ and fill `.env` |
| Week 1 demo | Pending user: trigger DAG, see bronze→silver→gold land in MinIO |

## 3. What is built (Weeks 1–2)

### Data flow (implemented end-to-end, verified by tests + CI)

```
Adzuna API ──AdzunaConnector──▶ bronze/adzuna/ingest_date=YYYY-MM-DD/page_NNN.json   (raw)
bronze ──transform_adzuna_bronze──▶ silver/adzuna/{job_postings,job_skills}/ingest_date=*/data.parquet
silver ──dbt build (dbt-duckdb, external materialization)──▶ gold/{fct_job_postings,dim_skills,skill_demand_daily,salary_by_skill}.parquet
gold ──Warehouse (DuckDB read-only)──▶ FastAPI /api/* endpoints
```

Orchestrated by Airflow DAG `adzuna_ingest_daily` (06:00 Australia/Sydney):
`ingest_to_bronze >> bronze_to_silver >> dbt_build`.

### Backend (`backend/src/datalens/`, Python 3.12, src layout)

| Module | What it does |
|---|---|
| `config.py` | `Settings` (pydantic-settings, env prefix `DATALENS_`). Key fields: `s3_*`, `lake_uri` (default `s3://datalens`), `adzuna_*` (creds default `None` → fail fast) |
| `connectors/base.py` | `BaseConnector` ABC + `ExtractBatch` + registry (`@register_connector`, `get_connector_class`) |
| `connectors/adzuna.py` | Pagination, short-page stop, retry-on-5xx (tenacity), 4xx fails fast. Query-param auth only — **never log request URLs** |
| `connectors/bronze.py` | `BronzeWriter` — Hive-style keys, key-part sanitization (`[A-Za-z0-9_-]+`) |
| `storage/object_store.py` | `ObjectStore` Protocol + `S3ObjectStore` (boto3, MinIO via endpoint_url, typed with boto3-stubs), `InMemoryObjectStore` (tests), `FilesystemObjectStore` (local/CI lake, root-escape guard) |
| `skills.py` | Deterministic taxonomy (~70 skills, categories) + boundary-safe regex extractor. Tested against false positives (java/JavaScript, excel/excellent, go needs context) |
| `transforms/adzuna.py` | flatten → pandera validation (`JOB_POSTINGS_SCHEMA`, `JOB_SKILLS_SCHEMA`, strict+coerce) → dedupe → Parquet. Drops invalid dates & blank titles. Raises loudly on empty bronze |
| `warehouse.py` | `Warehouse`: in-memory DuckDB, httpfs for s3:// lakes, `GOLD_TABLES` allowlist, bound params only, S3-config metachar guard. `JobMarketService`: top_skills / skill_trend / salaries / summary |
| `api.py` | Router `/api`: `GET /datasets`, `/job-market/summary`, `/job-market/skills/top`, `/job-market/skills/{skill}/trend` (404 if unknown), `/job-market/salaries`. DI via `get_warehouse` (lru_cache singleton; tests override `app.dependency_overrides[get_warehouse]`) |
| `ingest.py` | `run_adzuna_ingest` (bronze), `run_adzuna_silver`, `run_ingest` (generic). CLI `datalens-ingest adzuna --step bronze|silver|all` |
| `main.py` | FastAPI app, `/health`, includes api router |

### Pipelines

- `pipelines/dags/adzuna_ingest_daily.py` — TaskFlow DAG. `ds: str | None = None` in task
  signatures **is** the documented Airflow 2 context-injection pattern (a reviewer flagged it;
  rejected). Execution timeouts on all tasks. `datalens` importable via `PYTHONPATH=/opt/datalens/src`.
- `pipelines/dbt/` — dbt-duckdb project, profile targets: `dev` (MinIO/S3, env `DBT_S3_ENDPOINT`)
  and `ci` (plain local dir). Marts are `materialized: external` → written back to
  `{DATALENS_LAKE_URI}/gold/*.parquet`. `external_root` set in profiles.yml.
  Staging: `stg_job_postings` (cross-day dedupe via row_number, first/last_seen), `stg_job_skills`.
  Source location template: `{lake}/silver/adzuna/{name}/*/*.parquet`.

### Infra / tooling

- `docker/compose.dev.yml` — Postgres 16 (+ `airflow` db via `postgres-init.sql`), MinIO
  (+ bucket-creating `minio-init`), Airflow webserver+scheduler+init (custom image
  `docker/airflow.Dockerfile` with deps baked), backend (hot reload). Dev creds
  (minioadmin / admin / airflow) are local-only and intentional.
- `.github/workflows/ci.yml` — `backend` job (ruff, ruff format --check, mypy, pytest w/ 80% gate)
  and `dbt` job (build fixture lake → `dbt build` target `ci`). Frontend job comes Week 3.
- `scripts/build_fixture_lake.py` — fixtures → local lake at `.lake/` (also creates `gold/`
  dir because DuckDB COPY won't mkdir).
- `Makefile` — `dev`, `down`, `logs`, `setup` (uv venv), `test`, `lint`, `fmt`.

## 4. Decisions log (with reasons)

1. **DuckDB + Parquet on S3 + dbt external materialization** instead of a warehouse — $0,
   stateless, swap path documented. dbt models are plain SQL → portable.
2. **Airflow over Dagster/Prefect** — #1 AU job-ad keyword. Custom image, LocalExecutor in dev.
3. **Adzuna over scraping** — legal/stable; free tier. Query-param auth is its only mode.
4. **Skill extraction is regex taxonomy, not LLM** — deterministic, free, fast; this is a
   deliberate interview talking point (right tool vs LLM-everything).
5. **OpenAI behind internal `LLMClient` abstraction** (Week 5) — user has credits.
6. **Frontend = Next.js + TS on Vercel free tier** (Week 3); AWS budget goes to data plane.
7. **Monorepo**, conventional commits, **no AI attribution in commits** (user setting),
   feature-branch + PR workflow from Week 2 on.
8. Read-only analytics surface: gold table allowlist + bound params; config values guarded
   against quote/semicolon injection in DuckDB `SET` (can't be parameterized).

## 5. Environment & workflow facts (save re-discovery time)

- WSL2 Ubuntu; Python 3.12.3; **uv** for venvs (`backend/.venv`); node v25 present; Docker Desktop.
- **No `gh` CLI** — repo ops via SSH remote; PRs opened by user in browser
  (`https://github.com/devNavraj/datalens/pull/new/<branch>`).
- Git identity: global `devNavraj <praabiin.rai@gmail.com>` (repo-local config removed;
  initial commits were rewritten to this identity before first push).
- Verification one-liners (run from `backend/`):
  `.venv/bin/ruff format -q . && .venv/bin/ruff check -q . && .venv/bin/mypy src && .venv/bin/pytest -q`
- dbt locally: `python scripts/build_fixture_lake.py .lake` then
  `DATALENS_LAKE_URI=$PWD/.lake DBT_TARGET=ci DBT_TARGET_PATH=/tmp/dbt_target DBT_LOG_PATH=/tmp/dbt_logs backend/.venv/bin/dbt build --project-dir pipelines/dbt --profiles-dir pipelines/dbt`
- Workflow per session: feature branch → TDD → ruff/mypy/pytest green → **code-reviewer agent
  pass** (user's standing rule) → fix CRITICAL/HIGH → conventional commit → push → PR link.
- pandera: use `import pandera.pandas as pa`; tz-aware dtype is the string
  `"datetime64[ns, UTC]"`; date columns via `pandas_engine.Date()` (core `pa.dtypes.DateTime(tz=)`
  does NOT work).

## 6. Known gaps / paper cuts (intentional, revisit later)

- `Warehouse` `_configure_s3` path (lines ~28–42) untested — needs MinIO; covered manually when stack boots.
- Real AWS S3 auth for DuckDB/dbt (credential chain) deferred to Week 6 Terraform work.
- `get_warehouse` lru_cache singleton never closes its DuckDB conn — fine for in-memory; revisit if file-backed.
- Starlette TestClient deprecation warning (httpx) — harmless, pinned by FastAPI.
- `js`/`ts` taxonomy aliases are low-precision but boundary-guarded; acceptable.
- Frontend/, infra/ are placeholder READMEs until Weeks 3/6.

## 7. Next: Week 3 (not started)

From [TASK_LIST](TASK_LIST.md):
1. **CSV upload connector**: upload endpoint → bronze → schema inference → silver → per-dataset gold.
2. **Profiling service**: types, nulls, distributions, cardinality, quality score.
3. **`csv_process` DAG** triggered via Airflow REST API from the backend.
4. **Next.js scaffold** (`frontend/`): layout, Datasets page, upload flow, profile view —
   plus CI `frontend` job (eslint + tsc + vitest) which is already stubbed as a comment in ci.yml.
5. **Job Market Trends page** (Recharts) consuming the Week 2 API endpoints.
6. Design note: uploaded datasets need a registry — first real use of Postgres app DB
   (SQLAlchemy models + Alembic migration; deps not yet added).

**Definition of done every task:** tests first where practical, ≥80% backend coverage, CI green,
no secrets in repo, conventional commit.
