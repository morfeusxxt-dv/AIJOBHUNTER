from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.job import JobStatus
from app.schemas.company import CompanyInDB

class JobBase(BaseModel):
    title: str
    description: str
    requirements: Optional[str] = None
    location: Optional[str] = None
    url: str
    easy_apply: bool = False
    level: Optional[str] = None
    technologies: List[str] = []

class JobCreate(JobBase):
    company_name: str

class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    score: Optional[int] = None
    requirements: Optional[str] = None
    technologies: Optional[List[str]] = None

class JobInDB(JobBase):
    id: int
    company_id: int
    company: CompanyInDB
    hash: str
    status: JobStatus
    score: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
