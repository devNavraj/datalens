# Portfolio Plan — turning DataLens into job offers

## The 3-minute recruiter journey
1. Resume/LinkedIn → **live demo URL** → lands on Job Market Trends page (no login, demo mode)
2. Uploads own CSV or clicks a sample → profile, charts, insight cards appear
3. Asks the chat one question → streamed answer with the SQL shown
4. Clicks GitHub link → README hero GIF, architecture diagram, green badges, ADRs

## README must-haves
- One-line value prop + live demo link + 30-sec GIF at the very top
- Architecture diagram (mermaid from ARCHITECTURE.md)
- "Skills demonstrated" table linking to the actual code (connector interface, DAG, dbt models, guardrails, forecasting backtest)
- Quickstart: `docker compose up` → working local stack
- Badges: CI, coverage, license

## Blog posts (publish on dev.to/Medium + LinkedIn repost)
1. **"I built a lakehouse for $18/month"** — DuckDB + S3 + dbt + Airflow on one EC2 box; cost table; when you actually need Snowflake. (Publish at MVP launch)
2. **"Letting an LLM query my warehouse without losing sleep"** — NL→SQL guardrails: sqlglot validation, read-only connections, eval set in CI. (Draft week 6)
3. (Post-MVP) "Forecasting AU tech skill demand" — findings post; recruiters share content about their own market.

## Resume bullets this project generates
- Built end-to-end data platform on AWS: Airflow-orchestrated medallion lakehouse (S3/Parquet/DuckDB/dbt) ingesting daily AU job-market data
- Developed FastAPI + Next.js/TypeScript analytics product with time-series forecasting (statsmodels/sklearn) and anomaly detection
- Shipped guarded NL→SQL GenAI assistant with CI-enforced eval suite and provider-abstracted LLM layer
- Full IaC (Terraform), CI/CD (GitHub Actions), 80%+ test coverage, ≤$20/mo runtime cost

## LinkedIn cadence
Week 3: short post with upload-to-insights GIF (WIP framing) · Week 6: launch post + blog #1 · Then one insight-screenshot post per fortnight from the live job-market data (each one demos the product while saying something useful about the AU market).
