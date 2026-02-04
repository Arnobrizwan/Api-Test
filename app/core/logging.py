"""Structured logging configuration.

This module provides centralized logging setup with structured
JSON logging support for better observability in production.
"""

import logging
import re
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional

# Patterns for sensitive data that should be redacted in logs
SENSITIVE_PATTERNS = [
    (re.compile(r'(api[_-]?key|apikey|authorization|auth[_-]?token|password|secret|credential)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
    (re.compile(r'(Bearer\s+)[A-Za-z0-9\-_]+\.?[A-Za-z0-9\-_]*\.?[A-Za-z0-9\-_]*', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'X-API-Key:\s*\S+', re.IGNORECASE), 'X-API-Key: ***REDACTED***'),
]


def _sanitize_sensitive_data(text: str) -> str:
    """Remove sensitive data from log messages.

    Args:
        text: The text to sanitize

    Returns:
        Sanitized text with sensitive data redacted
    """
    if not text:
        return text

    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)

    return text


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging.

    Outputs logs in JSON format for easy parsing by log aggregation tools.
    Sanitizes sensitive data before logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": _sanitize_sensitive_data(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present (sanitized)
        if record.exc_info:
            exception_text = self.formatException(record.exc_info)
            log_data["exception"] = _sanitize_sensitive_data(exception_text)

        # Add extra fields (sanitized)
        if hasattr(record, "extra_data"):
            sanitized_extra = {}
            for key, value in record.extra_data.items():
                if isinstance(value, str):
                    sanitized_extra[key] = _sanitize_sensitive_data(value)
                else:
                    sanitized_extra[key] = value
            log_data["extra"] = sanitized_extra

        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """Standard formatter for development/debug logging."""

    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatting for production
        logger_name: Specific logger name, or None for root logger

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Set formatter based on environment
    if json_format:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(StandardFormatter())

    logger.addHandler(handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra context to logs.

    Usage:
        with LogContext(request_id="123", user_id="456"):
            logger.info("Processing request")
    """

    def __init__(self, **kwargs):
        self.extra_data = kwargs
        self._old_factory = None

    def __enter__(self):
        self._old_factory = logging.getLogRecordFactory()

        extra_data = self.extra_data

        def record_factory(*args, **kwargs):
            record = self._old_factory(*args, **kwargs)
            record.extra_data = extra_data
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self._old_factory)
        return False
