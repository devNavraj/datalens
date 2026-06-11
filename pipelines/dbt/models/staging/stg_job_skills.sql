-- Distinct skills per job across all ingest dates.
select distinct
    job_id,
    skill,
    skill_category
from {{ source('silver', 'job_skills') }}
