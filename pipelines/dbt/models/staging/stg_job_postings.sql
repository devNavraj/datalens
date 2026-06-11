-- Latest version of each posting across all ingest dates,
-- with first/last seen tracking for lifetime analysis.
with ranked as (
    select
        *,
        row_number() over (partition by job_id order by ingest_date desc) as rn,
        min(ingest_date) over (partition by job_id) as first_seen_date,
        max(ingest_date) over (partition by job_id) as last_seen_date
    from {{ source('silver', 'job_postings') }}
)

select
    job_id,
    title,
    description,
    company,
    location,
    state,
    salary_min,
    salary_max,
    salary_is_predicted,
    created_at,
    cast(created_at as date) as posting_date,
    category,
    contract_type,
    contract_time,
    url,
    first_seen_date,
    last_seen_date
from ranked
where rn = 1
