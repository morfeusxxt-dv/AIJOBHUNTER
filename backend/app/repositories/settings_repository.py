from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.settings import SettingsModel
from app.repositories.base import BaseRepository

class SettingsRepository(BaseRepository[SettingsModel]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(SettingsModel, db_session)

    async def get_global_settings(self) -> SettingsModel:
        # ID is fixed to 1 for global settings
        query = select(SettingsModel).where(SettingsModel.id == 1)
        result = await self.db_session.execute(query)
        settings_obj = result.scalar_one_or_none()
        
        if not settings_obj:
            settings_obj = SettingsModel(
                id=1,
                keywords=["Python", "FastAPI", "React", "Node.js", "Backend"],
                locations=["Brasil", "Remote"],
                remote=True,
                hybrid=True,
                onsite=False,
                score_min=90,
                daily_max=15,
                allowed_hours_start=9,
                allowed_hours_end=18
            )
            self.db_session.add(settings_obj)
            await self.db_session.commit()
            await self.db_session.refresh(settings_obj)
            
        return settings_obj
