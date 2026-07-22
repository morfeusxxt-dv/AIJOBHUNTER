import re
from typing import Dict, Any, List
from playwright.async_api import Page

class LinkedInJobParser:
    @staticmethod
    async def parse_job_page(page: Page, job_url: str) -> Dict[str, Any]:
        """
        Parses details from the active job detail view page.
        """
        # Wait for either the job details container or main content to load
        try:
            await page.wait_for_selector(".jobs-description", timeout=5000)
        except Exception:
            pass  # Proceed even if slow, it might already be loaded

        # Extract Title
        title = ""
        title_selectors = [
            ".job-details-jobs-unified-top-card__job-title",
            "h1.t-24",
            ".top-card-layout__title",
            "h2"
        ]
        for sel in title_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible():
                    title = (await el.text_content() or "").strip()
                    if title:
                        break
            except Exception:
                continue

        # Extract Company
        company = ""
        company_selectors = [
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__company-name",
            ".topcard__org-name-link",
            ".top-card-layout__card a"
        ]
        for sel in company_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible():
                    company = (await el.text_content() or "").strip()
                    if company:
                        break
            except Exception:
                continue

        # Extract Description
        description = ""
        desc_selectors = [
            "#job-details",
            ".jobs-description__content",
            ".jobs-box__html-content"
        ]
        for sel in desc_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible():
                    description = (await el.text_content() or "").strip()
                    if description:
                        break
            except Exception:
                continue

        # Extract Location / Work Mode
        location = ""
        loc_selectors = [
            ".job-details-jobs-unified-top-card__bullet",
            ".jobs-unified-top-card__bullet-point",
            ".topcard__flavor--bullet"
        ]
        bullets = []
        for sel in loc_selectors:
            try:
                locators = page.locator(sel)
                count = await locators.count()
                for i in range(count):
                    txt = (await locators.nth(i).text_content() or "").strip()
                    if txt:
                        bullets.append(txt)
                if bullets:
                    break
            except Exception:
                continue

        location = ", ".join(bullets) if bullets else "Remote/Brazil"

        # Check Easy Apply
        easy_apply = False
        try:
            apply_btn = page.locator("button.jobs-apply-button")
            if await apply_btn.count() > 0:
                btn_text = await apply_btn.first.text_content()
                if "Easy Apply" in (btn_text or "") or "Candidatura simplificada" in (btn_text or ""):
                    easy_apply = True
        except Exception:
            pass

        # Extract Level (Seniority)
        level = "Not Specified"
        if "senior" in title.lower() or "sr" in title.lower():
            level = "Senior"
        elif "pleno" in title.lower() or "mid" in title.lower() or "pl" in title.lower():
            level = "Pleno"
        elif "junior" in title.lower() or "jr" in title.lower():
            level = "Junior"

        # Find technologies from description
        tech_list = ["python", "django", "fastapi", "spring boot", "react", "node.js", "postgres", "aws", "docker", "kubernetes", "typescript", "javascript", "java", "c#", "go", "golang"]
        found_techs = []
        desc_lower = description.lower()
        for tech in tech_list:
            if re.search(r'\b' + re.escape(tech) + r'\b', desc_lower):
                found_techs.append(tech)

        # Extract job ID from URL
        job_id_match = re.search(r'currentJobId=(\d+)', job_url) or re.search(r'/view/(\d+)', job_url)
        job_id = job_id_match.group(1) if job_id_match else "unknown"

        return {
            "job_id": job_id,
            "title": title or "Untitled Job",
            "company": company or "Unknown Company",
            "description": description or "No description provided",
            "requirements": description,  # simplified
            "location": location,
            "easy_apply": easy_apply,
            "level": level,
            "technologies": found_techs,
            "url": job_url
        }
