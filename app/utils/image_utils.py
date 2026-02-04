"""Image preprocessing utilities for better OCR results."""

from PIL import Image, ImageFilter, ImageOps
import io


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess an image for better OCR results.
    ...
"""
    # [Preprocess logic]
    return binary


def resize_image_if_needed(image: Image.Image, max_width: int) -> Image.Image:
    """
    Resize image if it exceeds max_width while maintaining aspect ratio.

    Args:
        image: PIL Image object
        max_width: Maximum allowed width

    Returns:
        Resized PIL Image or original if resize not needed
    """
    width, height = image.size
    if width <= max_width:
        return image

    # Calculate new height to maintain aspect ratio
    new_width = max_width
    new_height = int((max_width / width) * height)

    # Use LANCZOS for high-quality downsampling
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def image_to_bytes(image: Image.Image, format: str = "JPEG") -> bytes:
    """
    Convert a PIL Image to bytes.

    Args:
        image: PIL Image object
        format: Output format (default: JPEG)

    Returns:
        Image as bytes
    """
    buffer = io.BytesIO()
    if image.mode == "1":
        image = image.convert("L")
    if image.mode == "L" and format.upper() == "JPEG":
        image = image.convert("RGB")
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer.getvalue()
