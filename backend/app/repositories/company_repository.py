from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.repositories.base import BaseRepository

class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Company, db_session)

    async def get_by_name(self, name: str) -> Optional[Company]:
        query = select(Company).where(Company.name == name)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
