"""Image preprocessing utilities for better OCR results."""

from PIL import Image, ImageFilter, ImageOps
import io


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess an image for better OCR results.

    Steps:
    1. Convert to RGB if necessary
    2. Convert to grayscale
    3. Apply contrast enhancement
    4. Apply slight sharpening
    5. Apply adaptive thresholding (binarization)

    Args:
        image: PIL Image object

    Returns:
        Preprocessed PIL Image
    """
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    grayscale = ImageOps.grayscale(image)

    enhanced = ImageOps.autocontrast(grayscale, cutoff=1)

    sharpened = enhanced.filter(ImageFilter.SHARPEN)

    threshold = 127
    binary = sharpened.point(lambda x: 255 if x > threshold else 0, mode="1")
    binary = binary.convert("L")

    return binary


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
