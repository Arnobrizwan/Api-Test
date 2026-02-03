"""Tests for image validators."""

import io
import pytest
from PIL import Image
from unittest.mock import AsyncMock, MagicMock

from app.utils.validators import validate_image_file, ValidationError


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content = content
        self.content_type = content_type

    async def read(self) -> bytes:
        return self.content


def create_valid_jpeg() -> bytes:
    """Create a valid JPEG image."""
    image = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


def create_valid_png() -> bytes:
    """Create a valid PNG image."""
    image = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


class TestValidateImageFile:
    """Tests for validate_image_file function."""

    @pytest.mark.asyncio
    async def test_valid_jpeg_jpg_extension(self):
        """Test validation passes for valid .jpg file."""
        content = create_valid_jpeg()
        file = MockUploadFile("test.jpg", content, "image/jpeg")
        image_bytes, pil_image = await validate_image_file(file)
        assert image_bytes == content
        assert pil_image is not None

    @pytest.mark.asyncio
    async def test_valid_jpeg_jpeg_extension(self):
        """Test validation passes for valid .jpeg file."""
        content = create_valid_jpeg()
        file = MockUploadFile("test.jpeg", content, "image/jpeg")
        image_bytes, pil_image = await validate_image_file(file)
        assert image_bytes == content

    @pytest.mark.asyncio
    async def test_missing_file(self):
        """Test validation fails for missing file."""
        with pytest.raises(ValidationError) as exc_info:
            await validate_image_file(None)
        assert exc_info.value.error_code == "MISSING_FILE"

    @pytest.mark.asyncio
    async def test_empty_filename(self):
        """Test validation fails for empty filename."""
        file = MockUploadFile("", b"content", "image/jpeg")
        with pytest.raises(ValidationError) as exc_info:
            await validate_image_file(file)
        assert exc_info.value.error_code == "MISSING_FILE"

    @pytest.mark.asyncio
    async def test_invalid_extension_png(self):
        """Test validation fails for PNG extension."""
        content = create_valid_png()
        file = MockUploadFile("test.png", content, "image/png")
        with pytest.raises(ValidationError) as exc_info:
            await validate_image_file(file)
        assert exc_info.value.error_code == "INVALID_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_invalid_extension_gif(self):
        """Test validation fails for GIF extension."""
        file = MockUploadFile("test.gif", b"content", "image/gif")
        with pytest.raises(ValidationError) as exc_info:
            await validate_image_file(file)
        assert exc_info.value.error_code == "INVALID_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_invalid_mime_type(self):
        """Test validation fails for wrong MIME type."""
        content = create_valid_jpeg()
        file = MockUploadFile("test.jpg", content, "image/png")
        with pytest.raises(ValidationError) as exc_info:
            await validate_image_file(file)
        assert exc_info.value.error_code == "INVALID_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_empty_file(self):
        """Test validation fails for empty file."""
        file = MockUploadFile("test.jpg", b"", "image/jpeg")
        with pytest.raises(ValidationError) as exc_info:
            await validate_image_file(file)
        assert exc_info.value.error_code == "INVALID_IMAGE"

    @pytest.mark.asyncio
    async def test_corrupted_image(self):
        """Test validation fails for corrupted image data."""
        file = MockUploadFile("test.jpg", b"not valid image data", "image/jpeg")
        with pytest.raises(ValidationError) as exc_info:
            await validate_image_file(file)
        assert exc_info.value.error_code == "INVALID_IMAGE"

    @pytest.mark.asyncio
    async def test_case_insensitive_extension(self):
        """Test validation handles uppercase extensions."""
        content = create_valid_jpeg()
        file = MockUploadFile("test.JPG", content, "image/jpeg")
        image_bytes, pil_image = await validate_image_file(file)
        assert image_bytes == content

    @pytest.mark.asyncio
    async def test_case_insensitive_extension_jpeg(self):
        """Test validation handles uppercase JPEG extension."""
        content = create_valid_jpeg()
        file = MockUploadFile("test.JPEG", content, "image/jpeg")
        image_bytes, pil_image = await validate_image_file(file)
        assert image_bytes == content
