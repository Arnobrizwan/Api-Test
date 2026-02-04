"""Tesseract OCR integration.

This module provides a service wrapper for Tesseract OCR with
image preprocessing, text extraction, and confidence scoring.
"""

import re
import threading
from typing import Tuple, Optional, Set

from PIL import Image

from ..core.config import settings
from ..core.exceptions import TesseractError
from ..core.logging import get_logger
from ..utils.image_utils import preprocess_image

logger = get_logger(__name__)

# Valid Tesseract language code pattern (ISO 639-3 codes, e.g., 'eng', 'deu', 'chi_sim')
LANG_CODE_PATTERN = re.compile(r'^[a-z]{3}(_[a-z]+)?(\+[a-z]{3}(_[a-z]+)?)*$')


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
        self._supported_languages: Optional[Set[str]] = None
        self._init_lock = threading.Lock()

    def _check_availability(self) -> None:
        """Check if Tesseract is installed and accessible (thread-safe)."""
        if self._available is not None:
            return

        with self._init_lock:
            # Double-check after acquiring lock
            if self._available is not None:
                return

            try:
                import pytesseract

                version = pytesseract.get_tesseract_version()
                self._version = str(version)
                # Cache supported languages at init
                self._supported_languages = set(pytesseract.get_languages())
                self._available = True
                logger.info(f"Tesseract OCR available: version {self._version}, "
                           f"languages: {len(self._supported_languages)}")

            except ImportError as e:
                self._init_error = f"pytesseract package not installed: {e}"
                self._available = False
                logger.warning(self._init_error)

            except (OSError, IOError) as e:
                self._init_error = f"Tesseract binary not found or not accessible: {e}"
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

    def _validate_language(self, lang: str) -> str:
        """Validate and sanitize language parameter.

        Args:
            lang: Language code(s) to validate

        Returns:
            Validated language string

        Raises:
            TesseractError: If language code is invalid
        """
        # Check format matches expected pattern
        if not LANG_CODE_PATTERN.match(lang):
            raise TesseractError(
                message=f"Invalid language code format: '{lang}'. Expected format like 'eng' or 'eng+deu'",
                details={"provided_lang": lang}
            )

        # Check if language is installed (if we have the list)
        if self._supported_languages:
            requested_langs = set(lang.split('+'))
            unsupported = requested_langs - self._supported_languages
            if unsupported:
                raise TesseractError(
                    message=f"Unsupported language(s): {unsupported}. "
                           f"Available: {sorted(self._supported_languages)[:10]}...",
                    details={"unsupported": list(unsupported), "requested": lang}
                )

        return lang

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
            lang: Language hint for OCR (default: 'eng'). Must be valid ISO 639-3 code.

        Returns:
            Tuple of (extracted_text, confidence_score)

        Raises:
            TesseractError: If OCR processing fails or language is invalid
        """
        self._check_availability()

        if not self._available:
            raise TesseractError(
                message=self._init_error or "Tesseract is not available",
                details={"init_error": self._init_error}
            )

        # Validate language parameter to prevent injection
        validated_lang = self._validate_language(lang)

        try:
            import pytesseract

            # Apply preprocessing if requested
            if preprocess:
                logger.debug("Applying image preprocessing")
                processed_image = preprocess_image(image)
            else:
                processed_image = image

            # Get detailed OCR data including confidence scores
            logger.debug(f"Running Tesseract OCR with lang={validated_lang}")
            data = pytesseract.image_to_data(
                processed_image,
                lang=validated_lang,
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

        except (OSError, IOError) as e:
            logger.error(f"Tesseract I/O error: {e}")
            raise TesseractError(
                message=f"Tesseract I/O error: {str(e)}",
                details={"exception_type": type(e).__name__}
            )

        except (KeyboardInterrupt, SystemExit):
            raise  # Don't catch system signals

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
