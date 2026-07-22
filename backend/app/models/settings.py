from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class SettingsModel(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    locations: Mapped[List[str]] = mapped_column(JSON, default=list)
    remote: Mapped[bool] = mapped_column(default=True)
    hybrid: Mapped[bool] = mapped_column(default=False)
    onsite: Mapped[bool] = mapped_column(default=False)
    score_min: Mapped[int] = mapped_column(Integer, default=90)
    daily_max: Mapped[int] = mapped_column(Integer, default=15)
    allowed_hours_start: Mapped[int] = mapped_column(Integer, default=9)  # 9 AM
    allowed_hours_end: Mapped[int] = mapped_column(Integer, default=18)    # 6 PM
    
    # Encrypted session string (Playwright browser state cookies)
    encrypted_session: Mapped[Optional[str]] = mapped_column(default=None)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
