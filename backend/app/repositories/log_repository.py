from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.log import LogEntry
from app.repositories.base import BaseRepository

class LogRepository(BaseRepository[LogEntry]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(LogEntry, db_session)

    async def get_recent_logs(self, limit: int = 100) -> List[LogEntry]:
        query = select(LogEntry).order_by(LogEntry.created_at.desc()).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def log(self, service: str, message: str, level: str = "INFO", details: dict = None) -> LogEntry:
        entry = LogEntry(
            service=service,
            message=message,
            level=level,
            details=details or {}
        )
        self.db_session.add(entry)
        await self.db_session.commit()
        await self.db_session.refresh(entry)
        return entry
