select
    job_id,
    title,
    company,
    location,
    state,
    salary_min,
    salary_max,
    (salary_min + salary_max) / 2.0 as salary_mid,
    salary_is_predicted,
    created_at,
    posting_date,
    category,
    contract_type,
    contract_time,
    url,
    first_seen_date,
    last_seen_date
from {{ ref('stg_job_postings') }}
