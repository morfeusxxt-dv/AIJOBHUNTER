from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class SettingsBase(BaseModel):
    keywords: List[str] = []
    locations: List[str] = []
    remote: bool = True
    hybrid: bool = False
    onsite: bool = False
    score_min: int = 90
    daily_max: int = 15
    allowed_hours_start: int = 9
    allowed_hours_end: int = 18

class SettingsUpdate(SettingsBase):
    pass

class SettingsInDB(SettingsBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
