from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import async_playwright

from app.core.config import settings
from app.core.database import get_db_session
from app.repositories.settings_repository import SettingsRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.log_repository import LogRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.schemas.settings import SettingsInDB, SettingsUpdate
from app.linkedin.login import LinkedInAuthenticator

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class BlacklistRequest(BaseModel):
    company_name: str
    blocked: bool

@router.get("", response_model=SettingsInDB)
async def get_settings(db: AsyncSession = Depends(get_db_session)):
    settings_repo = SettingsRepository(db)
    return await settings_repo.get_global_settings()

@router.put("", response_model=SettingsInDB)
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db_session)):
    settings_repo = SettingsRepository(db)
    settings_obj = await settings_repo.get_global_settings()
    
    settings_obj.keywords = payload.keywords
    settings_obj.locations = payload.locations
    settings_obj.remote = payload.remote
    settings_obj.hybrid = payload.hybrid
    settings_obj.onsite = payload.onsite
    settings_obj.score_min = payload.score_min
    settings_obj.daily_max = payload.daily_max
    settings_obj.allowed_hours_start = payload.allowed_hours_start
    settings_obj.allowed_hours_end = payload.allowed_hours_end

    await settings_repo.update(settings_obj)
    return settings_obj

@router.post("/login")
async def trigger_manual_login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Simulates automated browser login flow using user-provided credentials
    to fetch cookies securely. Stores state in DB using Cryptography encryption.
    """
    settings_repo = SettingsRepository(db)
    log_repo = LogRepository(db)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=settings.HEADLESS,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        auth = LinkedInAuthenticator(settings_repo, log_repo)
        auth.context = context

        try:
            success = await auth.login({"username": payload.username, "password": payload.password})
            if success:
                return {"status": "success", "message": "Logged in successfully. Cookies saved."}
            else:
                raise HTTPException(status_code=400, detail="Login failed. Check logs or verify MFA/checkpoint is requested.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")
        finally:
            await browser.close()

@router.post("/blacklist")
async def update_blacklist(payload: BlacklistRequest, db: AsyncSession = Depends(get_db_session)):
    comp_repo = CompanyRepository(db)
    company = await comp_repo.get_by_name(payload.company_name)
    
    if not company:
        from app.models.company import Company
        company = Company(name=payload.company_name, blocked=payload.blocked)
        await comp_repo.create(company)
    else:
        company.blocked = payload.blocked
        await comp_repo.update(company)

    return {"status": "success", "company": company.name, "blocked": company.blocked}
