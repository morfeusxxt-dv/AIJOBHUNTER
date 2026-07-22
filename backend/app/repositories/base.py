from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.base import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db_session: AsyncSession):
        self.model = model
        self.db_session = db_session

    async def get_by_id(self, id: any) -> Optional[T]:
        return await self.db_session.get(self.model, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        self.db_session.add(entity)
        await self.db_session.commit()
        await self.db_session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        await self.db_session.commit()
        await self.db_session.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self.db_session.delete(entity)
        await self.db_session.commit()
