# PRD — DataLens (working name)

**A pluggable data intelligence platform: ingest any dataset, get analytics, ML forecasts, and GenAI-powered insights from one dashboard.**

> Working name `DataLens` — rename freely before going public.

## 1. Why this project exists

Portfolio project for Nawaraj Rai (MIT in AI, Macquarie University; ex-COTIVITI software engineer) targeting **hybrid Data + AI Engineer roles in Australia**. The platform itself must be genuinely useful, but every architectural choice doubles as evidence of a skill hirers screen for.

**Skills it must demonstrate:** ETL/ELT pipelines, warehousing/lakehouse, orchestration (Airflow), analytics, classic ML (forecasting, anomaly detection), GenAI/agentic workflows, API development (FastAPI), full-stack TypeScript (Next.js), AWS, IaC, CI/CD, testing.

## 2. Product vision

A generic platform where a user connects or uploads a data source and immediately gets:

1. **Auto-profiling** — schema inference, quality report, distributions, missing-value analysis.
2. **Analytics dashboard** — interactive charts over the cleaned (gold-layer) data.
3. **ML layer** — time-series forecasting and anomaly detection where the data supports it.
4. **GenAI layer** — natural-language Q&A over the data ("chat with your data" via guarded NL→SQL), plus auto-generated narrative insights ("3 things that changed this month").

Generic at the core (connector plugin architecture); demonstrated on concrete data in the MVP.

## 3. Users

| Persona | Need |
|---|---|
| Hiring manager / recruiter (primary audience) | Click live demo, see depth in 3 minutes |
| Analyst-type end user | Upload CSV, explore, ask questions in plain English |
| Nawaraj (dogfooding) | AU tech job-market trends to guide his own job hunt |

## 4. MVP scope (4–6 weeks)

### Data connectors
- ✅ **CSV/Excel upload** — any tabular file → profile → analytics → chat.
- ✅ **AU job market** — scheduled ingestion from the **Adzuna API** (free tier, legal, AU coverage): tech job postings → skill-demand trends, salary distributions, location breakdowns, demand forecasting.
- 🔜 Post-MVP: AU open data API connector (ABS/AEMO), synthetic event-stream connector.

### Features (MVP)
- Upload + connector management UI
- Bronze/silver/gold lakehouse pipeline (S3 + Parquet + DuckDB + dbt), orchestrated by Airflow
- Dataset profiling report
- Dashboard: charts per dataset + curated "Job Market Trends" page
- Forecasting (skill demand / any time-series column) + anomaly detection
- GenAI insights: narrative summary generation + chat-with-data (NL→SQL with read-only guardrails)
- LLM provider abstraction (OpenAI now, swappable)
- Single-user auth (simple login) — multi-tenant is out of scope
- Deployed live demo on AWS, CI/CD via GitHub Actions

### Explicitly out of MVP scope
Multi-tenancy/orgs, RBAC, streaming ingestion, fine-tuning, computer vision module, mobile, billing.

## 5. Success criteria

- Live URL works end-to-end: upload a CSV → insights in under 2 minutes.
- Job-market pipeline runs daily unattended for 2+ weeks.
- Repo: architecture diagram, ADRs, ≥80% backend test coverage, green CI badge.
- Infra cost ≤ $30/month (target ~$20).
- 2 technical blog posts published.

## 6. Risks

| Risk | Mitigation |
|---|---|
| Scope creep (the "generic" trap) | Connector interface generic; only 2 connectors in MVP |
| Adzuna API limits/changes | Cache raw responses in bronze layer; connector abstraction allows swap |
| NL→SQL hallucination/injection | Read-only DuckDB connection, schema-scoped prompts, query validation, row limits |
| LLM cost runaway on public demo | Per-session rate limits, token budget, cheap model (gpt-4o-mini class) |
| AWS cost runaway | Single small instance + S3; budget alarm at $25 |
