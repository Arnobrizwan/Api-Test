"""OCR API endpoint handlers.

This module defines the API endpoints for OCR text extraction,
batch processing, and cache management.
"""

from typing import List

from fastapi import APIRouter, File, UploadFile, Query, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..core.config import settings
from ..core.constants import ErrorCodes
from ..core.exceptions import OCRAPIException, FileValidationError
from ..core.logging import get_logger
from ..models.responses import (
    OCRResponse,
    BatchOCRResponse,
    ErrorResponse,
    CacheStatsResponse,
)
from ..services.ocr_service import ocr_service
from ..utils.validators import (
    validate_image_file,
    validate_multiple_images,
    compute_image_hash,
)
from ..utils.cache_manager import ocr_cache

logger = get_logger(__name__)

router = APIRouter(tags=["OCR"])

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/extract-text",
    response_model=OCRResponse,
    responses={
        200: {
            "description": "Successful text extraction",
            "model": OCRResponse,
        },
        400: {
            "description": "Invalid request (bad file type, corrupted image)",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation error (missing file)",
            "model": ErrorResponse,
        },
        429: {
            "description": "Rate limit exceeded",
            "model": ErrorResponse,
        },
        500: {
            "description": "OCR processing failed",
            "model": ErrorResponse,
        },
    },
    summary="Extract Text from Image",
    description="""
Upload an image to extract text using OCR.

**Supported formats:** JPG, JPEG, PNG, GIF, WebP, BMP, TIFF

**Maximum file size:** 10MB

**Features:**
- Dual OCR engines (Cloud Vision primary, Tesseract fallback)
- Confidence scoring
- Text preprocessing and formatting
- Entity extraction (emails, phones, URLs, dates)
- Image metadata and quality assessment
- Result caching for identical images
    """,
)
@limiter.limit(settings.rate_limit)
async def extract_text(
    request: Request,
    image: UploadFile = File(
        ...,
        description="Image file to process (JPG, PNG, GIF, WebP, BMP, TIFF - max 10MB)"
    ),
    include_metadata: bool = Query(
        default=True,
        description="Include image metadata and quality assessment in response"
    ),
    include_entities: bool = Query(
        default=True,
        description="Extract entities (emails, phone numbers, URLs, dates) from text"
    ),
    use_cache: bool = Query(
        default=True,
        description="Use caching for identical images (based on SHA256 hash)"
    ),
) -> OCRResponse:
    """Extract text from a single uploaded image.

    This endpoint accepts an image file and returns extracted text along with
    confidence scores, metadata, and optional entity extraction.

    Args:
        request: FastAPI request object (for rate limiting)
        image: The uploaded image file
        include_metadata: Whether to include image metadata
        include_entities: Whether to extract entities from text
        use_cache: Whether to use result caching

    Returns:
        OCRResponse with extracted text and metadata

    Raises:
        FileValidationError: If image validation fails
        OCRAPIException: If OCR processing fails
    """
    # Validate uploaded image
    try:
        image_content, pil_image = await validate_image_file(image)
    except FileValidationError as e:
        logger.warning(f"Validation failed: {e.message}")
        status_code = 422 if e.error_code == ErrorCodes.MISSING_FILE else 400
        return JSONResponse(
            status_code=status_code,
            content=e.to_dict(),
        )

    # Compute cache key if caching enabled
    cache_key = compute_image_hash(image_content) if use_cache else None

    # Process image
    try:
        result = ocr_service.extract_text(
            image_content=image_content,
            image=pil_image,
            include_metadata=include_metadata,
            include_entities=include_entities,
            cache_key=cache_key,
        )

        logger.info(
            f"OCR extraction completed",
            extra={
                "engine": result.ocr_engine,
                "text_length": len(result.text or ""),
                "confidence": result.confidence,
                "cached": result.cached,
                "processing_time_ms": result.processing_time_ms,
            }
        )

        return result

    except OCRAPIException as e:
        logger.error(f"OCR processing failed: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict(),
        )


@router.post(
    "/extract-text/batch",
    response_model=BatchOCRResponse,
    responses={
        200: {
            "description": "Batch processing completed",
            "model": BatchOCRResponse,
        },
        400: {
            "description": "Invalid request",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation error",
            "model": ErrorResponse,
        },
        429: {
            "description": "Rate limit exceeded",
            "model": ErrorResponse,
        },
        500: {
            "description": "Processing failed",
            "model": ErrorResponse,
        },
    },
    summary="Batch Extract Text from Multiple Images",
    description="""
Upload multiple images for batch OCR processing.

**Maximum:** 10 images per request

**Note:** Metadata and entity extraction are disabled by default for batch
requests to improve performance. Enable them explicitly if needed.
    """,
)
@limiter.limit(settings.rate_limit_batch)
async def extract_text_batch(
    request: Request,
    images: List[UploadFile] = File(
        ...,
        description="Image files to process (max 10 files, 10MB each)"
    ),
    include_metadata: bool = Query(
        default=False,
        description="Include image metadata (disabled by default for performance)"
    ),
    include_entities: bool = Query(
        default=False,
        description="Extract entities (disabled by default for performance)"
    ),
    use_cache: bool = Query(
        default=True,
        description="Use caching for identical images"
    ),
) -> BatchOCRResponse:
    """Extract text from multiple images in a single request.

    This endpoint processes multiple images and returns results for each,
    along with summary statistics. Failed images don't cause the entire
    batch to fail.

    Args:
        request: FastAPI request object (for rate limiting)
        images: List of uploaded image files
        include_metadata: Whether to include image metadata
        include_entities: Whether to extract entities
        use_cache: Whether to use result caching

    Returns:
        BatchOCRResponse with individual results and summary

    Raises:
        FileValidationError: If validation fails
    """
    # Validate all images
    try:
        validated_images = await validate_multiple_images(images)
    except FileValidationError as e:
        logger.warning(f"Batch validation failed: {e.message}")
        status_code = 422 if e.error_code == ErrorCodes.MISSING_FILE else 400
        return JSONResponse(
            status_code=status_code,
            content=e.to_dict(),
        )

    # Prepare batch input with cache keys
    batch_input = []
    for content, pil_image, filename in validated_images:
        cache_key = compute_image_hash(content) if use_cache else None
        batch_input.append((content, pil_image, filename, cache_key))

    # Process batch
    try:
        result = ocr_service.extract_text_batch(
            images=batch_input,
            include_metadata=include_metadata,
            include_entities=include_entities,
        )

        logger.info(
            f"Batch OCR completed",
            extra={
                "total": result.total_files,
                "successful": result.successful,
                "failed": result.failed,
                "processing_time_ms": result.total_processing_time_ms,
            }
        )

        # Return 207 Multi-Status if there are mixed results (some successes, some failures)
        if result.failed > 0 and result.successful > 0:
            return JSONResponse(
                status_code=207,
                content=result.model_dump()
            )

        return result

    except OCRAPIException as e:
        logger.error(f"Batch OCR failed: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict(),
        )


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    summary="Get Cache Statistics",
    description="Returns current cache statistics including size, hit rate, and configuration.",
    tags=["Cache"],
)
async def get_cache_stats() -> CacheStatsResponse:
    """Get OCR result cache statistics.

    Returns:
        CacheStatsResponse with current cache metrics
    """
    stats = ocr_cache.get_stats()
    logger.debug(f"Cache stats requested: {stats}")
    return CacheStatsResponse(**stats)


@router.delete(
    "/cache",
    summary="Clear Cache",
    description="Clear all cached OCR results. Use with caution in production.",
    tags=["Cache"],
)
async def clear_cache():
    """Clear the OCR results cache.

    Returns:
        Success message
    """
    ocr_cache.clear()
    logger.info("Cache cleared by API request")
    return {
        "success": True,
        "message": "Cache cleared successfully"
    }
