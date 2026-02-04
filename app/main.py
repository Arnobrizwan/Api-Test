"""FastAPI application entry point.

This module configures and creates the FastAPI application with all
middleware, exception handlers, and routes properly configured.
"""

import os
import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.constants import ErrorCodes
from .core.exceptions import OCRAPIException
from .core.logging import setup_logging, get_logger
from .core.security import get_security_headers, generate_request_id
from .models.responses import HealthResponse, ErrorResponse, DependencyStatus
from .routes import ocr_router

# Setup logging
setup_logging(level=settings.log_level, json_format=not settings.debug)
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version}",
        extra={
            "event": "startup",
            "version": settings.app_version,
            "debug": settings.debug,
        }
    )
    logger.info(f"Rate limits: single={settings.rate_limit}, batch={settings.rate_limit_batch}")

    yield

    # Shutdown
    logger.info("Shutting down OCR API", extra={"event": "shutdown"})


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
A production-ready serverless OCR API that extracts text from images using
Google Cloud Vision API with Tesseract as fallback.

## Features
- **Multiple Image Formats**: JPG, PNG, GIF, WebP, BMP, TIFF
- **Dual OCR Engines**: Google Cloud Vision (primary) + Tesseract (fallback)
- **Confidence Scores**: Returns confidence scores for extracted text
- **Text Preprocessing**: Automatic cleanup and formatting
- **Entity Extraction**: Extracts emails, phone numbers, URLs, dates
- **Image Metadata**: Returns dimensions, format, EXIF data, color analysis
- **Quality Assessment**: Evaluates image quality for OCR
- **Caching**: SHA256-based caching for identical images
- **Batch Processing**: Process up to 10 images in one request
- **Rate Limiting**: Configurable rate limits for abuse protection
- **Security**: Input validation, magic byte checking, content scanning

## Error Handling
All errors return a consistent JSON structure with `success`, `error`, and `error_code` fields.
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Add security headers to all responses.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response with security headers
    """
    # Generate request ID for tracing
    request_id = generate_request_id()
    request.state.request_id = request_id

    # Process request
    response = await call_next(request)

    # Add security headers
    security_headers = get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value

    # Add request ID header
    response.headers["X-Request-ID"] = request_id

    return response


# Request size limit middleware - reject oversized requests early
@app.middleware("http")
async def check_content_length(request: Request, call_next: Callable) -> Response:
    """Reject requests that exceed the maximum allowed size before reading body.

    This prevents memory exhaustion from malicious large uploads.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response or 413 error if content too large
    """
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            # Allow some overhead for multipart form data (2x max file size)
            max_allowed = settings.max_file_size * 2
            if int(content_length) > max_allowed:
                logger.warning(
                    f"Request rejected: Content-Length {content_length} exceeds limit {max_allowed}"
                )
                return JSONResponse(
                    status_code=413,
                    content=ErrorResponse(
                        success=False,
                        error=f"Request body too large. Maximum allowed: {max_allowed // (1024 * 1024)}MB",
                        error_code=ErrorCodes.FILE_TOO_LARGE.value,
                    ).model_dump(),
                )
        except ValueError:
            pass  # Invalid content-length, let it proceed and fail elsewhere

    return await call_next(request)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """Log all incoming requests and their responses.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response from handler
    """
    start_time = time.perf_counter()

    # Get request_id from state (set by security headers middleware)
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request with request_id for tracing
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        }
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Log response with request_id for tracing
    logger.info(
        f"Response: {response.status_code} ({duration_ms}ms)",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
    )

    # Add timing header
    response.headers["X-Response-Time"] = f"{duration_ms}ms"

    return response


# CORS middleware
# Security Fix: Credentials cannot be allowed with wildcard origins ("*")
# If wildcard is present, use ONLY wildcard (don't mix with specific origins)
_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
_allow_all_origins = "*" in _cors_origins

# If wildcard is mixed with specific origins, that's a misconfiguration - use only wildcard
if _allow_all_origins:
    _cors_origins = ["*"]
    logger.warning("CORS configured with wildcard '*' - credentials will be disabled")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not _allow_all_origins,  # Credentials only allowed with specific origins
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI request validation errors (e.g., missing files).

    Converts FastAPI's default validation error format to our standardized
    error response format for consistency.

    Args:
        request: Incoming request
        exc: RequestValidationError from FastAPI/Pydantic

    Returns:
        JSON error response in standard format
    """
    # Check if it's a missing file error
    errors = exc.errors()
    missing_file = any(
        error.get("type") == "missing" and "image" in str(error.get("loc", []))
        for error in errors
    )

    if missing_file:
        logger.warning("Validation failed: No file uploaded")
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                success=False,
                error="No file uploaded. Please provide an image file.",
                error_code=ErrorCodes.MISSING_FILE.value,
            ).model_dump(),
        )

    # Generic validation error
    error_msg = "; ".join([f"{'.'.join(str(x) for x in e.get('loc', []))}: {e.get('msg', '')}" for e in errors])
    logger.warning(f"Validation error: {error_msg}")

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            error=f"Validation error: {error_msg}",
            error_code=ErrorCodes.INVALID_PARAMETERS.value,
        ).model_dump(),
    )


@app.exception_handler(OCRAPIException)
async def ocr_api_exception_handler(request: Request, exc: OCRAPIException) -> JSONResponse:
    """Handle OCR API specific exceptions.

    Args:
        request: Incoming request
        exc: OCR API exception

    Returns:
        JSON error response
    """
    logger.warning(
        f"API Exception: {exc.message}",
        extra={
            "error_code": exc.error_code.value if hasattr(exc.error_code, 'value') else exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions.

    Args:
        request: Incoming request
        exc: Unhandled exception

    Returns:
        JSON error response
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"exception_type": type(exc).__name__}
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="An unexpected error occurred. Please try again.",
            error_code=ErrorCodes.INTERNAL_ERROR.value,
        ).model_dump(),
    )


# Root endpoint
@app.get(
    "/",
    summary="API Information",
    description="Returns API information, available endpoints, and current configuration.",
    tags=["Info"],
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Extract text from images using OCR",
        "features": [
            "Multiple image formats (JPG, PNG, GIF, WebP, BMP, TIFF)",
            "Dual OCR engines (Cloud Vision + Tesseract fallback)",
            "Confidence scores",
            "Text preprocessing and formatting",
            "Entity extraction (emails, phones, URLs, dates)",
            "Image metadata and EXIF data",
            "Quality assessment",
            "Result caching",
            "Batch processing (up to 10 images)",
            "Rate limiting",
            "Security scanning",
        ],
        "endpoints": {
            "extract_text": "POST /extract-text",
            "batch_extract": "POST /extract-text/batch",
            "cache_stats": "GET /cache/stats",
            "clear_cache": "DELETE /cache",
            "health": "GET /health",
            "docs": "GET /docs",
        },
        "limits": {
            "max_file_size_mb": settings.max_file_size // (1024 * 1024),
            "max_batch_size": settings.max_batch_size,
            "rate_limit": settings.rate_limit,
            "rate_limit_batch": settings.rate_limit_batch,
        },
    }


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="""
Returns the health status of the service and its dependencies.

**Status values:**
- `healthy`: All dependencies are available
- `degraded`: Some non-critical dependencies are unavailable (e.g., cache)
- `unhealthy`: Critical dependencies are unavailable (e.g., no OCR engine)
    """,
    tags=["Info"],
)
async def health_check():
    """Health check endpoint for Cloud Run and load balancers.

    Verifies availability of:
    - OCR engines (Vision API and/or Tesseract)
    - Cache (Redis or in-memory)
    """
    from .services.vision_api import vision_service
    from .services.tesseract import tesseract_service
    from .utils.cache_manager import ocr_cache

    dependencies = {}
    overall_status = "healthy"

    # Check Vision API
    vision_available = vision_service.is_available
    dependencies["vision_api"] = DependencyStatus(
        available=vision_available,
        error=None if vision_available else "Vision API client not initialized"
    )

    # Check Tesseract
    tesseract_available = tesseract_service.is_available
    dependencies["tesseract"] = DependencyStatus(
        available=tesseract_available,
        version=tesseract_service.version if tesseract_available else None,
        error=None if tesseract_available else "Tesseract not installed or not accessible"
    )

    # Check cache
    cache_stats = ocr_cache.get_stats()
    cache_available = cache_stats.get("status") != "error" and cache_stats.get("status") != "disconnected"
    if cache_stats.get("type") == "in-memory":
        cache_available = True  # In-memory cache is always available
    dependencies["cache"] = DependencyStatus(
        available=cache_available,
        version=cache_stats.get("redis_version"),
        error=cache_stats.get("error") if not cache_available else None
    )

    # Determine overall status
    # Unhealthy if no OCR engine is available
    if not vision_available and not tesseract_available:
        overall_status = "unhealthy"
    # Degraded if cache is unavailable (non-critical)
    elif not cache_available:
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        dependencies=dependencies
    )


# Include OCR routes with v1 versioning (primary)
app.include_router(ocr_router, prefix="/v1")


# Static file cache headers middleware
@app.middleware("http")
async def add_static_cache_headers(request: Request, call_next: Callable) -> Response:
    """Add cache control headers for static files.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response with cache headers for static content
    """
    response = await call_next(request)

    # Add cache headers for static files served from /web
    if request.url.path.startswith("/web"):
        # Get file extension
        path = request.url.path.lower()

        # Immutable assets (versioned/hashed files, fonts)
        if any(path.endswith(ext) for ext in (".woff", ".woff2", ".ttf", ".eot")):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        # CSS/JS - moderate caching
        elif any(path.endswith(ext) for ext in (".css", ".js")):
            response.headers["Cache-Control"] = "public, max-age=3600, must-revalidate"
        # Images - longer caching
        elif any(path.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp")):
            response.headers["Cache-Control"] = "public, max-age=86400, must-revalidate"
        # HTML - short caching
        elif path.endswith(".html") or path == "/web" or path == "/web/":
            response.headers["Cache-Control"] = "public, max-age=300, must-revalidate"

    return response


# Serve frontend static files
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
frontend_path = os.path.join(project_root, "frontend")

if os.path.exists(frontend_path):
    app.mount("/web", StaticFiles(directory=frontend_path, html=True), name="frontend")
