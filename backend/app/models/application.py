from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, unique=True)
    resume_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    cover_letter: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # SUCCESS, ERROR
    error_message: Mapped[Optional[str]] = mapped_column(nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="application")
