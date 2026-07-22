from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AuthenticationProvider(ABC):
    @abstractmethod
    async def login(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate user and initialize session"""
        pass

    @abstractmethod
    async def is_session_valid(self) -> bool:
        """Check if stored session is still valid"""
        pass

    @abstractmethod
    async def save_session(self) -> str:
        """Serialize and encrypt session cookies/state"""
        pass

    @abstractmethod
    async def load_session(self, encrypted_session: str) -> None:
        """Decrypt and restore session cookies/state"""
        pass


class JobProvider(ABC):
    @abstractmethod
    async def search_jobs(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search jobs matching filters and return parsed metadata list"""
        pass

    @abstractmethod
    async def extract_job_details(self, url: str) -> Dict[str, Any]:
        """Navigate to a job URL and extract full description, requirements, etc."""
        pass


class ApplyProvider(ABC):
    @abstractmethod
    async def apply(self, job_url: str, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform automated application (e.g. Easy Apply) and return status/logs"""
        pass


class ResumeProvider(ABC):
    @abstractmethod
    async def retrieve_resume(self, resume_id: str) -> bytes:
        """Download or retrieve resume file contents"""
        pass

    @abstractmethod
    async def generate_cover_letter(self, job_details: Dict[str, Any]) -> str:
        """Generate custom cover letter tailored to the job description"""
        pass
