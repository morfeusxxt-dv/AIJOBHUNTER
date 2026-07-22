from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db_session
from app.models.job import JobStatus
from app.repositories.job_repository import JobRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.log_repository import LogRepository
from app.schemas.job import JobInDB
from app.linkedin.workflow import LinkedInWorkflow

router = APIRouter()

class AnalysisResponse(BaseModel):
    apply: bool
    score: int
    resume: str
    coverLetter: Optional[str] = None
    highlightSkills: List[str] = []
    missingSkills: List[str] = []

@router.get("", response_model=List[JobInDB])
async def list_jobs(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    job_repo = JobRepository(db)
    return await job_repo.get_all(skip, limit)

@router.get("/queue", response_model=List[JobInDB])
async def list_job_queue(db: AsyncSession = Depends(get_db_session)):
    job_repo = JobRepository(db)
    # Return recent jobs in general
    return await job_repo.get_recent_jobs(limit=50)

@router.put("/{job_id}/analysis")
async def update_job_analysis(
    job_id: int, 
    analysis: AnalysisResponse, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Endpoint for n8n to send back analysis results asynchronously.
    """
    job_repo = JobRepository(db)
    log_repo = LogRepository(db)
    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.score = analysis.score
    
    # Check eligibility rules
    # "score < 90", "no Easy Apply", "skipped/applied"
    if not analysis.apply or analysis.score < 90 or not job.easy_apply:
        job.status = JobStatus.SKIPPED
        msg = f"Job {job.title} skipped. Score: {analysis.score}, Apply decision: {analysis.apply}"
        await log_repo.log("analysis", msg, "INFO")
    else:
        job.status = JobStatus.READY
        msg = f"Job {job.title} analysis complete. READY to apply. Score: {analysis.score}"
        await log_repo.log("analysis", msg, "INFO")

    await job_repo.update(job)
    return {"status": "success"}

@router.post("/trigger/crawl")
async def trigger_crawl(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db_session)):
    """
    Manually triggers the LinkedIn crawler flow as a background task.
    """
    job_repo = JobRepository(db)
    company_repo = CompanyRepository(db)
    app_repo = ApplicationRepository(db)
    settings_repo = SettingsRepository(db)
    log_repo = LogRepository(db)
    
    workflow = LinkedInWorkflow(job_repo, company_repo, app_repo, settings_repo, log_repo)
    
    background_tasks.add_task(workflow.run_crawler_flow)
    await log_repo.log("crawler", "Manual crawler run triggered", "INFO")
    return {"message": "Crawler triggered in background"}

@router.post("/trigger/apply")
async def trigger_apply(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db_session)):
    """
    Manually triggers the LinkedIn apply flow as a background task.
    """
    job_repo = JobRepository(db)
    company_repo = CompanyRepository(db)
    app_repo = ApplicationRepository(db)
    settings_repo = SettingsRepository(db)
    log_repo = LogRepository(db)
    
    workflow = LinkedInWorkflow(job_repo, company_repo, app_repo, settings_repo, log_repo)
    
    background_tasks.add_task(workflow.run_apply_flow)
    await log_repo.log("apply", "Manual apply run triggered", "INFO")
    return {"message": "Apply triggered in background"}
