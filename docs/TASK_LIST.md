# Task List — DataLens MVP (6 weeks)

Each week ends with something demoable. TDD throughout: tests first on services/connectors/guardrails.

## Week 1 — Foundations + first pipeline vertical slice ✅
- [x] Monorepo scaffold (backend, frontend, pipelines, infra, docker, CI skeleton)
- [x] Docker Compose dev stack: Postgres, Airflow, MinIO (local S3), backend
- [x] GitHub Actions: ruff + mypy + pytest on PR (frontend CI lands Week 3)
- [x] `BaseConnector` interface + tests
- [x] Adzuna connector: extract → bronze (raw JSON to S3/MinIO)
- [x] `adzuna_ingest_daily` DAG skeleton running end-to-end to bronze
- **Demo:** DAG run lands raw Adzuna data in bronze, CI green.

## Week 2 — Lakehouse + dbt + job-market gold ✅
- [x] Silver layer: typed Parquet with pandera validation, dedupe
- [x] dbt project: staging → marts (`fct_job_postings`, `dim_skills`, `skill_demand_daily`, `salary_by_skill`); dbt tests
- [x] Skill extraction from job descriptions (keyword/taxonomy-based, deterministic)
- [x] DuckDB query service in backend (read-only, gold table allowlist)
- [x] API endpoints: datasets list, job-market aggregates (top skills, trends, salaries, summary)
- **Demo:** `dbt build` green; API returns real skill-demand trends.

## Week 3 — CSV connector + profiling + dashboard skeleton
- [ ] Upload endpoint → bronze → auto schema inference → silver → per-dataset gold
- [ ] Profiling service: types, nulls, distributions, cardinality, quality score
- [ ] `csv_process` DAG triggered via Airflow REST from API
- [ ] Next.js scaffold: layout, Datasets page, upload flow, profile view
- [ ] Charts: job-market trends page (Recharts)
- **Demo:** Upload a CSV in the browser → see profile + charts.

## Week 4 — ML layer
- [ ] Time-series detection heuristic (date column + numeric metric)
- [ ] Forecasting service: ETS/SARIMA + sklearn GBM, backtest selection (MAPE), tests
- [ ] Anomaly detection: STL residual + IsolationForest
- [ ] Materialise forecasts/anomalies to gold; DAG integration; API + chart overlays
- **Demo:** Skill-demand forecast with confidence band; anomalies flagged on uploaded data.

## Week 5 — GenAI layer
- [ ] `LLMClient` abstraction + OpenAI impl + retry/budget guard, tests (mocked)
- [ ] Insight generator: profile + aggregates → structured JSON insight cards
- [ ] NL→SQL chat: schema-scoped prompt, sqlglot SELECT-only validation, LIMIT injection, read-only DuckDB, result narration; SSE streaming to chat UI
- [ ] Golden-question eval set (~15 Qs) running in CI against mocked/live flag
- [ ] Rate limiting per session (demo protection)
- **Demo:** "Which skills grew fastest last quarter?" answered correctly in chat.

## Week 6 — Deploy, polish, publish
- [ ] Terraform: VPC-lite, EC2, S3, IAM, budget alarm; Caddy TLS; domain
- [ ] Prod compose + GHCR images + Actions deploy job; Vercel frontend hookup
- [ ] Simple auth (single user + demo mode), seed demo datasets
- [ ] README: hero GIF, architecture diagram, badges, quickstart; ADRs 1–6
- [ ] 2 weeks of scheduled runs begin (leave it running while applying)
- [ ] Blog post #1 published; #2 drafted
- **Demo:** Public URL on resume.

## Post-MVP backlog
ABS/AEMO connector · synthetic event-stream connector (scale story) · LLM eval harness expansion · RAG over docs · CV module (document/chart extraction) · multi-user · ECS migration · semantic skill extraction (embeddings)

## Definition of done (every task)
Tests written first where practical · ≥80% backend coverage maintained · CI green · no secrets in repo · conventional commit.
