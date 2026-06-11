-- Salary stats per skill from postings with real (non-predicted) salary ranges.
select
    s.skill,
    s.skill_category,
    count(distinct p.job_id) as sample_size,
    avg((p.salary_min + p.salary_max) / 2.0) as avg_salary,
    median((p.salary_min + p.salary_max) / 2.0) as median_salary,
    min(p.salary_min) as min_salary,
    max(p.salary_max) as max_salary
from {{ ref('stg_job_skills') }} s
join {{ ref('stg_job_postings') }} p using (job_id)
where p.salary_min is not null
  and p.salary_max is not null
  and not p.salary_is_predicted
group by s.skill, s.skill_category
