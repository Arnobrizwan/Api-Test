"""Custom exceptions for the OCR API.

This module defines a hierarchy of custom exceptions for
consistent error handling throughout the application.
"""

from typing import Optional, Dict, Any

from .constants import ErrorCodes, HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR


class OCRAPIException(Exception):
    """Base exception for all OCR API errors.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCodes = ErrorCodes.INTERNAL_ERROR,
        status_code: int = HTTP_INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response.

        Internal details are hidden in production unless debug is enabled.

        Returns:
            Dictionary representation of the error
        """
        from .config import settings

        result = {
            "success": False,
            "error": self.message,
            "error_code": self.error_code.value if isinstance(self.error_code, ErrorCodes) else self.error_code,
        }
        
        # Only include details in non-production or if they are public safe
        # (e.g. filename validation errors are safe, stack traces are not)
        if self.details and (settings.debug or self.__class__.__name__ == "FileValidationError"):
            result["details"] = self.details
            
        return result


class ValidationError(OCRAPIException):
    """Exception raised for input validation failures.

    Used when client input fails validation checks such as
    invalid file type, file too large, or corrupted image.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCodes = ErrorCodes.INVALID_PARAMETERS,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTP_BAD_REQUEST,
            details=details
        )


class FileValidationError(ValidationError):
    """Exception raised for file-specific validation failures."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCodes,
        filename: Optional[str] = None
    ):
        details = {"filename": filename} if filename else None
        super().__init__(message=message, error_code=error_code, details=details)


class OCRProcessingError(OCRAPIException):
    """Exception raised when OCR processing fails.

    Used when the OCR engines fail to process an image,
    either due to engine errors or unsupported content.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCodes = ErrorCodes.OCR_FAILED,
        engine: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if engine:
            details["engine"] = engine
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTP_INTERNAL_ERROR,
            details=details
        )


class VisionAPIError(OCRProcessingError):
    """Exception raised for Google Cloud Vision API errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.VISION_API_ERROR,
            engine="cloud_vision",
            details=details
        )


class TesseractError(OCRProcessingError):
    """Exception raised for Tesseract OCR errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.TESSERACT_ERROR,
            engine="tesseract",
            details=details
        )


class RateLimitError(OCRAPIException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {"retry_after_seconds": retry_after} if retry_after else None
        super().__init__(
            message=message,
            error_code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details
        )


class ServiceUnavailableError(OCRAPIException):
    """Exception raised when a required service is unavailable."""

    def __init__(self, message: str, service: Optional[str] = None):
        details = {"service": service} if service else None
        super().__init__(
            message=message,
            error_code=ErrorCodes.SERVICE_UNAVAILABLE,
            status_code=503,
            details=details
        )
