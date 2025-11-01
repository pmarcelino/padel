"""
Configuration management using Pydantic settings.

This module provides a centralized configuration system that loads settings from
environment variables and .env files. All settings are validated at startup and
immutable after initialization.

Usage:
    from src.config import settings

    api_key = settings.google_api_key
    data_path = settings.processed_data_dir / "facilities.csv"
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class provides type-safe access to all application configuration.
    Settings are loaded from environment variables and .env files, with
    environment variables taking precedence.

    All settings are immutable after initialization to prevent accidental
    modification during runtime.

    Attributes:
        google_api_key: Google Maps API key (required)
        openai_api_key: OpenAI API key (optional, for LLM analysis)
        anthropic_api_key: Anthropic API key (optional, for LLM analysis)
        llm_provider: LLM provider to use ('openai' or 'anthropic')
        llm_model: Specific LLM model to use
        project_root: Root directory of the project
        data_dir: Main data directory
        raw_data_dir: Directory for raw/unprocessed data
        processed_data_dir: Directory for processed data
        cache_dir: Directory for API response cache
        exports_dir: Directory for exported reports
        search_region: Geographic region to search for facilities
        cache_enabled: Whether to enable API response caching
        cache_ttl_days: Cache time-to-live in days
        rate_limit_delay: Delay between API requests in seconds
        min_rating: Minimum facility rating (0.0 to 5.0)
        max_rating: Maximum facility rating (0.0 to 5.0)
        population_weight: Weight for population/demand factor
        saturation_weight: Weight for market saturation factor
        quality_gap_weight: Weight for quality gap factor
        geographic_gap_weight: Weight for geographic coverage gap factor
    """

    # ============================================================================
    # API Keys
    # ============================================================================

    google_api_key: str = Field(
        ...,
        env="GOOGLE_API_KEY",
        description="Google Maps API key (required for Places API and Geocoding)",
    )

    openai_api_key: Optional[str] = Field(
        None, env="OPENAI_API_KEY", description="OpenAI API key (optional, for GPT models)"
    )

    anthropic_api_key: Optional[str] = Field(
        None, env="ANTHROPIC_API_KEY", description="Anthropic API key (optional, for Claude models)"
    )

    llm_provider: str = Field(
        "openai", env="LLM_PROVIDER", description='LLM provider to use: "openai" or "anthropic"'
    )

    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL", description="Specific LLM model to use")

    # ============================================================================
    # Paths (computed from project root)
    # ============================================================================

    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.resolve(),
        description="Root directory of the project",
    )

    data_dir: Optional[Path] = Field(
        None, description="Main data directory (auto-computed from project_root)"
    )

    raw_data_dir: Optional[Path] = Field(None, description="Directory for raw/unprocessed data")

    processed_data_dir: Optional[Path] = Field(None, description="Directory for processed data")

    cache_dir: Optional[Path] = Field(None, description="Directory for API response cache")

    exports_dir: Optional[Path] = Field(None, description="Directory for exported reports")

    # ============================================================================
    # Data Collection Settings
    # ============================================================================

    search_region: str = Field(
        "Algarve, Portugal",
        env="SEARCH_REGION",
        description="Geographic region to search for padel facilities",
    )

    cache_enabled: bool = Field(
        True, env="CACHE_ENABLED", description="Enable caching for API responses"
    )

    cache_ttl_days: int = Field(30, env="CACHE_TTL_DAYS", description="Cache time-to-live in days")

    rate_limit_delay: float = Field(
        0.2,
        env="RATE_LIMIT_DELAY",
        description="Delay between API requests in seconds (to respect rate limits)",
    )

    # ============================================================================
    # Analysis Settings
    # ============================================================================

    min_rating: float = Field(
        0.0, env="MIN_RATING", description="Minimum rating for facilities (0.0 to 5.0)"
    )

    max_rating: float = Field(
        5.0, env="MAX_RATING", description="Maximum rating for facilities (0.0 to 5.0)"
    )

    # ============================================================================
    # Opportunity Scoring Weights (must sum to 1.0)
    # ============================================================================

    population_weight: float = Field(
        0.2, env="POPULATION_WEIGHT", description="Weight for population/demand factor (0.0 to 1.0)"
    )

    saturation_weight: float = Field(
        0.3, env="SATURATION_WEIGHT", description="Weight for market saturation factor (0.0 to 1.0)"
    )

    quality_gap_weight: float = Field(
        0.2, env="QUALITY_GAP_WEIGHT", description="Weight for quality gap factor (0.0 to 1.0)"
    )

    geographic_gap_weight: float = Field(
        0.3,
        env="GEOGRAPHIC_GAP_WEIGHT",
        description="Weight for geographic coverage gap factor (0.0 to 1.0)",
    )

    # ============================================================================
    # Configuration
    # ============================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,  # Make settings immutable after initialization
        extra="forbid",  # Forbid extra fields
    )

    def __init__(self, **kwargs):
        """
        Initialize settings and compute derived paths.

        This method automatically computes all data directory paths from
        the project root after base initialization.
        """
        super().__init__(**kwargs)

        # Compute derived paths if not explicitly provided
        # Using object.__setattr__ because model is frozen
        if self.data_dir is None:
            object.__setattr__(self, "data_dir", self.project_root / "data")
        if self.raw_data_dir is None:
            object.__setattr__(self, "raw_data_dir", self.data_dir / "raw")
        if self.processed_data_dir is None:
            object.__setattr__(self, "processed_data_dir", self.data_dir / "processed")
        if self.cache_dir is None:
            object.__setattr__(self, "cache_dir", self.data_dir / "cache")
        if self.exports_dir is None:
            object.__setattr__(self, "exports_dir", self.data_dir / "exports")

    # ============================================================================
    # Validators
    # ============================================================================

    @field_validator("google_api_key")
    @classmethod
    def validate_google_api_key(cls, v: str) -> str:
        """
        Validate Google API key.

        Args:
            v: The API key value

        Returns:
            The validated API key

        Raises:
            ValueError: If API key is empty or too short
        """
        if not v or len(v.strip()) == 0:
            raise ValueError("GOOGLE_API_KEY cannot be empty")
        if len(v) < 10:
            raise ValueError("GOOGLE_API_KEY must be at least 10 characters long")
        return v

    @field_validator("rate_limit_delay")
    @classmethod
    def validate_rate_limit_delay(cls, v: float) -> float:
        """
        Validate rate limit delay.

        Args:
            v: The rate limit delay value

        Returns:
            The validated rate limit delay

        Raises:
            ValueError: If delay is not positive
        """
        if v <= 0:
            raise ValueError("rate_limit_delay must be greater than 0")
        return v

    @field_validator("cache_ttl_days")
    @classmethod
    def validate_cache_ttl_days(cls, v: int) -> int:
        """
        Validate cache TTL days.

        Args:
            v: The cache TTL value

        Returns:
            The validated cache TTL

        Raises:
            ValueError: If TTL is negative
        """
        if v < 0:
            raise ValueError("cache_ttl_days cannot be negative")
        return v

    @field_validator("min_rating", "max_rating")
    @classmethod
    def validate_rating_range(cls, v: float) -> float:
        """
        Validate rating values are within valid range.

        Args:
            v: The rating value

        Returns:
            The validated rating

        Raises:
            ValueError: If rating is outside 0-5 range
        """
        if not (0.0 <= v <= 5.0):
            raise ValueError("Rating must be between 0.0 and 5.0")
        return v

    @field_validator("max_rating")
    @classmethod
    def validate_rating_bounds(cls, v: float, info) -> float:
        """
        Validate that max_rating is greater than min_rating.

        Args:
            v: The max_rating value
            info: Validation context with other field values

        Returns:
            The validated max_rating

        Raises:
            ValueError: If max_rating is less than or equal to min_rating
        """
        min_rating = info.data.get("min_rating")
        if min_rating is not None and v <= min_rating:
            raise ValueError("max_rating must be greater than min_rating")
        return v

    @field_validator("population_weight", "saturation_weight", "quality_gap_weight")
    @classmethod
    def validate_weight_range(cls, v: float) -> float:
        """
        Validate individual weights are within valid range.

        Args:
            v: The weight value

        Returns:
            The validated weight

        Raises:
            ValueError: If weight is outside 0-1 range
        """
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("geographic_gap_weight")
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """
        Validate that all scoring weights sum to approximately 1.0.

        This validator runs last (on geographic_gap_weight) to ensure all
        weights have been set before checking their sum.

        Args:
            v: The geographic_gap_weight value
            info: Validation context with other field values

        Returns:
            The validated geographic_gap_weight

        Raises:
            ValueError: If weights don't sum to approximately 1.0 (within 0.99-1.01)
        """
        # First validate this weight is in range
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {v}")

        # Calculate total weight sum
        total = (
            info.data.get("population_weight", 0)
            + info.data.get("saturation_weight", 0)
            + info.data.get("quality_gap_weight", 0)
            + v  # geographic_gap_weight
        )

        # Allow small tolerance for floating point arithmetic
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Scoring weights must sum to 1.0 (±0.01 tolerance), got {total:.4f}. "
                f"population_weight={info.data.get('population_weight')}, "
                f"saturation_weight={info.data.get('saturation_weight')}, "
                f"quality_gap_weight={info.data.get('quality_gap_weight')}, "
                f"geographic_gap_weight={v}"
            )

        return v


# ============================================================================
# Singleton Instance
# ============================================================================

# Create singleton instance that will be imported by other modules
# This instance is lazy-loaded when first imported
settings = Settings()
