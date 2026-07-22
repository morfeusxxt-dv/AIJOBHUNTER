import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository

@pytest.mark.asyncio
async def test_create_and_retrieve_job(db_session: AsyncSession):
    company_repo = CompanyRepository(db_session)
    job_repo = JobRepository(db_session)

    # 1. Create company
    company = Company(name="Google", blocked=False)
    await company_repo.create(company)
    assert company.id is not None

    # 2. Create job
    job = Job(
        title="Staff Software Engineer",
        company_id=company.id,
        description="Write beautiful code",
        url="https://google.com/jobs/1",
        easy_apply=True,
        hash="google_1",
        status=JobStatus.NEW
    )
    await job_repo.create(job)
    assert job.id is not None

    # 3. Retrieve and test duplication checks
    fetched = await job_repo.get_by_hash("google_1")
    assert fetched is not None
    assert fetched.title == "Staff Software Engineer"

    # Test count by status
    counts = await job_repo.count_by_status()
    assert counts.get(JobStatus.NEW) == 1
