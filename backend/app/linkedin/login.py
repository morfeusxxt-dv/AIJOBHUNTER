import json
from typing import Dict, Any, Optional
from playwright.async_api import BrowserContext, Page
from app.core.providers import AuthenticationProvider
from app.core.security import security_manager
from app.core.logger import logger
from app.repositories.settings_repository import SettingsRepository
from app.repositories.log_repository import LogRepository

class LinkedInAuthenticator(AuthenticationProvider):
    def __init__(self, settings_repo: SettingsRepository, log_repo: LogRepository):
        self.settings_repo = settings_repo
        self.log_repo = log_repo
        self.context: Optional[BrowserContext] = None

    async def login(self, credentials: Dict[str, Any]) -> bool:
        """
        Perform login flow on LinkedIn.
        In a commercial system, if MFA or manual intervention is needed, we run in non-headless
        or throw an exception to be resolved by the user, saving session afterwards.
        """
        username = credentials.get("username")
        password = credentials.get("password")
        if not username or not password:
            raise ValueError("Credentials must contain username and password")

        page = await self.context.new_page()
        try:
            await self.log_repo.log("login", "Starting LinkedIn login flow", "INFO")
            await page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            
            # Check if already logged in
            if "feed" in page.url:
                await self.log_repo.log("login", "Already logged in (session restored successfully)", "INFO")
                return True

            await page.fill("#username", username)
            await page.fill("#password", password)
            await page.click("button[type='submit']")
            await page.wait_for_timeout(5000)

            # Check if login is successful
            if "feed" in page.url or "checkpoint" in page.url or page.locator("#global-nav").is_visible():
                await self.log_repo.log("login", "Login successful", "INFO")
                serialized = await self.save_session()
                settings_obj = await self.settings_repo.get_global_settings()
                settings_obj.encrypted_session = serialized
                await self.settings_repo.update(settings_obj)
                return True
            else:
                await self.log_repo.log("login", "Login failed. Check credentials or MFA required.", "WARNING")
                return False
        except Exception as e:
            await self.log_repo.log("login", f"Error during login: {str(e)}", "ERROR")
            raise e
        finally:
            await page.close()

    async def is_session_valid(self) -> bool:
        if not self.context:
            return False
        page = await self.context.new_page()
        try:
            await page.goto("https://www.linkedin.com/feed", wait_until="networkidle")
            # If redirected to login, session is invalid
            is_valid = "login" not in page.url and "signup" not in page.url
            return is_valid
        except Exception:
            return False
        finally:
            await page.close()

    async def save_session(self) -> str:
        """Serializes cookies/origins and encrypts them"""
        if not self.context:
            return ""
        state = await self.context.storage_state()
        state_str = json.dumps(state)
        return security_manager.encrypt_data(state_str)

    async def load_session(self, encrypted_session: str) -> None:
        """Decrypts and sets storage state on the context"""
        if not encrypted_session or not self.context:
            return
        state_str = security_manager.decrypt_data(encrypted_session)
        if state_str:
            state = json.loads(state_str)
            # Apply cookies to the current context
            await self.context.add_cookies(state.get("cookies", []))
