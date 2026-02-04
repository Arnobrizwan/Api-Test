"""Google Cloud Vision API integration.

This module provides a service wrapper for Google Cloud Vision API's
OCR capabilities with proper initialization, error handling, and
text extraction methods.
"""

import threading
from typing import Tuple, Optional

from ..core.config import settings
from ..core.constants import (
    DEFAULT_CONFIDENCE_DOCUMENT_DETECTION,
    DEFAULT_CONFIDENCE_TEXT_DETECTION,
)
from ..core.exceptions import VisionAPIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class VisionAPIService:
    """Service for Google Cloud Vision API OCR.

    Provides lazy initialization of the Vision API client and methods
    for extracting text from images using document and text detection.

    Attributes:
        _client: The Vision API client instance (lazily initialized)
        _initialized: Whether initialization has been attempted
    """

    def __init__(self):
        """Initialize the Vision API service."""
        self._client = None
        self._initialized = False
        self._init_error: Optional[str] = None
        self._init_lock = threading.Lock()

    def _init_client(self) -> None:
        """Lazily initialize the Vision API client (thread-safe).

        Defers client creation until first use to avoid startup delays
        and to handle missing credentials gracefully. Uses double-checked
        locking to ensure thread safety without excessive lock contention.
        """
        if self._initialized:
            return

        with self._init_lock:
            # Double-check after acquiring lock
            if self._initialized:
                return

            try:
                from google.cloud import vision

                self._client = vision.ImageAnnotatorClient()
                self._initialized = True
                logger.info("Google Cloud Vision API client initialized successfully")

            except ImportError as e:
                self._init_error = f"google-cloud-vision package not installed: {e}"
                logger.warning(self._init_error)
                self._initialized = True

            except Exception as e:
                self._init_error = f"Failed to initialize Vision API client: {e}"
                logger.warning(self._init_error)
                self._initialized = True

    @property
    def is_available(self) -> bool:
        """Check if Vision API is available for use.

        Returns:
            True if the client is initialized and ready
        """
        self._init_client()
        return self._client is not None

    def extract_text(self, image_content: bytes) -> Tuple[str, float]:
        """Extract text from an image using Google Cloud Vision API.

        Uses DOCUMENT_TEXT_DETECTION for better results with complex layouts,
        falling back to TEXT_DETECTION if no text is found.

        Args:
            image_content: Image file content as bytes

        Returns:
            Tuple of (extracted_text, confidence_score)

        Raises:
            VisionAPIError: If API call fails or client unavailable
        """
        self._init_client()

        if not self._client:
            raise VisionAPIError(
                message=self._init_error or "Vision API client not available",
                details={"init_error": self._init_error}
            )

        try:
            from google.cloud import vision

            # Create image object
            image = vision.Image(content=image_content)

            # Try document text detection first (better for complex layouts)
            logger.debug("Attempting DOCUMENT_TEXT_DETECTION")
            response = self._client.document_text_detection(image=image)

            # Check for API errors
            if response.error.message:
                raise VisionAPIError(
                    message=f"Vision API returned error: {response.error.message}",
                    details={"api_error": response.error.message}
                )

            # If no text found, try regular text detection
            if not response.full_text_annotation.text:
                logger.debug("No text from DOCUMENT_TEXT_DETECTION, trying TEXT_DETECTION")
                response = self._client.text_detection(image=image)

                if response.error.message:
                    raise VisionAPIError(
                        message=f"Vision API returned error: {response.error.message}",
                        details={"api_error": response.error.message}
                    )

            # Extract text and confidence
            text, confidence = self._parse_response(response)

            logger.debug(
                f"Vision API extraction complete: "
                f"text_length={len(text)}, confidence={confidence:.4f}"
            )

            return text, confidence

        except VisionAPIError:
            raise

        except Exception as e:
            logger.error(f"Vision API request failed: {e}", exc_info=True)
            raise VisionAPIError(
                message=f"Vision API request failed: {str(e)}",
                details={"exception_type": type(e).__name__}
            )

    def _parse_response(self, response) -> Tuple[str, float]:
        """Parse Vision API response to extract text and confidence.

        Args:
            response: Vision API annotate response

        Returns:
            Tuple of (text, confidence)
        """
        text = ""
        confidence = 0.0

        # Try full text annotation first (from document detection)
        if response.full_text_annotation.text:
            text = response.full_text_annotation.text.strip()

            # Calculate average confidence from blocks
            confidences = []
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    if hasattr(block, 'confidence') and block.confidence:
                        confidences.append(block.confidence)

            if confidences:
                confidence = sum(confidences) / len(confidences)
            else:
                # API didn't provide confidence scores; use estimated default
                confidence = DEFAULT_CONFIDENCE_DOCUMENT_DETECTION

        # Fall back to text annotations (from text detection)
        elif response.text_annotations:
            text = response.text_annotations[0].description.strip()
            # TEXT_DETECTION doesn't provide confidence; use estimated default
            confidence = DEFAULT_CONFIDENCE_TEXT_DETECTION

        return text, confidence


# Global service instance
vision_service = VisionAPIService()
