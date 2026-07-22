from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.application import Application
from app.repositories.base import BaseRepository

class ApplicationRepository(BaseRepository[Application]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Application, db_session)

    async def get_by_job_id(self, job_id: int) -> Optional[Application]:
        query = select(Application).where(Application.job_id == job_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def count_today_applications(self) -> int:
        today_start = datetime.combine(date.today(), datetime.min.time())
        query = select(func.count(Application.id)).where(
            and_(
                Application.applied_at >= today_start,
                Application.status == "SUCCESS"
            )
        )
        result = await self.db_session.execute(query)
        val = result.scalar()
        return val if val is not None else 0

    async def get_applications_history(self, limit: int = 50) -> List[Application]:
        query = select(Application).options(selectinload(Application.job)).order_by(Application.applied_at.desc()).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
