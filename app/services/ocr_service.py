"""OCR orchestration service.

This module provides the main OCR service that orchestrates between
Google Cloud Vision API and Tesseract OCR engines, with support for
caching, batch processing, and comprehensive result formatting.
"""

import time
from typing import Tuple, Optional, List

from PIL import Image

from .vision_api import vision_service
from .tesseract import tesseract_service
from ..core.config import settings
from ..core.constants import OCREngine, ErrorCodes
from ..core.exceptions import OCRProcessingError
from ..core.logging import get_logger
from ..models.responses import (
    OCRResponse,
    BatchOCRResponse,
    BatchItemResponse,
    TextStats,
    ExtractedEntities,
    ImageMetadata,
    QualityAssessment,
)
from ..utils.cache_manager import ocr_cache
from ..utils.text_processing import (
    cleanup_text,
    format_as_paragraphs,
    extract_emails,
    extract_phone_numbers,
    extract_urls,
    extract_dates,
    get_word_count,
    get_character_count,
)
from ..utils.metadata import extract_image_metadata, get_image_quality_score
from ..utils.image_utils import resize_image_if_needed, image_to_bytes

logger = get_logger(__name__)


class OCRService:
    """Orchestrates OCR processing between available engines.

    This service manages the OCR workflow including:
    - Engine selection and fallback
    - Result caching
    - Text post-processing
    - Metadata extraction
    - Batch processing

    Attributes:
        use_tesseract_only: Skip Cloud Vision, use only Tesseract
        enable_cache: Enable result caching
    """

    def __init__(self):
        """Initialize OCR service with configuration."""
        self.use_tesseract_only = settings.use_tesseract_only
        self.enable_cache = settings.enable_cache

        logger.info(
            f"OCR Service initialized: "
            f"tesseract_only={self.use_tesseract_only}, "
            f"cache_enabled={self.enable_cache}"
        )

    def _perform_ocr(
        self,
        image_content: bytes,
        image: Image.Image
    ) -> Tuple[str, float, OCREngine]:
        """Perform OCR using available engines with fallback.

        Attempts Cloud Vision first (unless disabled), then falls back
        to Tesseract if Cloud Vision fails or is unavailable.

        Args:
            image_content: Raw image bytes for Vision API
            image: PIL Image object for Tesseract

        Returns:
            Tuple of (extracted_text, confidence_score, engine_used)

        Raises:
            OCRProcessingError: If all OCR engines fail
        """
        text: Optional[str] = None
        confidence: Optional[float] = None
        engine_used: Optional[OCREngine] = None
        errors: List[str] = []

        # Try Cloud Vision API first
        if not self.use_tesseract_only and vision_service.is_available:
            try:
                logger.debug("Attempting OCR with Google Cloud Vision API")
                text, confidence = vision_service.extract_text(image_content)
                engine_used = OCREngine.CLOUD_VISION
                logger.info(
                    f"Vision API extraction successful: "
                    f"text_length={len(text or '')}, confidence={confidence:.4f}"
                )
            except Exception as e:
                error_msg = f"Vision API: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Vision API failed: {e}", exc_info=True)

        # Fall back to Tesseract if needed
        if text is None and tesseract_service.is_available:
            try:
                logger.debug("Attempting OCR with Tesseract")
                text, confidence = tesseract_service.extract_text(image)
                engine_used = OCREngine.TESSERACT
                logger.info(
                    f"Tesseract extraction successful: "
                    f"text_length={len(text or '')}, confidence={confidence:.4f}"
                )
            except Exception as e:
                error_msg = f"Tesseract: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Tesseract failed: {e}", exc_info=True)

        # Check if all engines failed
        if text is None:
            error_details = "; ".join(errors) if errors else "No OCR engines available"
            logger.error(f"All OCR engines failed: {error_details}")
            raise OCRProcessingError(
                message="OCR processing failed. All engines unavailable or returned errors.",
                error_code=ErrorCodes.OCR_FAILED,
                details={"engine_errors": errors}
            )

        return text or "", confidence or 0.0, engine_used

    def _build_text_stats(self, text: str) -> TextStats:
        """Build text statistics from extracted text.

        Args:
            text: Extracted text content

        Returns:
            TextStats with word count, character counts, line count
        """
        return TextStats(
            word_count=get_word_count(text),
            character_count=get_character_count(text, include_spaces=True),
            character_count_no_spaces=get_character_count(text, include_spaces=False),
            line_count=len(text.split("\n")) if text else 0,
        )

    def _build_entities(self, text: str) -> ExtractedEntities:
        """Extract structured entities from text.

        Args:
            text: Text to extract entities from

        Returns:
            ExtractedEntities with emails, phones, URLs, dates
        """
        return ExtractedEntities(
            emails=extract_emails(text),
            phone_numbers=extract_phone_numbers(text),
            urls=extract_urls(text),
            dates=extract_dates(text),
        )

    def _build_image_metadata(self, image: Image.Image) -> ImageMetadata:
        """Build comprehensive image metadata.

        Args:
            image: PIL Image object

        Returns:
            ImageMetadata with dimensions, format, EXIF, color info
        """
        metadata = extract_image_metadata(image)
        basic = metadata.get("basic", {})
        exif = metadata.get("exif")
        color = metadata.get("color")

        return ImageMetadata(
            width=basic.get("width", 0),
            height=basic.get("height", 0),
            format=basic.get("format"),
            mode=basic.get("mode"),
            aspect_ratio=basic.get("aspect_ratio"),
            megapixels=basic.get("megapixels"),
            has_transparency=basic.get("has_transparency", False),
            exif=exif,
            color_info=color,
        )

    def _build_quality_assessment(self, image: Image.Image) -> QualityAssessment:
        """Assess image quality for OCR purposes.

        Args:
            image: PIL Image object

        Returns:
            QualityAssessment with score and recommendations
        """
        quality = get_image_quality_score(image)
        return QualityAssessment(
            score=quality.get("score", 0),
            quality=quality.get("quality", "unknown"),
            recommendations=quality.get("recommendations", []),
        )

    def extract_text(
        self,
        image_content: bytes,
        image: Image.Image,
        include_metadata: bool = True,
        include_entities: bool = True,
        cache_key: Optional[str] = None,
    ) -> OCRResponse:
        """Extract text from an image with full processing pipeline.

        This is the main entry point for single-image OCR processing.
        It handles caching, OCR execution, and result formatting.

        Args:
            image_content: Raw image bytes
            image: PIL Image object
            include_metadata: Include image metadata in response
            include_entities: Extract entities from text
            cache_key: Optional cache key for result caching

        Returns:
            OCRResponse with extracted text and all metadata

        Raises:
            OCRProcessingError: If OCR processing fails
        """
        start_time = time.perf_counter()

        # Check cache first
        if self.enable_cache and cache_key:
            cached_result = ocr_cache.get(cache_key)
            if cached_result:
                processing_time_ms = int((time.perf_counter() - start_time) * 1000)
                cached_result["cached"] = True
                cached_result["processing_time_ms"] = processing_time_ms
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                return OCRResponse(**cached_result)

        # Auto-resize if needed (Optimization)
        original_size = image.size
        image = resize_image_if_needed(image, settings.max_image_width)
        if image.size != original_size:
            logger.info(f"Image resized from {original_size} to {image.size}")
            # Update bytes for Cloud Vision API
            image_content = image_to_bytes(image)

        # Perform OCR
        text, confidence, engine_used = self._perform_ocr(image_content, image)

        # Post-process text
        text_formatted = format_as_paragraphs(cleanup_text(text)) if text else ""

        # Build response components
        text_stats = self._build_text_stats(text)
        entities = self._build_entities(text) if include_entities else None
        image_metadata = self._build_image_metadata(image) if include_metadata else None
        quality_assessment = self._build_quality_assessment(image) if include_metadata else None

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        # Build result
        result = {
            "success": True,
            "text": text,
            "text_formatted": text_formatted,
            "confidence": round(confidence, 4) if confidence else 0.0,
            "processing_time_ms": processing_time_ms,
            "ocr_engine": engine_used.value if engine_used else None,
            "cached": False,
            "text_stats": text_stats,
            "entities": entities,
            "image_metadata": image_metadata,
            "quality_assessment": quality_assessment,
        }

        # Cache result
        if self.enable_cache and cache_key:
            # Deep copy and convert Pydantic models to dicts for JSON serialization
            cache_data = {
                "success": result["success"],
                "text": result["text"],
                "text_formatted": result["text_formatted"],
                "confidence": result["confidence"],
                "ocr_engine": result["ocr_engine"],
                "text_stats": result["text_stats"].model_dump() if result["text_stats"] else None,
                "entities": result["entities"].model_dump() if result["entities"] else None,
                "image_metadata": result["image_metadata"].model_dump() if result["image_metadata"] else None,
                "quality_assessment": result["quality_assessment"].model_dump() if result["quality_assessment"] else None,
            }
            ocr_cache.set(cache_key, cache_data)
            logger.debug(f"Cached result for key: {cache_key[:16]}...")

        logger.info(
            f"OCR completed: engine={engine_used.value if engine_used else 'none'}",
            extra={
                "engine": engine_used.value if engine_used else "none",
                "is_fallback": engine_used == OCREngine.TESSERACT and not self.use_tesseract_only,
                "confidence": confidence,
                "processing_time_ms": processing_time_ms
            }
        )

        return OCRResponse(**result)

    def extract_text_batch(
        self,
        images: List[Tuple[bytes, Image.Image, str, Optional[str]]],
        include_metadata: bool = False,
        include_entities: bool = False,
    ) -> BatchOCRResponse:
        """Extract text from multiple images in batch.

        Processes multiple images sequentially, collecting results
        and handling individual failures gracefully.

        Args:
            images: List of (content, pil_image, filename, cache_key) tuples
            include_metadata: Include image metadata for each result
            include_entities: Extract entities for each result

        Returns:
            BatchOCRResponse with individual results and summary statistics
        """
        start_time = time.perf_counter()
        results: List[BatchItemResponse] = []
        successful = 0
        failed = 0

        logger.info(f"Starting batch OCR processing for {len(images)} images")

        for idx, (image_content, pil_image, filename, cache_key) in enumerate(images):
            item_start = time.perf_counter()

            try:
                result = self.extract_text(
                    image_content,
                    pil_image,
                    include_metadata=include_metadata,
                    include_entities=include_entities,
                    cache_key=cache_key,
                )
                results.append(
                    BatchItemResponse(
                        filename=filename,
                        success=True,
                        text=result.text,
                        text_formatted=result.text_formatted,
                        confidence=result.confidence,
                        ocr_engine=result.ocr_engine,
                        cached=result.cached,
                        processing_time_ms=int((time.perf_counter() - item_start) * 1000),
                    )
                )
                successful += 1
                logger.debug(f"Batch item {idx + 1}/{len(images)} processed: {filename}")

            except Exception as e:
                error_msg = str(e)
                results.append(
                    BatchItemResponse(
                        filename=filename,
                        success=False,
                        error=error_msg,
                        error_code=ErrorCodes.OCR_FAILED.value,
                        processing_time_ms=int((time.perf_counter() - item_start) * 1000),
                    )
                )
                failed += 1
                logger.warning(f"Batch item {idx + 1}/{len(images)} failed: {filename} - {error_msg}")

        total_time_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            f"Batch OCR completed: total={len(images)}, "
            f"successful={successful}, failed={failed}, "
            f"time={total_time_ms}ms"
        )

        return BatchOCRResponse(
            success=True,
            total_files=len(images),
            successful=successful,
            failed=failed,
            total_processing_time_ms=total_time_ms,
            results=results,
        )


# Global service instance
ocr_service = OCRService()
