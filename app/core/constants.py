"""Application constants and enumerations.

This module defines all constant values, enumerations, and error codes
used throughout the application for consistency and maintainability.
"""

from enum import Enum
from typing import Dict, Set


class ErrorCodes(str, Enum):
    """Standardized error codes for API responses.

    These codes provide machine-readable error identification
    for client-side error handling.
    """

    # Validation Errors (400)
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_IMAGE = "INVALID_IMAGE"
    TOO_MANY_FILES = "TOO_MANY_FILES"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"

    # Authentication/Authorization (401/403)
    MISSING_FILE = "MISSING_FILE"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Server Errors (500)
    OCR_FAILED = "OCR_FAILED"
    BATCH_FAILED = "BATCH_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    VISION_API_ERROR = "VISION_API_ERROR"
    TESSERACT_ERROR = "TESSERACT_ERROR"


class OCREngine(str, Enum):
    """Available OCR engines."""

    CLOUD_VISION = "cloud_vision"
    TESSERACT = "tesseract"


class ImageFormat(str, Enum):
    """Supported image formats."""

    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    BMP = "bmp"
    TIFF = "tiff"
    TIF = "tif"


# Supported file extensions (lowercase)
ALLOWED_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"
}

# Supported MIME types
ALLOWED_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
}

# MIME type to extension mapping
MIME_TO_EXTENSION: Dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
}

# HTTP Status codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# Error messages
ERROR_MESSAGES: Dict[str, str] = {
    ErrorCodes.INVALID_FILE_TYPE: "Invalid file type. Supported formats: JPG, PNG, GIF, WebP, BMP, TIFF",
    ErrorCodes.FILE_TOO_LARGE: "File size exceeds maximum allowed limit",
    ErrorCodes.INVALID_IMAGE: "Invalid or corrupted image file",
    ErrorCodes.TOO_MANY_FILES: "Too many files. Maximum {max} files per batch request",
    ErrorCodes.MISSING_FILE: "No file uploaded",
    ErrorCodes.OCR_FAILED: "OCR processing failed. Please try again",
    ErrorCodes.BATCH_FAILED: "Batch processing failed. Please try again",
    ErrorCodes.RATE_LIMIT_EXCEEDED: "Rate limit exceeded. Please try again later",
    ErrorCodes.INTERNAL_ERROR: "An unexpected error occurred",
}

# Quality assessment thresholds
QUALITY_SCORE_GOOD = 70
QUALITY_SCORE_FAIR = 50
MIN_IMAGE_DIMENSION = 100
LOW_IMAGE_DIMENSION = 300
MAX_ASPECT_RATIO = 10
MIN_ASPECT_RATIO = 0.1
MIN_BRIGHTNESS = 0.2
MAX_BRIGHTNESS = 0.9
