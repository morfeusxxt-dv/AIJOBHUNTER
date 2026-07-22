from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.repositories.log_repository import LogRepository
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class LogResponse(BaseModel):
    id: int
    service: str
    message: str
    level: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[LogResponse])
async def get_logs(db: AsyncSession = Depends(get_db_session)):
    log_repo = LogRepository(db)
    return await log_repo.get_recent_logs(limit=100)
