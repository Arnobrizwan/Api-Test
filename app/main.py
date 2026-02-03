"""FastAPI application entry point.

This module configures and creates the FastAPI application with all
middleware, exception handlers, and routes properly configured.
"""

from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.constants import ErrorCodes
from .core.exceptions import OCRAPIException
from .core.logging import setup_logging, get_logger
from .core.security import get_security_headers, generate_request_id
from .models.responses import HealthResponse, ErrorResponse

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
    import time

    start_time = time.perf_counter()

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        }
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Log response
    logger.info(
        f"Response: {response.status_code} ({duration_ms}ms)",
        extra={
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
    )

    # Add timing header
    response.headers["X-Response-Time"] = f"{duration_ms}ms"

    return response


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
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
    description="Returns the health status of the service for load balancers and monitoring.",
    tags=["Info"],
)
async def health_check():
    """Health check endpoint for Cloud Run and load balancers."""
    return HealthResponse(status="healthy", version=settings.app_version)


# Include OCR routes
from .routes import ocr_router

app.include_router(ocr_router)
