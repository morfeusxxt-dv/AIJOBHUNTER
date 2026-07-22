from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ApplicationBase(BaseModel):
    job_id: int
    resume_path: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str
    error_message: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationInDB(ApplicationBase):
    id: int
    applied_at: datetime

    model_config = ConfigDict(from_attributes=True)
