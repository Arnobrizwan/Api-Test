"""Pydantic models for API responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class TextStats(BaseModel):
    """Statistics about extracted text."""

    word_count: int = Field(description="Number of words in extracted text")
    character_count: int = Field(description="Number of characters including spaces")
    character_count_no_spaces: int = Field(description="Number of characters excluding spaces")
    line_count: int = Field(description="Number of lines in text")


class ExtractedEntities(BaseModel):
    """Entities extracted from text."""

    emails: List[str] = Field(default_factory=list, description="Email addresses found")
    phone_numbers: List[str] = Field(default_factory=list, description="Phone numbers found")
    urls: List[str] = Field(default_factory=list, description="URLs found")
    dates: List[str] = Field(default_factory=list, description="Dates found")


class ImageMetadata(BaseModel):
    """Image metadata information."""

    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    format: Optional[str] = Field(default=None, description="Image format (JPEG, PNG, etc.)")
    mode: Optional[str] = Field(default=None, description="Image color mode (RGB, L, etc.)")
    aspect_ratio: Optional[float] = Field(default=None, description="Width/height ratio")
    megapixels: Optional[float] = Field(default=None, description="Image size in megapixels")
    has_transparency: bool = Field(default=False, description="Whether image has alpha channel")
    exif: Optional[Dict[str, Any]] = Field(default=None, description="EXIF metadata if available")
    color_info: Optional[Dict[str, Any]] = Field(default=None, description="Color analysis")


class QualityAssessment(BaseModel):
    """Image quality assessment for OCR."""

    score: int = Field(ge=0, le=100, description="Quality score 0-100")
    quality: str = Field(description="Quality rating: good, fair, or poor")
    recommendations: List[str] = Field(default_factory=list, description="Improvement suggestions")


class OCRResponse(BaseModel):
    """Response model for successful OCR extraction."""

    success: bool = Field(default=True, description="Whether the operation was successful")
    text: Optional[str] = Field(default=None, description="Extracted text from the image")
    text_formatted: Optional[str] = Field(default=None, description="Cleaned and formatted text")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction (0.0 to 1.0)",
    )
    processing_time_ms: int = Field(
        description="Time taken to process the image in milliseconds"
    )
    ocr_engine: str = Field(
        description="OCR engine used: 'cloud_vision' or 'tesseract'"
    )
    cached: bool = Field(default=False, description="Whether result was served from cache")
    text_stats: Optional[TextStats] = Field(default=None, description="Text statistics")
    entities: Optional[ExtractedEntities] = Field(default=None, description="Extracted entities")
    image_metadata: Optional[ImageMetadata] = Field(default=None, description="Image metadata")
    quality_assessment: Optional[QualityAssessment] = Field(default=None, description="OCR quality assessment")


class BatchItemResponse(BaseModel):
    """Response for a single item in batch processing."""

    filename: str = Field(description="Original filename")
    success: bool = Field(description="Whether extraction was successful")
    text: Optional[str] = Field(default=None, description="Extracted text")
    text_formatted: Optional[str] = Field(default=None, description="Cleaned text")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    ocr_engine: Optional[str] = Field(default=None, description="OCR engine used")
    cached: bool = Field(default=False, description="Whether result was from cache")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_code: Optional[str] = Field(default=None, description="Error code if failed")
    processing_time_ms: int = Field(description="Processing time for this image")


class BatchOCRResponse(BaseModel):
    """Response model for batch OCR processing."""

    success: bool = Field(default=True, description="Whether the batch operation completed")
    total_files: int = Field(description="Total number of files processed")
    successful: int = Field(description="Number of successfully processed files")
    failed: int = Field(description="Number of failed files")
    total_processing_time_ms: int = Field(description="Total processing time")
    results: List[BatchItemResponse] = Field(description="Individual results for each file")


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    success: bool = Field(default=False, description="Always False for errors")
    error: str = Field(description="Human-readable error message")
    error_code: str = Field(description="Machine-readable error code")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(default="healthy", description="Service health status")
    version: str = Field(description="API version")


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    size: int = Field(description="Current number of cached items")
    max_size: int = Field(description="Maximum cache size")
    ttl_seconds: int = Field(description="Cache TTL in seconds")
    hits: int = Field(description="Number of cache hits")
    misses: int = Field(description="Number of cache misses")
    hit_rate_percent: float = Field(description="Cache hit rate percentage")
