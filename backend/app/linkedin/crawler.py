import urllib.parse
from typing import List, Dict, Any
from playwright.async_api import BrowserContext, Page
from app.core.providers import JobProvider
from app.linkedin.job_parser import LinkedInJobParser
from app.core.logger import logger
from app.repositories.log_repository import LogRepository

class LinkedInCrawler(JobProvider):
    def __init__(self, context: BrowserContext, log_repo: LogRepository):
        self.context = context
        self.log_repo = log_repo

    async def search_jobs(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search LinkedIn for jobs based on settings (keywords, locations, modes).
        """
        keywords = search_criteria.get("keywords", ["Python"])
        locations = search_criteria.get("locations", ["Brazil"])
        easy_apply_only = search_criteria.get("easy_apply_only", True)

        found_jobs = []
        page = await self.context.new_page()

        try:
            for kw in keywords:
                for loc in locations:
                    await self.log_repo.log("crawler", f"Searching for keyword: '{kw}' in location: '{loc}'", "INFO")
                    
                    # Construct LinkedIn search URL
                    q_kw = urllib.parse.quote(kw)
                    q_loc = urllib.parse.quote(loc)
                    search_url = f"https://www.linkedin.com/jobs/search/?keywords={q_kw}&location={q_loc}"
                    if easy_apply_only:
                        search_url += "&f_LF=f_AL" # Easy Apply filter

                    await page.goto(search_url, wait_until="networkidle")
                    await page.wait_for_timeout(3000)

                    # Extract job card links
                    # Selector for job list items
                    job_cards = page.locator(".jobs-search-results__list-item, .job-card-container")
                    count = await job_cards.count()
                    await self.log_repo.log("crawler", f"Found {count} job cards on current page view", "INFO")

                    # Limit to top 10 per search keyword/location combination to prevent spam
                    limit = min(count, 10)
                    for i in range(limit):
                        try:
                            card = job_cards.nth(i)
                            # Scroll card into view
                            await card.scroll_into_view_if_needed()
                            # Click card to load details pane
                            await card.click()
                            await page.wait_for_timeout(2000)

                            current_url = page.url
                            job_details = await LinkedInJobParser.parse_job_page(page, current_url)
                            
                            if job_details and job_details.get("title"):
                                found_jobs.append(job_details)
                                await self.log_repo.log("crawler", f"Parsed job: {job_details['title']} at {job_details['company']}", "INFO")
                        except Exception as card_err:
                            logger.error(f"Error parsing job card index {i}: {str(card_err)}")
                            continue
            
            return found_jobs

        except Exception as e:
            await self.log_repo.log("crawler", f"Crawler exception: {str(e)}", "ERROR")
            return found_jobs
        finally:
            await page.close()

    async def extract_job_details(self, url: str) -> Dict[str, Any]:
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            return await LinkedInJobParser.parse_job_page(page, url)
        finally:
            await page.close()
