"""Text preprocessing and cleanup utilities."""

import re
import unicodedata
from typing import Optional


def cleanup_text(text: str, options: Optional[dict] = None) -> str:
    """
    Clean up and format extracted OCR text.

    Args:
        text: Raw extracted text
        options: Optional dict with cleanup options:
            - remove_extra_whitespace: bool (default: True)
            - remove_line_breaks: bool (default: False)
            - normalize_unicode: bool (default: True)
            - remove_special_chars: bool (default: False)
            - lowercase: bool (default: False)
            - uppercase: bool (default: False)
            - trim: bool (default: True)

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    options = options or {}

    if options.get("normalize_unicode", True):
        text = unicodedata.normalize("NFKC", text)

    if options.get("remove_extra_whitespace", True):
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)

    if options.get("remove_line_breaks", False):
        text = re.sub(r"\n+", " ", text)

    if options.get("remove_special_chars", False):
        text = re.sub(r"[^\w\s.,!?;:'\"-]", "", text)

    if options.get("lowercase", False):
        text = text.lower()
    elif options.get("uppercase", False):
        text = text.upper()

    if options.get("trim", True):
        text = text.strip()
        text = "\n".join(line.strip() for line in text.split("\n"))

    return text


def format_as_paragraphs(text: str) -> str:
    """Format text into clean paragraphs."""
    if not text:
        return ""

    paragraphs = re.split(r"\n{2,}", text)
    cleaned_paragraphs = []

    for para in paragraphs:
        para = re.sub(r"\s+", " ", para).strip()
        if para:
            cleaned_paragraphs.append(para)

    return "\n\n".join(cleaned_paragraphs)


def extract_emails(text: str) -> list:
    """Extract email addresses from text."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> list:
    """Extract phone numbers from text.

    Supports common US/international formats with validation to reduce false positives.
    """
    phone_patterns = [
        # US format: (123) 456-7890, 123-456-7890, 123.456.7890, +1 123 456 7890
        r"(?:\+1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?[2-9]\d{2}[-.\s]?\d{4}",
        # International format: +XX XXX XXX XXXX (with country code)
        r"\+[1-9]\d{0,2}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
    ]
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        # Filter out matches that are likely not phone numbers (e.g., too many digits)
        for match in matches:
            # Remove non-digit characters and check length
            digits_only = re.sub(r'\D', '', match)
            if 10 <= len(digits_only) <= 15:  # Valid phone numbers are 10-15 digits
                phones.append(match.strip())
    return list(set(phones))


def extract_urls(text: str) -> list:
    """Extract URLs from text."""
    url_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
    return re.findall(url_pattern, text)


def extract_dates(text: str) -> list:
    """Extract common date formats from text."""
    date_patterns = [
        r"\d{1,2}/\d{1,2}/\d{2,4}",
        r"\d{1,2}-\d{1,2}-\d{2,4}",
        r"\d{4}-\d{2}-\d{2}",
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}",
        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}",
    ]
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    return dates


def get_word_count(text: str) -> int:
    """Get word count from text."""
    if not text:
        return 0
    words = text.split()
    return len(words)


def get_character_count(text: str, include_spaces: bool = True) -> int:
    """Get character count from text."""
    if not text:
        return 0
    if include_spaces:
        return len(text)
    return len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
