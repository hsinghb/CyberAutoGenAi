"""Custom exceptions for CyberAutoGenAI."""

class CyberAutoGenAIException(Exception):
    """Base exception class for CyberAutoGenAI."""
    pass

class QuotaExceededException(CyberAutoGenAIException):
    """Raised when API quota is exceeded."""
    def __init__(self, message: str = "API quota exceeded", service: str = None):
        self.service = service
        self.message = f"{message} for service: {service}" if service else message
        super().__init__(self.message)

class APIKeyError(CyberAutoGenAIException):
    """Raised when there are issues with API keys."""
    def __init__(self, message: str = "Invalid or missing API key", service: str = None):
        self.service = service
        self.message = f"{message} for service: {service}" if service else message
        super().__init__(self.message)

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class ConnectionError(CyberAutoGenAIException):
    """Raised when connection to services fails."""
    pass

class ConfigurationError(CyberAutoGenAIException):
    """Raised when there are configuration issues."""
    pass

class ProcessingError(Exception):
    """Raised when processing fails."""
    pass

class AgentError(CyberAutoGenAIException):
    """Raised when there are agent-specific issues."""
    pass

class MCPError(CyberAutoGenAIException):
    """Raised when there are MCP-related issues."""
    pass

class QuotaExceededError(Exception):
    """Raised when API quota is exceeded."""
    pass

# Export all exceptions
__all__ = [
    'CyberAutoGenAIException',
    'QuotaExceededException',
    'APIKeyError',
    'ValidationError',
    'ConnectionError',
    'ConfigurationError',
    'ProcessingError',
    'AgentError',
    'MCPError'
] 