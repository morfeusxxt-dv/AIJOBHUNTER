from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class CompanyBase(BaseModel):
    name: str
    blocked: bool = False
    whitelist: bool = False

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    blocked: Optional[bool] = None
    whitelist: Optional[bool] = None



class CompanyInDB(CompanyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
