import os
import random
from typing import Dict, Any
from playwright.async_api import BrowserContext, Page
from app.core.providers import ApplyProvider
from app.core.logger import logger
from app.repositories.log_repository import LogRepository

class LinkedInEasyApplier(ApplyProvider):
    def __init__(self, context: BrowserContext, log_repo: LogRepository):
        self.context = context
        self.log_repo = log_repo

    async def apply(self, job_url: str, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automate the Easy Apply flow on a job details page.
        """
        resume_path = application_data.get("resume_path")
        cover_letter = application_data.get("cover_letter", "")
        
        page = await self.context.new_page()
        try:
            await self.log_repo.log("apply", f"Navigating to job page for application: {job_url}", "INFO")
            await page.goto(job_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Check for Easy Apply button
            apply_button = page.locator("button.jobs-apply-button").first
            if not await apply_button.is_visible():
                msg = "Easy Apply button not visible or already applied"
                await self.log_repo.log("apply", msg, "WARNING")
                return {"status": "FAILED", "error": msg}

            await apply_button.click()
            await page.wait_for_timeout(2000)

            # Loop through steps of the Easy Apply modal
            max_steps = 10
            step_count = 0
            
            while step_count < max_steps:
                step_count += 1
                
                # Try to upload resume if required on current page
                file_input = page.locator("input[type='file'][id*='resume'], input[type='file'][name*='resume']").first
                if await file_input.is_visible() and resume_path and os.path.exists(resume_path):
                    await self.log_repo.log("apply", f"Uploading resume from {resume_path}", "INFO")
                    await file_input.set_input_files(resume_path)
                    await page.wait_for_timeout(2000)

                # Try to handle cover letter
                cl_input = page.locator("textarea[id*='cover'], textarea[name*='cover']").first
                if await cl_input.is_visible() and cover_letter:
                    await self.log_repo.log("apply", "Filling cover letter text area", "INFO")
                    await cl_input.fill(cover_letter)
                    await page.wait_for_timeout(1000)

                # Solve common questions (radio buttons, checkboxes, simple inputs)
                await self._answer_questions(page)

                # Locate navigation buttons: Next, Review, Submit
                next_btn = page.locator("button:has-text('Next'), button:has-text('Avançar')").first
                review_btn = page.locator("button:has-text('Review'), button:has-text('Revisar')").first
                submit_btn = page.locator("button:has-text('Submit'), button:has-text('Enviar')").first

                if await submit_btn.is_visible():
                    await self.log_repo.log("apply", "Clicking submit application button", "INFO")
                    await submit_btn.click()
                    await page.wait_for_timeout(5000)
                    
                    # Confirm success
                    await self.log_repo.log("apply", "Application submitted successfully", "INFO")
                    return {"status": "SUCCESS"}
                
                elif await review_btn.is_visible():
                    await self.log_repo.log("apply", "Clicking Review button", "INFO")
                    await review_btn.click()
                    await page.wait_for_timeout(2000)
                    
                elif await next_btn.is_visible():
                    await self.log_repo.log("apply", "Clicking Next button", "INFO")
                    await next_btn.click()
                    await page.wait_for_timeout(2000)
                    
                else:
                    # If we get stuck, check if there's an error on the page
                    error_msg = "Stuck in Easy Apply wizard; no navigation button found or form has errors."
                    await self.log_repo.log("apply", error_msg, "ERROR")
                    return {"status": "FAILED", "error": error_msg}

            return {"status": "FAILED", "error": "Exceeded maximum wizard steps"}

        except Exception as e:
            await self.log_repo.log("apply", f"Exception during application: {str(e)}", "ERROR")
            return {"status": "FAILED", "error": str(e)}
        finally:
            await page.close()

    async def _answer_questions(self, page: Page):
        """
        Attempts to fill typical question inputs if present.
        """
        try:
            # 1. Look for text inputs
            inputs = page.locator("input[type='text']")
            count = await inputs.count()
            for i in range(count):
                inp = inputs.nth(i)
                label_text = await page.locator(f"label[for='{await inp.get_attribute('id')}']").text_content() or ""
                label_text = label_text.lower()
                
                # Check for experience years questions
                if "years" in label_text or "experiência" in label_text:
                    await inp.fill("3")
                elif "salary" in label_text or "pretensão" in label_text:
                    await inp.fill("8000")
                elif not await inp.input_value():
                    await inp.fill("Yes")

            # 2. Look for radio buttons/checkboxes (Yes / No)
            radio_groups = page.locator(".fb-form-element-wrapper")
            rg_count = await radio_groups.count()
            for i in range(rg_count):
                rg = radio_groups.nth(i)
                yes_opt = rg.locator("label:has-text('Yes'), label:has-text('Sim')").first
                if await yes_opt.is_visible():
                    await yes_opt.click()

        except Exception as q_err:
            logger.debug(f"Non-critical issue answering custom questions: {str(q_err)}")
