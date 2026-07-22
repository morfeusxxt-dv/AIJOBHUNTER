class JobHunterException(Exception):
    """Base exception for AI Job Hunter"""
    pass

class DatabaseException(JobHunterException):
    """Database operations failure"""
    pass

class ProviderException(JobHunterException):
    """External job/auth provider exception"""
    pass

class AuthenticationException(ProviderException):
    """Session expired or credentials rejected"""
    pass

class ApplicationLimitExceeded(JobHunterException):
    """Exceeded daily application limit"""
    pass

class WebhookException(JobHunterException):
    """Failed communicating with n8n webhook"""
    pass
