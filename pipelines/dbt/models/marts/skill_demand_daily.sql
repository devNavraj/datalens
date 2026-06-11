-- Postings per skill per posting day — the forecasting input (Week 4).
select
    p.posting_date,
    s.skill,
    s.skill_category,
    count(distinct s.job_id) as postings
from {{ ref('stg_job_skills') }} s
join {{ ref('stg_job_postings') }} p using (job_id)
group by p.posting_date, s.skill, s.skill_category
