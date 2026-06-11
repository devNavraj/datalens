FROM apache/airflow:2.10.4-python3.12

# Pipeline dependencies baked in (replaces dev-only _PIP_ADDITIONAL_REQUIREMENTS,
# which reinstalled on every container start). datalens itself is volume-mounted
# via PYTHONPATH in dev; the prod image will pip-install it (Week 6).
USER airflow
RUN pip install --no-cache-dir \
    "httpx>=0.28" \
    "tenacity>=9.0" \
    "pydantic-settings>=2.7" \
    "boto3>=1.35" \
    "pandas>=2.2" \
    "pyarrow>=18.0" \
    "pandera>=0.24" \
    "duckdb>=1.1" \
    "dbt-duckdb>=1.9"
