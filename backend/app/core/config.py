import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API configs
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Job Hunter"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/ai_job_hunter"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/ai_job_hunter"

    # Security & Encryption
    ENCRYPTION_KEY: str = "3kR8hJn29LmPqR4tV5wY6zB7eG8hK9jN2pQ5sT8wY1z="  # 32 url-safe base64-encoded bytes

    # Webhook
    N8N_WEBHOOK_URL: str = "http://n8n:5678/webhook/job-analysis"

    # Playwright Settings
    HEADLESS: bool = True
    USER_DATA_DIR: str = "/app/data/playwright_user_data"

    # Scheduling
    CRAWL_INTERVAL_MINUTES: int = 60
    APPLY_INTERVAL_MINUTES: int = 15

settings = Settings()
