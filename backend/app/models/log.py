from datetime import datetime
from typing import Optional
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class LogEntry(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    service: Mapped[str] = mapped_column(String(50), index=True)  # crawler, login, analysis, webhook, apply, error
    message: Mapped[str] = mapped_column(nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="INFO")
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
