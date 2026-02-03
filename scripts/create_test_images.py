#!/usr/bin/env python3
"""Script to create sample test images for OCR testing."""

import os
from PIL import Image, ImageDraw, ImageFont


def create_text_sample_image(output_path: str):
    """Create an image with sample text for OCR testing."""
    width, height = 600, 200
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except OSError:
            font = ImageFont.load_default()

    text_lines = [
        "Hello, World!",
        "This is a sample OCR test image.",
        "Testing 123... Special chars: @#$%",
    ]

    y_position = 30
    for line in text_lines:
        draw.text((20, y_position), line, fill="black", font=font)
        y_position += 50

    image.save(output_path, "JPEG", quality=95)
    print(f"Created: {output_path}")


def create_no_text_image(output_path: str):
    """Create a blank image with no text."""
    width, height = 200, 200
    image = Image.new("RGB", (width, height), color="lightgray")
    draw = ImageDraw.Draw(image)
    draw.rectangle([10, 10, 190, 190], outline="gray", width=2)
    draw.ellipse([50, 50, 150, 150], fill="white", outline="darkgray")

    image.save(output_path, "JPEG", quality=95)
    print(f"Created: {output_path}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    sample_images_dir = os.path.join(project_dir, "tests", "sample_images")

    os.makedirs(sample_images_dir, exist_ok=True)

    create_text_sample_image(os.path.join(sample_images_dir, "text_sample.jpg"))
    create_no_text_image(os.path.join(sample_images_dir, "no_text.jpg"))

    print(f"\nSample images created in: {sample_images_dir}")


if __name__ == "__main__":
    main()
