"""
Tests for configuration management (src/config.py).

Following TDD approach: tests written first, implementation follows.
"""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError


def test_settings_loads_from_env(tmp_path, monkeypatch):
    """Test settings loads correctly from .env file."""
    # Create a temporary .env file
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=test_key_123456789\n")

    # Set the env file path
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    settings = Settings()

    assert settings.google_api_key == "test_key_123456789"


def test_missing_required_key_raises_error():
    """Test missing GOOGLE_API_KEY raises ValidationError."""
    from src.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    # Check that the error is about the missing google_api_key field
    assert "google_api_key" in str(exc_info.value).lower()


def test_default_values_applied(monkeypatch):
    """Test default values are used when not specified."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    settings = Settings()

    assert settings.search_region == "Algarve, Portugal"
    assert settings.cache_enabled is True
    assert settings.cache_ttl_days == 30
    assert settings.rate_limit_delay == 0.2
    assert settings.llm_provider == "openai"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.min_rating == 0.0
    assert settings.max_rating == 5.0
    assert settings.population_weight == 0.2
    assert settings.saturation_weight == 0.3
    assert settings.quality_gap_weight == 0.2
    assert settings.geographic_gap_weight == 0.3


def test_paths_are_computed_correctly(monkeypatch):
    """Test data directory paths are auto-computed."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    settings = Settings()

    # Verify project root is set
    assert settings.project_root is not None
    assert isinstance(settings.project_root, Path)
    assert settings.project_root.is_absolute()

    # Verify all paths are computed correctly
    assert settings.data_dir == settings.project_root / "data"
    assert settings.raw_data_dir == settings.data_dir / "raw"
    assert settings.processed_data_dir == settings.data_dir / "processed"
    assert settings.cache_dir == settings.data_dir / "cache"
    assert settings.exports_dir == settings.data_dir / "exports"

    # Verify all paths are absolute
    assert settings.data_dir.is_absolute()
    assert settings.raw_data_dir.is_absolute()
    assert settings.processed_data_dir.is_absolute()
    assert settings.cache_dir.is_absolute()
    assert settings.exports_dir.is_absolute()


def test_environment_variables_override_env_file(tmp_path, monkeypatch):
    """Test environment variables take precedence over .env file."""
    # Create a temporary .env file
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=from_file\nSEARCH_REGION=Test Region\n")

    # Override with environment variable
    monkeypatch.setenv("GOOGLE_API_KEY", "from_env_override")
    monkeypatch.setenv("SEARCH_REGION", "Override Region")

    from src.config import Settings

    settings = Settings(_env_file=str(env_file))

    # Environment variable should take precedence
    assert settings.google_api_key == "from_env_override"
    assert settings.search_region == "Override Region"


def test_scoring_weights_validation_sum_to_one(monkeypatch):
    """Test that scoring weights must sum to approximately 1.0."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    # Valid weights that sum to 1.0
    settings = Settings(
        population_weight=0.25,
        saturation_weight=0.25,
        quality_gap_weight=0.25,
        geographic_gap_weight=0.25,
    )
    assert settings.population_weight == 0.25

    # Weights that sum to 0.995 (within tolerance) should be valid
    settings2 = Settings(
        population_weight=0.248,
        saturation_weight=0.249,
        quality_gap_weight=0.249,
        geographic_gap_weight=0.249,
    )
    assert settings2.population_weight == 0.248


def test_scoring_weights_validation_invalid_sum(monkeypatch):
    """Test that invalid scoring weights sum raises ValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    # Weights that sum to 2.0 should fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            population_weight=0.5,
            saturation_weight=0.5,
            quality_gap_weight=0.5,
            geographic_gap_weight=0.5,
        )
    assert "weight" in str(exc_info.value).lower()


def test_singleton_behavior(monkeypatch):
    """Test that settings singleton returns the same instance."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import settings as settings1
    from src.config import settings as settings2

    # Both imports should return the same instance
    assert settings1 is settings2
    assert id(settings1) == id(settings2)


def test_empty_api_key_raises_error(monkeypatch):
    """Test that empty Google API key raises ValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    from src.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "google_api_key" in str(exc_info.value).lower()


def test_short_api_key_raises_error(monkeypatch):
    """Test that very short API key raises ValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "short")

    from src.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    # Should fail validation for being too short
    assert "google_api_key" in str(exc_info.value).lower()


def test_negative_rate_limit_delay_raises_error(monkeypatch):
    """Test that negative rate limit delay raises ValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(rate_limit_delay=-0.5)

    assert "rate_limit_delay" in str(exc_info.value).lower()


def test_zero_rate_limit_delay_raises_error(monkeypatch):
    """Test that zero rate limit delay raises ValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(rate_limit_delay=0)

    assert "rate_limit_delay" in str(exc_info.value).lower()


def test_optional_llm_keys_are_optional(monkeypatch):
    """Test that LLM API keys are optional."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")
    # Don't set OPENAI_API_KEY or ANTHROPIC_API_KEY

    from src.config import Settings

    settings = Settings()

    # Should not raise error, keys should be None
    assert settings.openai_api_key is None
    assert settings.anthropic_api_key is None


def test_invalid_rating_bounds(monkeypatch):
    """Test that invalid rating bounds raise ValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    # min_rating > max_rating should fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(min_rating=5.0, max_rating=0.0)

    assert "rating" in str(exc_info.value).lower()


def test_negative_cache_ttl_raises_error(monkeypatch):
    """Test that negative cache TTL raises ValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(cache_ttl_days=-1)

    assert "cache_ttl_days" in str(exc_info.value).lower()


def test_settings_are_immutable(monkeypatch):
    """Test that settings cannot be modified after initialization."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    settings = Settings()

    # Attempt to modify a setting should raise an error
    with pytest.raises((ValidationError, AttributeError)):
        settings.google_api_key = "new_key"


def test_llm_provider_values(monkeypatch):
    """Test that LLM provider accepts valid values."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    # Test valid providers
    settings_openai = Settings(llm_provider="openai")
    assert settings_openai.llm_provider == "openai"

    settings_anthropic = Settings(llm_provider="anthropic")
    assert settings_anthropic.llm_provider == "anthropic"


def test_weights_within_valid_range(monkeypatch):
    """Test that weights must be between 0 and 1."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_123456789")

    from src.config import Settings

    # Negative weight should fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(population_weight=-0.1)

    assert "weight" in str(exc_info.value).lower()

    # Weight > 1.0 should fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(saturation_weight=1.5)

    assert "weight" in str(exc_info.value).lower()
