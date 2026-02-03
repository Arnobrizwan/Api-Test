"""Image metadata extraction utilities."""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Optional
from datetime import datetime


def extract_image_metadata(image: Image.Image) -> dict:
    """
    Extract metadata from an image.

    Args:
        image: PIL Image object

    Returns:
        Dictionary containing image metadata
    """
    metadata = {
        "basic": extract_basic_info(image),
        "exif": extract_exif_data(image),
        "color": extract_color_info(image),
    }

    return metadata


def extract_basic_info(image: Image.Image) -> dict:
    """Extract basic image information."""
    return {
        "width": image.width,
        "height": image.height,
        "format": image.format,
        "mode": image.mode,
        "has_transparency": image.mode in ("RGBA", "LA", "P"),
        "is_animated": getattr(image, "is_animated", False),
        "n_frames": getattr(image, "n_frames", 1),
        "aspect_ratio": round(image.width / image.height, 2) if image.height > 0 else 0,
        "megapixels": round((image.width * image.height) / 1_000_000, 2),
    }


def extract_exif_data(image: Image.Image) -> Optional[dict]:
    """Extract EXIF metadata from image."""
    try:
        exif_data = image._getexif()
        if not exif_data:
            return None

        exif = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)

            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8", errors="ignore")
                except Exception:
                    value = str(value)

            if tag == "GPSInfo":
                gps_data = {}
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_data[gps_tag] = str(gps_value)
                value = gps_data

            if tag in ["MakerNote", "UserComment"]:
                continue

            exif[tag] = str(value) if not isinstance(value, (dict, list)) else value

        useful_tags = [
            "Make", "Model", "DateTime", "DateTimeOriginal", "DateTimeDigitized",
            "ExposureTime", "FNumber", "ISOSpeedRatings", "FocalLength",
            "ImageWidth", "ImageLength", "Orientation", "Software",
            "GPSInfo", "Flash", "WhiteBalance", "ExposureMode",
        ]

        filtered_exif = {k: v for k, v in exif.items() if k in useful_tags}

        return filtered_exif if filtered_exif else None

    except Exception:
        return None


def extract_color_info(image: Image.Image) -> dict:
    """Extract color information from image."""
    try:
        if image.mode != "RGB":
            rgb_image = image.convert("RGB")
        else:
            rgb_image = image

        small = rgb_image.resize((50, 50))
        pixels = list(small.getdata())

        if not pixels:
            return {}

        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)

        brightness = (avg_r + avg_g + avg_b) / 3 / 255

        return {
            "average_color": {"r": avg_r, "g": avg_g, "b": avg_b},
            "average_color_hex": f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}",
            "brightness": round(brightness, 2),
            "is_grayscale": image.mode in ("L", "LA", "1"),
        }

    except Exception:
        return {}


def get_image_quality_score(image: Image.Image) -> dict:
    """
    Estimate image quality for OCR purposes.

    Returns a score and recommendations.
    """
    score = 100
    recommendations = []

    if image.width < 100 or image.height < 100:
        score -= 30
        recommendations.append("Image resolution is very low. Consider using a higher resolution image.")
    elif image.width < 300 or image.height < 300:
        score -= 15
        recommendations.append("Image resolution is low. OCR accuracy may be reduced.")

    if image.mode == "L":
        pass
    elif image.mode in ("RGBA", "LA"):
        score -= 5
        recommendations.append("Image has transparency which may affect OCR.")

    aspect_ratio = image.width / image.height if image.height > 0 else 1
    if aspect_ratio > 10 or aspect_ratio < 0.1:
        score -= 10
        recommendations.append("Unusual aspect ratio may indicate a cropped or partial image.")

    try:
        if image.mode != "RGB":
            rgb_image = image.convert("RGB")
        else:
            rgb_image = image

        small = rgb_image.resize((50, 50))
        pixels = list(small.getdata())
        brightness = sum(sum(p) for p in pixels) / (len(pixels) * 3 * 255)

        if brightness < 0.2:
            score -= 15
            recommendations.append("Image appears too dark. Consider adjusting brightness.")
        elif brightness > 0.9:
            score -= 10
            recommendations.append("Image appears overexposed. Text may be washed out.")
    except Exception:
        pass

    return {
        "score": max(0, score),
        "quality": "good" if score >= 70 else "fair" if score >= 50 else "poor",
        "recommendations": recommendations,
    }
