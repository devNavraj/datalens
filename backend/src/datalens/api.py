"""HTTP API: dataset catalogue and job-market analytics endpoints."""

from datetime import date
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from datalens.config import Settings
from datalens.warehouse import GOLD_TABLES, JobMarketService, Warehouse

router = APIRouter(prefix="/api")


@lru_cache
def get_warehouse() -> Warehouse:
    return Warehouse(Settings())


def get_job_market(warehouse: Annotated[Warehouse, Depends(get_warehouse)]) -> JobMarketService:
    return JobMarketService(warehouse)


JobMarket = Annotated[JobMarketService, Depends(get_job_market)]


class DatasetInfo(BaseModel):
    name: str
    tables: list[str]


class TopSkill(BaseModel):
    skill: str
    skill_category: str
    postings_count: int


class TrendPoint(BaseModel):
    posting_date: date
    postings: int


class SkillSalary(BaseModel):
    skill: str
    skill_category: str
    sample_size: int
    avg_salary: float
    median_salary: float
    min_salary: float
    max_salary: float


class MarketSummary(BaseModel):
    total_postings: int
    companies: int
    earliest_posting: date | None
    latest_posting: date | None


@router.get("/datasets")
def list_datasets() -> list[DatasetInfo]:
    return [DatasetInfo(name="adzuna", tables=sorted(GOLD_TABLES))]


@router.get("/job-market/summary")
def market_summary(service: JobMarket) -> MarketSummary:
    return MarketSummary(**service.summary())


@router.get("/job-market/skills/top")
def top_skills(
    service: JobMarket, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[TopSkill]:
    return [TopSkill(**row) for row in service.top_skills(limit)]


@router.get("/job-market/skills/{skill}/trend")
def skill_trend(service: JobMarket, skill: str) -> list[TrendPoint]:
    rows = service.skill_trend(skill)
    if not rows:
        raise HTTPException(status_code=404, detail=f"no demand data for skill {skill!r}")
    return [TrendPoint(**row) for row in rows]


@router.get("/job-market/salaries")
def salaries(
    service: JobMarket,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    min_sample_size: Annotated[int, Query(ge=1)] = 1,
) -> list[SkillSalary]:
    return [SkillSalary(**row) for row in service.salaries(limit, min_sample_size)]
