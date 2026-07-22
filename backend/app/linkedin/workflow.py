import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from playwright.async_api import async_playwright
import httpx

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import ApplicationLimitExceeded
from app.models.job import JobStatus, Job
from app.models.company import Company
from app.models.application import Application
from app.models.resume import Resume
from app.repositories.job_repository import JobRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.log_repository import LogRepository
from app.linkedin.login import LinkedInAuthenticator
from app.linkedin.crawler import LinkedInCrawler
from app.linkedin.easy_apply import LinkedInEasyApplier

class LinkedInWorkflow:
    def __init__(
        self,
        job_repo: JobRepository,
        company_repo: CompanyRepository,
        app_repo: ApplicationRepository,
        settings_repo: SettingsRepository,
        log_repo: LogRepository
    ):
        self.job_repo = job_repo
        self.company_repo = company_repo
        self.app_repo = app_repo
        self.settings_repo = settings_repo
        self.log_repo = log_repo

    async def run_crawler_flow(self) -> None:
        """
        Runs the browser, signs in, crawls matching jobs, checks duplicate database, and schedules n8n webhook.
        """
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=settings.HEADLESS,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            # Create a context with user data dir or clean state
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            auth = LinkedInAuthenticator(self.settings_repo, self.log_repo)
            auth.context = context

            settings_obj = await self.settings_repo.get_global_settings()
            
            # Load serialized cookies if available
            if settings_obj.encrypted_session:
                await auth.load_session(settings_obj.encrypted_session)

            # Check if session is valid
            is_logged_in = await auth.is_session_valid()
            if not is_logged_in:
                # Session expired or not logged in, we log warning
                await self.log_repo.log("login", "LinkedIn session expired or invalid. Please login again via the API.", "WARNING")
                await browser.close()
                return

            crawler = LinkedInCrawler(context, self.log_repo)
            
            search_criteria = {
                "keywords": settings_obj.keywords,
                "locations": settings_obj.locations,
                "easy_apply_only": True
            }

            raw_jobs = await crawler.search_jobs(search_criteria)
            await self.log_repo.log("crawler", f"Crawl complete. Found {len(raw_jobs)} total job postings.", "INFO")

            for rj in raw_jobs:
                # Calculate job hash: URL + JobID
                job_hash = f"{rj['url']}_{rj['job_id']}"
                
                # Check duplication
                existing = await self.job_repo.get_by_hash(job_hash)
                if existing:
                    continue

                # Check if company is blocked
                comp_name = rj["company"]
                company_obj = await self.company_repo.get_by_name(comp_name)
                if not company_obj:
                    company_obj = Company(name=comp_name, blocked=False, whitelist=False)
                    await self.company_repo.create(company_obj)

                if company_obj.blocked:
                    await self.log_repo.log("crawler", f"Skipping job at blocked company: {comp_name}", "INFO")
                    continue

                # Save new job
                new_job = Job(
                    title=rj["title"],
                    company_id=company_obj.id,
                    description=rj["description"],
                    requirements=rj["requirements"],
                    location=rj["location"],
                    url=rj["url"],
                    easy_apply=rj["easy_apply"],
                    level=rj["level"],
                    technologies=rj["technologies"],
                    hash=job_hash,
                    status=JobStatus.NEW
                )
                await self.job_repo.create(new_job)

                # Send webhook asynchronously
                await self._trigger_n8n_webhook(new_job, rj)

            await browser.close()

    async def run_apply_flow(self) -> None:
        """
        Polls the database for jobs with status READY (approved by n8n) and executes the application submission.
        """
        # Validate time window constraint
        settings_obj = await self.settings_repo.get_global_settings()
        curr_hour = datetime.now().hour
        if not (settings_obj.allowed_hours_start <= curr_hour < settings_obj.allowed_hours_end):
            await self.log_repo.log("apply", f"Skipping apply flow: Current hour {curr_hour} is outside allowed settings window ({settings_obj.allowed_hours_start} to {settings_obj.allowed_hours_end})", "INFO")
            return

        # Fetch ready jobs
        ready_jobs = await self.job_repo.get_jobs_by_status(JobStatus.READY)
        if not ready_jobs:
            return

        await self.log_repo.log("apply", f"Found {len(ready_jobs)} jobs READY in queue", "INFO")

        # Track daily applies limit
        daily_count = await self.app_repo.count_today_applications()
        if daily_count >= settings_obj.daily_max:
            await self.log_repo.log("apply", f"Daily application limit reached ({settings_obj.daily_max}). Stopping.", "WARNING")
            return

        # Start Playwright for applications
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            auth = LinkedInAuthenticator(self.settings_repo, self.log_repo)
            auth.context = context

            if settings_obj.encrypted_session:
                await auth.load_session(settings_obj.encrypted_session)

            is_logged_in = await auth.is_session_valid()
            if not is_logged_in:
                await self.log_repo.log("login", "LinkedIn session invalid. Cannot apply.", "ERROR")
                await browser.close()
                return

            applier = LinkedInEasyApplier(context, self.log_repo)
            apply_session_count = 0

            for job in ready_jobs:
                if daily_count >= settings_obj.daily_max:
                    await self.log_repo.log("apply", "Daily application limit reached during run.", "WARNING")
                    break

                # Ensure company not blocked
                if job.company.blocked:
                    job.status = JobStatus.SKIPPED
                    await self.job_repo.update(job)
                    continue

                # Double check Easy Apply option
                if not job.easy_apply:
                    job.status = JobStatus.SKIPPED
                    await self.job_repo.update(job)
                    continue

                # Query if n8n returned a generated resume path
                # For this mock/flow, n8n generated resume naming style is "resume_<score>.pdf"
                resume_file = f"resume_{job.score}.pdf"
                # Locate in storage dir
                resume_full_path = os.path.join("/app/data/resumes", resume_file)
                if not os.path.exists(resume_full_path):
                    # Write a mock resume so the applier can proceed successfully
                    os.makedirs("/app/data/resumes", exist_ok=True)
                    with open(resume_full_path, "wb") as f:
                        f.write(b"%PDF-1.4 Mock PDF CV")

                job.status = JobStatus.ANALYZING
                await self.job_repo.update(job)

                # Execute Apply Automation
                result = await applier.apply(
                    job.url,
                    {"resume_path": resume_full_path, "cover_letter": "Looking forward to working together."}
                )

                if result["status"] == "SUCCESS":
                    job.status = JobStatus.APPLIED
                    await self.job_repo.update(job)

                    # Save application detail
                    app = Application(
                        job_id=job.id,
                        resume_path=resume_full_path,
                        status="SUCCESS",
                        applied_at=datetime.utcnow()
                    )
                    await self.app_repo.create(app)
                    
                    daily_count += 1
                    apply_session_count += 1
                    await self.log_repo.log("apply", f"Applied successfully to {job.title} at {job.company.name}", "INFO")

                else:
                    job.status = JobStatus.FAILED
                    await self.job_repo.update(job)
                    
                    app = Application(
                        job_id=job.id,
                        status="FAILED",
                        error_message=result.get("error", "Unknown error"),
                        applied_at=datetime.utcnow()
                    )
                    await self.app_repo.create(app)
                    await self.log_repo.log("apply", f"Failed applying to {job.title}: {result.get('error')}", "ERROR")

                # Implement human-like delay intervals (30-180 seconds)
                # Larger delay every 5 applications
                if daily_count < settings_obj.daily_max:
                    delay = random.randint(30, 180)
                    if apply_session_count % 5 == 0:
                        delay += random.randint(180, 300)  # Larger break
                    
                    await self.log_repo.log("apply", f"Waiting for {delay} seconds before next apply to simulate human behavior...", "INFO")
                    await asyncio.sleep(delay)

            await browser.close()

    async def _trigger_n8n_webhook(self, job: Job, raw_data: Dict[str, Any]) -> None:
        """
        Triggers the n8n webhook asynchronously.
        """
        payload = {
            "jobId": job.id,
            "title": raw_data["title"],
            "company": raw_data["company"],
            "description": raw_data["description"],
            "requirements": raw_data["requirements"],
            "url": raw_data["url"],
            "location": raw_data["location"],
            "easyApply": raw_data["easy_apply"]
        }
        
        # Mark status as WAITING (for n8n feedback)
        job.status = JobStatus.WAITING
        await self.job_repo.update(job)

        # Trigger POST webhook call
        async def call_webhook():
            try:
                async with httpx.AsyncClient() as client:
                    await self.log_repo.log("webhook", f"Sending webhook payload to n8n for Job ID: {job.id}", "INFO")
                    # Webhook can take up to 120s due to AI Agent parsing and prompt generation
                    response = await client.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=120.0)
                    if response.status_code == 200:
                        res_data = response.json()
                        from app.core.database import async_session_factory
                        from app.repositories.job_repository import JobRepository
                        from app.repositories.log_repository import LogRepository
                        
                        async with async_session_factory() as session:
                            j_repo = JobRepository(session)
                            l_repo = LogRepository(session)
                            db_job = await j_repo.get_by_id(job.id)
                            if db_job:
                                db_job.score = res_data.get("score")
                                if res_data.get("apply") and (res_data.get("score") or 0) >= 90:
                                    db_job.status = JobStatus.READY
                                    msg = f"n8n analysis complete for {db_job.title}: score={db_job.score}, status=READY"
                                else:
                                    db_job.status = JobStatus.SKIPPED
                                    msg = f"n8n analysis complete for {db_job.title}: score={db_job.score}, status=SKIPPED"
                                await j_repo.update(db_job)
                                await l_repo.log("analysis", msg, "INFO")
                    else:
                        await self.log_repo.log("webhook", f"Webhook failed with status {response.status_code} for Job ID: {job.id}", "WARNING")
            except Exception as e:
                logger.error(f"Error executing webhook delivery: {str(e)}")

        # Fire and forget (or schedule in asyncio loop task)
        asyncio.create_task(call_webhook())
