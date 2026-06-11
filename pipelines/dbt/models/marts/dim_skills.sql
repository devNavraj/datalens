select
    skill,
    skill_category,
    count(distinct job_id) as postings_count
from {{ ref('stg_job_skills') }}
group by skill, skill_category
