"""Tesseract OCR integration.

This module provides a service wrapper for Tesseract OCR with
image preprocessing, text extraction, and confidence scoring.
"""

from typing import Tuple, Optional

from PIL import Image

from ..core.config import settings
from ..core.exceptions import TesseractError
from ..core.logging import get_logger
from ..utils.image_utils import preprocess_image

logger = get_logger(__name__)


class TesseractService:
    """Service for Tesseract OCR processing.

    Provides image preprocessing and OCR capabilities using Tesseract
    with proper error handling and confidence scoring.

    Attributes:
        _available: Cached availability status
        _version: Tesseract version string
    """

    def __init__(self):
        """Initialize Tesseract service."""
        self._available: Optional[bool] = None
        self._version: Optional[str] = None
        self._init_error: Optional[str] = None

    def _check_availability(self) -> None:
        """Check if Tesseract is installed and accessible."""
        if self._available is not None:
            return

        try:
            import pytesseract

            version = pytesseract.get_tesseract_version()
            self._version = str(version)
            self._available = True
            logger.info(f"Tesseract OCR available: version {self._version}")

        except ImportError as e:
            self._init_error = f"pytesseract package not installed: {e}"
            self._available = False
            logger.warning(self._init_error)

        except Exception as e:
            self._init_error = f"Tesseract not available: {e}"
            self._available = False
            logger.warning(self._init_error)

    @property
    def is_available(self) -> bool:
        """Check if Tesseract is available for use.

        Returns:
            True if Tesseract is installed and accessible
        """
        self._check_availability()
        return self._available or False

    @property
    def version(self) -> Optional[str]:
        """Get Tesseract version string.

        Returns:
            Version string or None if not available
        """
        self._check_availability()
        return self._version

    def extract_text(
        self,
        image: Image.Image,
        preprocess: bool = True,
        lang: str = "eng"
    ) -> Tuple[str, float]:
        """Extract text from an image using Tesseract OCR.

        Args:
            image: PIL Image object
            preprocess: Whether to apply preprocessing (default: True)
            lang: Language hint for OCR (default: 'eng')

        Returns:
            Tuple of (extracted_text, confidence_score)

        Raises:
            TesseractError: If OCR processing fails
        """
        self._check_availability()

        if not self._available:
            raise TesseractError(
                message=self._init_error or "Tesseract is not available",
                details={"init_error": self._init_error}
            )

        try:
            import pytesseract

            # Apply preprocessing if requested
            if preprocess:
                logger.debug("Applying image preprocessing")
                processed_image = preprocess_image(image)
            else:
                processed_image = image

            # Get detailed OCR data including confidence scores
            logger.debug(f"Running Tesseract OCR with lang={lang}")
            data = pytesseract.image_to_data(
                processed_image,
                lang=lang,
                output_type=pytesseract.Output.DICT
            )

            # Extract text and calculate confidence
            text, confidence = self._parse_ocr_data(data)

            logger.debug(
                f"Tesseract extraction complete: "
                f"text_length={len(text)}, confidence={confidence:.4f}"
            )

            return text, confidence

        except TesseractError:
            raise

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}", exc_info=True)
            raise TesseractError(
                message=f"Tesseract OCR failed: {str(e)}",
                details={"exception_type": type(e).__name__}
            )

    def _parse_ocr_data(self, data: dict) -> Tuple[str, float]:
        """Parse Tesseract OCR output data.

        Args:
            data: Dictionary output from image_to_data

        Returns:
            Tuple of (text, confidence)
        """
        text_parts = []
        confidences = []

        for i, word in enumerate(data.get("text", [])):
            word_stripped = word.strip()
            if word_stripped:
                text_parts.append(word_stripped)

                # Get confidence (Tesseract uses -1 for invalid)
                conf = data.get("conf", [])[i] if i < len(data.get("conf", [])) else -1
                if conf != -1 and conf >= 0:
                    # Tesseract returns confidence as 0-100
                    confidences.append(conf / 100.0)

        # Join words and normalize whitespace
        text = " ".join(text_parts)
        text = " ".join(text.split())  # Normalize whitespace

        # Calculate average confidence
        if confidences:
            confidence = sum(confidences) / len(confidences)
        else:
            confidence = 0.0

        return text, confidence

    def get_supported_languages(self) -> list:
        """Get list of languages supported by Tesseract.

        Returns:
            List of language codes, or empty list if unavailable
        """
        if not self.is_available:
            return []

        try:
            import pytesseract
            return pytesseract.get_languages()
        except Exception as e:
            logger.warning(f"Failed to get Tesseract languages: {e}")
            return []


# Global service instance
tesseract_service = TesseractService()
