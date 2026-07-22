from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.repositories.job_repository import JobRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.company_repository import CompanyRepository

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db_session)):
    job_repo = JobRepository(db)
    app_repo = ApplicationRepository(db)

    # 1. Total jobs found
    counts = await job_repo.count_by_status()
    total_jobs = sum(counts.values())

    # 2. Total applied
    total_applied = counts.get("APPLIED", 0)

    # 3. Total analyzed (all status except NEW)
    total_analyzed = sum(counts.get(s, 0) for s in ["ANALYZING", "WAITING", "READY", "APPLIED", "FAILED", "SKIPPED"])

    # 4. Score average
    avg_score = await job_repo.get_average_score()

    # 5. Daily applications
    daily_applies = await app_repo.count_today_applications()

    # 6. Top Technologies found
    recent_jobs = await job_repo.get_recent_jobs(limit=100)
    tech_counts = {}
    for job in recent_jobs:
        if job.technologies:
            for tech in job.technologies:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1
    
    sorted_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_technologies = [{"name": name, "count": count} for name, count in sorted_techs]

    return {
        "total_jobs": total_jobs,
        "total_analyzed": total_analyzed,
        "total_applied": total_applied,
        "average_score": round(avg_score, 1),
        "daily_applies": daily_applies,
        "top_technologies": top_technologies
    }
