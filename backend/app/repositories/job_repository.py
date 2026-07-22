from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.job import Job, JobStatus
from app.repositories.base import BaseRepository

class JobRepository(BaseRepository[Job]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Job, db_session)

    async def get_by_hash(self, job_hash: str) -> Optional[Job]:
        query = select(Job).where(Job.hash == job_hash)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        query = select(Job).where(Job.status == status).options(selectinload(Job.company))
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict:
        query = select(Job.status, func.count(Job.id)).group_by(Job.status)
        result = await self.db_session.execute(query)
        return {status: count for status, count in result.all()}

    async def get_average_score(self) -> float:
        query = select(func.avg(Job.score)).where(Job.score.isnot(None))
        result = await self.db_session.execute(query)
        val = result.scalar()
        return float(val) if val is not None else 0.0

    async def get_recent_jobs(self, limit: int = 20) -> List[Job]:
        query = select(Job).order_by(Job.created_at.desc()).limit(limit).options(selectinload(Job.company))
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
