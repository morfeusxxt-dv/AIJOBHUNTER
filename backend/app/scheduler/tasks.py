from apscheduler.schedulers.asyncio import AsyncScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import async_session_factory
from app.core.config import settings
from app.core.logger import logger
from app.repositories.job_repository import JobRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.log_repository import LogRepository
from app.linkedin.workflow import LinkedInWorkflow

# We will use BackgroundScheduler/AsyncioScheduler for APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def scheduled_crawl():
    logger.info("Executing scheduled crawler flow...")
    async with async_session_factory() as session:
        job_repo = JobRepository(session)
        company_repo = CompanyRepository(session)
        app_repo = ApplicationRepository(session)
        settings_repo = SettingsRepository(session)
        log_repo = LogRepository(session)
        
        wf = LinkedInWorkflow(job_repo, company_repo, app_repo, settings_repo, log_repo)
        try:
            await wf.run_crawler_flow()
        except Exception as e:
            logger.error(f"Error in scheduled crawl task: {str(e)}")

async def scheduled_apply():
    logger.info("Executing scheduled apply flow...")
    async with async_session_factory() as session:
        job_repo = JobRepository(session)
        company_repo = CompanyRepository(session)
        app_repo = ApplicationRepository(session)
        settings_repo = SettingsRepository(session)
        log_repo = LogRepository(session)
        
        wf = LinkedInWorkflow(job_repo, company_repo, app_repo, settings_repo, log_repo)
        try:
            await wf.run_apply_flow()
        except Exception as e:
            logger.error(f"Error in scheduled apply task: {str(e)}")

def setup_scheduler():
    scheduler.add_job(scheduled_crawl, 'interval', minutes=settings.CRAWL_INTERVAL_MINUTES, id='crawl_job', replace_existing=True)
    scheduler.add_job(scheduled_apply, 'interval', minutes=settings.APPLY_INTERVAL_MINUTES, id='apply_job', replace_existing=True)
    scheduler.start()
    logger.info("APScheduler initialized successfully with crawl and apply jobs.")
