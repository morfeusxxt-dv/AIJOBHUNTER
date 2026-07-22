import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class JobStatus(str, enum.Enum):
    NEW = "NEW"
    ANALYZING = "ANALYZING"
    WAITING = "WAITING"
    READY = "READY"
    APPLIED = "APPLIED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    requirements: Mapped[str] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    easy_apply: Mapped[bool] = mapped_column(Boolean, default=False)
    level: Mapped[str] = mapped_column(String(100), nullable=True)
    technologies: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    status: Mapped[JobStatus] = mapped_column(String(50), default=JobStatus.NEW)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="jobs")
    application = relationship("Application", back_populates="job", uselist=False)
