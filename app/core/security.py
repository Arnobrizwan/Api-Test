"""Security utilities and middleware.

This module provides security-related functions including
input sanitization, file validation, and security headers.
"""

import re
import hashlib
import secrets
from typing import Optional, Tuple
from functools import lru_cache

# Patterns for detecting potentially malicious content
SUSPICIOUS_PATTERNS = [
    rb'<script',  # Script tags
    rb'javascript:',  # JavaScript URLs
    rb'data:text/html',  # Data URLs with HTML
    rb'<?php',  # PHP tags
    rb'<%',  # ASP/JSP tags
]

# Magic bytes for image formats
IMAGE_SIGNATURES = {
    b'\xff\xd8\xff': 'jpeg',
    b'\x89PNG\r\n\x1a\n': 'png',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',  # WebP starts with RIFF
    b'BM': 'bmp',
    b'II*\x00': 'tiff',  # Little-endian TIFF
    b'MM\x00*': 'tiff',  # Big-endian TIFF
}


def validate_image_magic_bytes(content: bytes) -> Tuple[bool, Optional[str]]:
    """Validate image content by checking magic bytes.

    This provides an additional layer of security beyond MIME type
    checking to ensure the file content matches the expected format.

    Args:
        content: Raw file content bytes

    Returns:
        Tuple of (is_valid, detected_format)
    """
    if len(content) < 8:
        return False, None

    for signature, format_name in IMAGE_SIGNATURES.items():
        if content.startswith(signature):
            return True, format_name

    # Special case for WebP (check for WEBP after RIFF)
    if content[:4] == b'RIFF' and len(content) >= 12:
        if content[8:12] == b'WEBP':
            return True, 'webp'

    return False, None


def check_for_suspicious_content(content: bytes) -> bool:
    """Check file content for suspicious patterns.

    Scans the first portion of the file for patterns that might
    indicate an attempt to embed malicious content.

    Args:
        content: Raw file content bytes

    Returns:
        True if suspicious content is detected
    """
    # Only check first 1KB for performance
    check_content = content[:1024].lower()

    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.lower() in check_content:
            return True

    return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and injection.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for use
    """
    if not filename:
        return "unnamed"

    # Remove path components
    filename = filename.replace('\\', '/').split('/')[-1]

    # Remove null bytes and control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # Remove potentially dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)

    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:max_length - len(ext) - 1] + '.' + ext if ext else name[:max_length]

    return filename or "unnamed"


def compute_content_hash(content: bytes, algorithm: str = "sha256") -> str:
    """Compute cryptographic hash of content.

    Args:
        content: Content to hash
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        Hexadecimal hash string
    """
    if algorithm == "sha256":
        return hashlib.sha256(content).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(content).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(content).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def generate_request_id() -> str:
    """Generate a unique request ID for tracing.

    Returns:
        Unique hex string suitable for request tracing
    """
    return secrets.token_hex(16)


@lru_cache(maxsize=1)
def get_security_headers() -> dict:
    """Get security headers for API responses.

    Returns:
        Dictionary of security headers
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }


def validate_content_length(content_length: Optional[int], max_size: int) -> bool:
    """Validate Content-Length header before reading body.

    Args:
        content_length: Content-Length header value
        max_size: Maximum allowed size in bytes

    Returns:
        True if content length is valid
    """
    if content_length is None:
        return True  # Allow streaming uploads

    return 0 < content_length <= max_size
