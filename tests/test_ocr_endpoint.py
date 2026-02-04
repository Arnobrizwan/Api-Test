"""Tests for OCR API endpoint."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont
from unittest.mock import patch, MagicMock, PropertyMock

from app.main import app

client = TestClient(app)


def create_test_image_with_text(text: str = "Hello World") -> bytes:
    """Create a test image with text for OCR testing."""
    image = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 30), text, fill="black")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


def create_blank_test_image() -> bytes:
    """Create a blank test image with no text."""
    image = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestExtractTextEndpoint:
    """Tests for extract-text endpoint."""

    def test_missing_file(self):
        """Test error when no file is uploaded."""
        response = client.post("/extract-text")
        assert response.status_code == 422

    def test_invalid_file_type_text(self):
        """Test error when uploading text file."""
        response = client.post(
            "/extract-text",
            files={"image": ("test.txt", b"not an image", "text/plain")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_FILE_TYPE"

    @patch("app.services.vision_api.VisionAPIService.is_available", new_callable=PropertyMock)
    @patch("app.services.tesseract.TesseractService.is_available", new_callable=PropertyMock)
    @patch("app.services.tesseract.tesseract_service.extract_text")
    def test_successful_extraction_tesseract(self, mock_extract, mock_tess_avail, mock_vision_avail):
        """Test successful text extraction with Tesseract."""
        mock_vision_avail.return_value = False
        mock_tess_avail.return_value = True
        mock_extract.return_value = ("Hello World", 0.85)

        image_bytes = create_test_image_with_text("Hello World")
        response = client.post(
            "/extract-text",
            files={"image": ("test.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "Hello World"
        assert data["confidence"] == 0.85
        assert data["ocr_engine"] == "tesseract"
        assert "processing_time_ms" in data

    @patch("app.services.vision_api.VisionAPIService.is_available", new_callable=PropertyMock)
    @patch("app.services.vision_api.vision_service.extract_text")
    def test_successful_extraction_vision(self, mock_extract, mock_vision_avail):
        """Test successful text extraction with Cloud Vision."""
        mock_vision_avail.return_value = True
        mock_extract.return_value = ("Hello World", 0.95)

        image_bytes = create_test_image_with_text("Hello World")
        response = client.post(
            "/extract-text",
            files={"image": ("test.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "Hello World"
        assert data["confidence"] == 0.95
        assert data["ocr_engine"] == "cloud_vision"

    @patch("app.services.vision_api.VisionAPIService.is_available", new_callable=PropertyMock)
    @patch("app.services.vision_api.vision_service.extract_text")
    @patch("app.services.tesseract.TesseractService.is_available", new_callable=PropertyMock)
    @patch("app.services.tesseract.tesseract_service.extract_text")
    def test_fallback_to_tesseract(self, mock_tesseract, mock_tess_avail, mock_vision, mock_vision_avail):
        """Test fallback to Tesseract when Vision API fails."""
        mock_vision_avail.return_value = True
        mock_tess_avail.return_value = True
        mock_vision.side_effect = Exception("Vision API error")
        mock_tesseract.return_value = ("Fallback text", 0.75)

        image_bytes = create_test_image_with_text()
        response = client.post(
            "/extract-text",
            files={"image": ("test.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "Fallback text"
        assert data["ocr_engine"] == "tesseract"

    @patch("app.services.vision_api.VisionAPIService.is_available", new_callable=PropertyMock)
    @patch("app.services.tesseract.TesseractService.is_available", new_callable=PropertyMock)
    def test_all_engines_unavailable(self, mock_tess_avail, mock_vision_avail):
        """Test error when all OCR engines are unavailable."""
        mock_vision_avail.return_value = False
        mock_tess_avail.return_value = False
        image_bytes = create_test_image_with_text()
        response = client.post(
            "/extract-text",
            files={"image": ("test.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "OCR_FAILED"


class TestValidators:
    """Tests for image validators."""

    def test_empty_file(self):
        """Test error when uploading empty file."""
        response = client.post(
            "/extract-text",
            files={"image": ("test.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_IMAGE"

    def test_valid_jpeg_file(self):
        """Test that valid JPEG file passes validation."""
        image_bytes = create_test_image_with_text()

        with patch("app.services.ocr_service.ocr_service.extract_text") as mock_ocr:
            mock_ocr.return_value = MagicMock(
                success=True,
                text="Test",
                text_formatted="Test",
                confidence=0.9,
                processing_time_ms=100,
                ocr_engine="tesseract",
                cached=False,
                text_stats=None,
                entities=None,
                image_metadata=None,
                quality_assessment=None,
                model_dump=lambda: {
                    "success": True,
                    "text": "Test",
                    "text_formatted": "Test",
                    "confidence": 0.9,
                    "processing_time_ms": 100,
                    "ocr_engine": "tesseract",
                    "cached": False,
                    "text_stats": None,
                    "entities": None,
                    "image_metadata": None,
                    "quality_assessment": None,
                },
            )

            response = client.post(
                "/extract-text",
                files={"image": ("test.jpg", image_bytes, "image/jpeg")},
            )
            assert response.status_code == 200
