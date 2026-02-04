"""Image validation utilities.

This module provides comprehensive image validation including
file type, size, integrity, and security checks.
"""

import asyncio
import io
from typing import Tuple, List

from PIL import Image
from fastapi import UploadFile

from ..core.config import settings
from ..core.constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    ErrorCodes,
    MIN_IMAGE_SIZE_BYTES,
    FILE_READ_TIMEOUT_SECONDS,
)
from ..core.exceptions import FileValidationError
from ..core.security import (
    validate_image_magic_bytes,
    check_for_suspicious_content,
    sanitize_filename,
    compute_content_hash,
)
from ..core.logging import get_logger

logger = get_logger(__name__)


def compute_image_hash(content: bytes) -> str:
    """Compute SHA256 hash of image content for caching.

    Args:
        content: Image file content as bytes

    Returns:
        Hexadecimal SHA256 hash string
    """
    return compute_content_hash(content, "sha256")


async def validate_image_file(file: UploadFile) -> Tuple[bytes, Image.Image]:
    """Validate an uploaded image file comprehensively.

    Performs multiple validation checks:
    1. File presence and filename validation
    2. File extension validation
    3. MIME type validation
    4. File size validation
    5. Magic bytes validation
    6. Security content scanning
    7. Image integrity validation (can be opened by PIL)

    Args:
        file: The uploaded file from FastAPI

    Returns:
        Tuple of (file_bytes, PIL_Image)

    Raises:
        FileValidationError: If any validation check fails
    """
    # Check file presence
    if not file or not file.filename:
        logger.warning("Validation failed: No file uploaded")
        raise FileValidationError(
            message="No file uploaded",
            error_code=ErrorCodes.MISSING_FILE
        )

    # Sanitize and validate filename
    original_filename = file.filename
    safe_filename = sanitize_filename(original_filename)

    if safe_filename != original_filename:
        logger.info(f"Filename sanitized: '{original_filename}' -> '{safe_filename}'")

    # Validate file extension
    ext = '.' + safe_filename.rsplit('.', 1)[-1].lower() if '.' in safe_filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Validation failed: Invalid extension '{ext}' for file '{safe_filename}'")
        raise FileValidationError(
            message=f"Invalid file type. Supported formats: JPG, JPEG, PNG, GIF, WebP, BMP, TIFF. Got: {ext}",
            error_code=ErrorCodes.INVALID_FILE_TYPE,
            filename=safe_filename
        )

    # Validate MIME type (if provided)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        # Allow if it starts with 'image/' as some clients send generic types
        if not file.content_type.startswith("image/"):
            logger.warning(f"Validation failed: Invalid MIME type '{file.content_type}'")
            raise FileValidationError(
                message=f"Invalid MIME type. Expected image type, got: {file.content_type}",
                error_code=ErrorCodes.INVALID_FILE_TYPE,
                filename=safe_filename
            )

    # Read file content with timeout to prevent Slowloris attacks
    try:
        content = await asyncio.wait_for(file.read(), timeout=FILE_READ_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.warning(f"Validation failed: File read timeout for '{safe_filename}'")
        raise FileValidationError(
            message="File upload timed out. Please try again.",
            error_code=ErrorCodes.INVALID_IMAGE,
            filename=safe_filename
        )

    # Validate file size
    if len(content) > settings.max_file_size:
        size_mb = settings.max_file_size // (1024 * 1024)
        logger.warning(f"Validation failed: File too large ({len(content)} bytes)")
        raise FileValidationError(
            message=f"File too large. Maximum size is {size_mb}MB",
            error_code=ErrorCodes.FILE_TOO_LARGE,
            filename=safe_filename
        )

    if len(content) == 0:
        logger.warning("Validation failed: Empty file")
        raise FileValidationError(
            message="Empty file uploaded",
            error_code=ErrorCodes.INVALID_IMAGE,
            filename=safe_filename
        )

    # Check minimum file size (files too small cannot be valid images)
    if len(content) < MIN_IMAGE_SIZE_BYTES:
        logger.warning(f"Validation failed: File too small ({len(content)} bytes)")
        raise FileValidationError(
            message=f"File too small to be a valid image. Minimum size is {MIN_IMAGE_SIZE_BYTES} bytes.",
            error_code=ErrorCodes.INVALID_IMAGE,
            filename=safe_filename
        )

    # Validate magic bytes
    is_valid_image, detected_format = validate_image_magic_bytes(content)
    if not is_valid_image:
        logger.warning(f"Validation failed: Invalid magic bytes for file '{safe_filename}'")
        raise FileValidationError(
            message="Invalid image file. File content does not match expected image format.",
            error_code=ErrorCodes.INVALID_IMAGE,
            filename=safe_filename
        )

    # Security scan
    if check_for_suspicious_content(content):
        logger.error(f"Security alert: Suspicious content detected in file '{safe_filename}'")
        raise FileValidationError(
            message="File rejected due to suspicious content",
            error_code=ErrorCodes.INVALID_IMAGE,
            filename=safe_filename
        )

    # Validate image integrity with PIL - open once, verify, and use
    try:
        image_buffer = io.BytesIO(content)
        image = Image.open(image_buffer)
        # Verify by loading the image data
        image.load()
    except Exception as e:
        logger.warning(f"Validation failed: Image integrity check failed - {e}")
        raise FileValidationError(
            message="Invalid or corrupted image file",
            error_code=ErrorCodes.INVALID_IMAGE,
            filename=safe_filename
        )

    logger.debug(
        f"Validation passed: file='{safe_filename}', "
        f"size={len(content)}, format={detected_format}, "
        f"dimensions={image.width}x{image.height}"
    )

    return content, image


async def validate_multiple_images(files: List[UploadFile]) -> List[Tuple[bytes, Image.Image, str]]:
    """Validate multiple uploaded image files.

    Args:
        files: List of uploaded files

    Returns:
        List of tuples (file_bytes, PIL_Image, filename)

    Raises:
        FileValidationError: If validation fails for any file
    """
    if not files:
        raise FileValidationError(
            message="No files uploaded",
            error_code=ErrorCodes.MISSING_FILE
        )

    if len(files) > settings.max_batch_size:
        raise FileValidationError(
            message=f"Too many files. Maximum {settings.max_batch_size} files per batch request.",
            error_code=ErrorCodes.TOO_MANY_FILES
        )

    # Track total batch size to prevent memory exhaustion
    total_batch_bytes = 0
    max_total_batch_size = settings.max_file_size * settings.max_batch_size  # e.g., 10MB * 10 = 100MB

    results = []
    for idx, file in enumerate(files):
        try:
            content, image = await validate_image_file(file)
            safe_filename = sanitize_filename(file.filename) if file.filename else f"file_{idx}"

            # Check total batch size
            total_batch_bytes += len(content)
            if total_batch_bytes > max_total_batch_size:
                raise FileValidationError(
                    message=f"Total batch size exceeds limit. Maximum total size is {max_total_batch_size // (1024 * 1024)}MB.",
                    error_code=ErrorCodes.FILE_TOO_LARGE
                )

            results.append((content, image, safe_filename))
        except FileValidationError as e:
            # Re-raise with file index for better error messages
            raise FileValidationError(
                message=f"File {idx + 1}: {e.message}",
                error_code=e.error_code,
                filename=e.details.get("filename") if e.details else None
            )

    logger.info(f"Batch validation passed: {len(results)} files validated")
    return results
