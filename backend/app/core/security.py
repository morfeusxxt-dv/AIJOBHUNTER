from cryptography.fernet import Fernet
from app.core.config import settings

class SecurityManager:
    def __init__(self):
        # Fernet requires 32 url-safe base64-encoded bytes
        # If settings.ENCRYPTION_KEY is not suitable, we can generate a fallback
        try:
            self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        except Exception:
            # Fallback for development/testing if key format is invalid
            fallback_key = Fernet.generate_key()
            self.fernet = Fernet(fallback_key)

    def encrypt_data(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return ""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt encrypted string data"""
        if not encrypted_data:
            return ""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return ""

security_manager = SecurityManager()
