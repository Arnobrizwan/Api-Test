"""Application configuration management.

This module provides centralized configuration using pydantic-settings
for type-safe environment variable handling with validation.
"""

import re
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valid rate limit pattern: number/period (e.g., "60/minute", "100/hour")
RATE_LIMIT_PATTERN = re.compile(r"^\d+/(second|minute|hour|day)$")


class Settings(BaseSettings):
    """Application settings with validation and defaults.

    All settings can be overridden via environment variables.
    Environment variables take precedence over default values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Application
    app_name: str = Field(default="OCR Image Text Extraction API")
    app_version: str = Field(default="1.2.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Google Cloud
    gcp_project_id: Optional[str] = Field(default=None)
    google_application_credentials: Optional[str] = Field(default=None)
    use_tesseract_only: bool = Field(default=False)

    # File Upload Limits
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    max_batch_size: int = Field(default=10)

    # Rate Limiting
    rate_limit: str = Field(default="60/minute")
    rate_limit_batch: str = Field(default="10/minute")

    # Caching
    enable_cache: bool = Field(default=True)
    cache_type: str = Field(default="in-memory")  # "in-memory" or "redis"
    cache_max_size: int = Field(default=100)  # For in-memory cache
    cache_ttl_seconds: int = Field(default=3600)

    # Optimization
    max_image_width: int = Field(default=2000)  # Auto-resize if wider than this

    # Redis Settings
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)
    redis_ssl: bool = Field(default=False)  # Enable SSL for Redis (required for cloud Redis)
    redis_required: bool = Field(default=False)  # If True, app fails fast when Redis is unavailable
    
    # Upstash Redis REST API (alternative connection method)
    upstash_redis_rest_url: Optional[str] = Field(default=None)
    upstash_redis_rest_token: Optional[str] = Field(default=None)

    # Security
    api_key: Optional[str] = Field(default=None)  # API Key for authentication
    cors_origins: str = Field(default="*")

    # Timeouts (in seconds)
    ocr_timeout: int = Field(default=30)
    vision_api_timeout: int = Field(default=25)
    tesseract_timeout: int = Field(default=20)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Validate file size is within reasonable bounds."""
        min_size = 1024  # 1KB
        max_size = 50 * 1024 * 1024  # 50MB
        if not min_size <= v <= max_size:
            raise ValueError(f"max_file_size must be between {min_size} and {max_size}")
        return v

    @field_validator("cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL is positive and reasonable."""
        if v < 60:
            raise ValueError("cache_ttl_seconds must be at least 60 seconds")
        if v > 86400:  # 24 hours
            raise ValueError("cache_ttl_seconds must not exceed 86400 (24 hours)")
        return v

    @field_validator("rate_limit", "rate_limit_batch")
    @classmethod
    def validate_rate_limit(cls, v: str) -> str:
        """Validate rate limit format (e.g., '60/minute')."""
        if not RATE_LIMIT_PATTERN.match(v):
            raise ValueError(
                f"Invalid rate limit format: {v}. "
                "Must be in format 'number/period' (e.g., '60/minute', '100/hour')"
            )
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses LRU cache to ensure settings are only loaded once.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
