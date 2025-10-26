"""Custom exception classes for the Memory Service."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from memsrv.utils.logger import get_logger

logger = get_logger(__name__)

def add_exception_handlers(_app: FastAPI):
    """Function for adding exception handler to fastapi app"""

    @_app.exception_handler(MemoryServiceError)
    async def memory_service_exception_handler(request: Request, exc: MemoryServiceError):
        """
        Handles custom application exceptions and returns a structured JSON response.
        """
        logger.error(
            f"An application error occurred: {exc.error_code} - {exc.message}",
            exc_info=True
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                }
            },
        )

class MemoryServiceError(Exception):
    """Base exception class for all service-related errors."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_SERVER_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class ConfigurationError(MemoryServiceError):
    """Raised for configuration-related issues."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="CONFIGURATION_ERROR")

class APIError(MemoryServiceError):
    """Raised when there's an error interacting with the API."""
    def __init__(self, message: str):
        super().__init__(message, status_code=503, error_code="API_SERVICE_UNAVAILABLE")

class RetryableAPIError(APIError):
    """A specific API error that indicates the operation can be retried."""
    def __init__(self, message: str):
        super().__init__(
            message,
            status_code=503,
            error_code="API_SERVICE_TEMPORARILY_UNAVAILABLE"
        )

# TODO: Use them later
class DatabaseError(MemoryServiceError):
    """Raised for errors related to the vector database."""
    def __init__(self, message: str):
        super().__init__(message, status_code=503, error_code="DATABASE_SERVICE_UNAVAILABLE")

class MemoryNotFoundError(MemoryServiceError):
    """Raised when one or more memories are not found for a given ID."""
    def __init__(self, memory_ids: list[str]):
        message = f"Memories with the following IDs were not found: {', '.join(memory_ids)}"
        super().__init__(message, status_code=404, error_code="MEMORY_NOT_FOUND")

class InvalidRequestError(MemoryServiceError):
    """Raised for invalid input from the user."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code="INVALID_REQUEST")
