"""
Unit tests for caching utilities.

Tests the cache_response decorator with various scenarios including:
- Cache hits and misses
- TTL expiration
- Error handling
- Cache key generation
- Metadata storage
"""

import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.utils.cache import cache_response, _generate_cache_key


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_settings(tmp_path):
    """Mock settings with temporary cache directory."""
    with patch("src.utils.cache.settings") as mock_settings:
        mock_settings.cache_dir = tmp_path / "cache"
        yield mock_settings


@pytest.fixture
def call_counter():
    """Create a call counter for tracking function executions."""
    counter = {"count": 0}
    return counter


# ============================================================================
# Test 1: Cache Miss - First Call
# ============================================================================


def test_cache_miss_first_call(mock_settings, call_counter):
    """Test that function executes on first call and result is cached."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    result = expensive_function(5)

    # Verify function executed
    assert call_counter["count"] == 1
    assert result == 10

    # Verify cache file was created
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    assert len(cache_files) == 1

    # Verify cache content
    with open(cache_files[0], "rb") as f:
        cached_data = pickle.load(f)
        assert "created_at" in cached_data
        assert "ttl_days" in cached_data
        assert "data" in cached_data
        assert cached_data["ttl_days"] == 30
        assert cached_data["data"] == 10


# ============================================================================
# Test 2: Cache Hit - Second Call
# ============================================================================


def test_cache_hit_second_call(mock_settings, call_counter):
    """Test that cached result is returned without executing function."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # First call - cache miss
    result1 = expensive_function(5)
    assert call_counter["count"] == 1
    assert result1 == 10

    # Second call - cache hit
    result2 = expensive_function(5)
    assert call_counter["count"] == 1  # Function not executed again
    assert result2 == 10


# ============================================================================
# Test 3: Cache Key Uniqueness
# ============================================================================


def test_cache_key_uniqueness(mock_settings, call_counter):
    """Test that different arguments generate different cache keys."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    result1 = expensive_function(5)
    result2 = expensive_function(10)

    # Both functions should have executed
    assert call_counter["count"] == 2
    assert result1 == 10
    assert result2 == 20

    # Verify two different cache files created
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    assert len(cache_files) == 2


def test_cache_key_uniqueness_with_kwargs(mock_settings, call_counter):
    """Test cache key uniqueness with keyword arguments."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int, multiplier: int = 2) -> int:
        call_counter["count"] += 1
        return x * multiplier

    result1 = expensive_function(5, multiplier=2)
    result2 = expensive_function(5, multiplier=3)

    # Both functions should have executed
    assert call_counter["count"] == 2
    assert result1 == 10
    assert result2 == 15

    # Verify two different cache files created
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    assert len(cache_files) == 2


# ============================================================================
# Test 4: Cache Key Consistency
# ============================================================================


def test_cache_key_consistency(mock_settings, call_counter):
    """Test that same arguments always generate same cache key."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # Call multiple times with same args
    expensive_function(5)
    expensive_function(5)
    expensive_function(5)

    # Function should only execute once
    assert call_counter["count"] == 1

    # Only one cache file should exist
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    assert len(cache_files) == 1


# ============================================================================
# Test 5: TTL Expiration
# ============================================================================


def test_ttl_expiration(mock_settings, call_counter):
    """Test that expired cache triggers re-execution."""

    @cache_response(ttl_days=1)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # First call - cache miss
    result1 = expensive_function(5)
    assert call_counter["count"] == 1
    assert result1 == 10

    # Manually modify cache file to have old timestamp
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    assert len(cache_files) == 1

    with open(cache_files[0], "rb") as f:
        cached_data = pickle.load(f)

    # Set timestamp to 2 days ago (expired for ttl_days=1)
    cached_data["created_at"] = datetime.now() - timedelta(days=2)

    with open(cache_files[0], "wb") as f:
        pickle.dump(cached_data, f)

    # Second call - cache expired, should re-execute
    result2 = expensive_function(5)
    assert call_counter["count"] == 2  # Function executed again
    assert result2 == 10


# ============================================================================
# Test 6: TTL Not Expired
# ============================================================================


def test_ttl_not_expired(mock_settings, call_counter):
    """Test that valid cache is used without re-execution."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # First call - cache miss
    result1 = expensive_function(5)
    assert call_counter["count"] == 1

    # Manually modify cache file to have recent timestamp
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    with open(cache_files[0], "rb") as f:
        cached_data = pickle.load(f)

    # Set timestamp to 1 day ago (not expired for ttl_days=30)
    cached_data["created_at"] = datetime.now() - timedelta(days=1)

    with open(cache_files[0], "wb") as f:
        pickle.dump(cached_data, f)

    # Second call - cache still valid
    result2 = expensive_function(5)
    assert call_counter["count"] == 1  # Function not executed again
    assert result2 == 10


# ============================================================================
# Test 7: Pickle Failure Handling
# ============================================================================


def test_pickle_load_failure(mock_settings, call_counter):
    """Test graceful handling of pickle load failures."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # First call to create cache
    expensive_function(5)
    assert call_counter["count"] == 1

    # Corrupt the cache file
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    with open(cache_files[0], "wb") as f:
        f.write(b"corrupted data")

    # Second call should handle error gracefully and re-execute
    result = expensive_function(5)
    assert call_counter["count"] == 2  # Function executed again
    assert result == 10


def test_pickle_dump_failure(mock_settings, call_counter):
    """Test graceful handling of pickle dump failures."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # Mock pickle.dump to raise exception
    with patch("src.utils.cache.pickle.dump", side_effect=Exception("Pickle error")):
        result = expensive_function(5)

    # Function should still execute and return result
    assert call_counter["count"] == 1
    assert result == 10


# ============================================================================
# Test 8: File System Failure Handling
# ============================================================================


def test_file_system_read_failure(mock_settings, call_counter):
    """Test graceful handling of file read failures."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # First call to create cache
    expensive_function(5)
    assert call_counter["count"] == 1

    # Mock file open to raise exception on read
    original_open = open

    def mock_open(*args, **kwargs):
        if "rb" in args or kwargs.get("mode") == "rb":
            raise IOError("Read error")
        return original_open(*args, **kwargs)

    with patch("builtins.open", side_effect=mock_open):
        result = expensive_function(5)

    # Function should execute and return result
    assert call_counter["count"] == 2
    assert result == 10


def test_file_system_write_failure(mock_settings, call_counter):
    """Test graceful handling of file write failures."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    # Mock file open to raise exception on write
    original_open = open

    def mock_open(*args, **kwargs):
        if "wb" in args or kwargs.get("mode") == "wb":
            raise IOError("Write error")
        return original_open(*args, **kwargs)

    with patch("builtins.open", side_effect=mock_open):
        result = expensive_function(5)

    # Function should still execute and return result
    assert call_counter["count"] == 1
    assert result == 10


# ============================================================================
# Test 9: Cache Metadata Storage Validation
# ============================================================================


def test_cache_metadata_structure(mock_settings, call_counter):
    """Test that cache metadata has correct structure."""

    @cache_response(ttl_days=15)
    def expensive_function(x: int) -> int:
        call_counter["count"] += 1
        return x * 2

    expensive_function(5)

    # Load cache file and verify structure
    cache_files = list(mock_settings.cache_dir.glob("*.pkl"))
    assert len(cache_files) == 1

    with open(cache_files[0], "rb") as f:
        cached_data = pickle.load(f)

    # Verify required keys exist
    assert "created_at" in cached_data
    assert "ttl_days" in cached_data
    assert "data" in cached_data

    # Verify correct types and values
    assert isinstance(cached_data["created_at"], datetime)
    assert cached_data["ttl_days"] == 15
    assert cached_data["data"] == 10

    # Verify timestamp is recent (within last minute)
    age = datetime.now() - cached_data["created_at"]
    assert age.total_seconds() < 60


# ============================================================================
# Test 10: Cache Directory Auto-Creation
# ============================================================================


def test_cache_directory_auto_creation(tmp_path, call_counter):
    """Test that cache directory is created automatically if it doesn't exist."""
    cache_dir = tmp_path / "nonexistent" / "cache"

    with patch("src.utils.cache.settings") as mock_settings:
        mock_settings.cache_dir = cache_dir

        # Verify directory doesn't exist
        assert not cache_dir.exists()

        @cache_response(ttl_days=30)
        def expensive_function(x: int) -> int:
            call_counter["count"] += 1
            return x * 2

        result = expensive_function(5)

        # Verify directory was created
        assert cache_dir.exists()
        assert result == 10
        assert call_counter["count"] == 1


# ============================================================================
# Test 11: Function Metadata Preservation
# ============================================================================


def test_function_metadata_preservation():
    """Test that @wraps preserves function metadata."""

    @cache_response(ttl_days=30)
    def expensive_function(x: int) -> int:
        """This is a test function.
        
        Args:
            x: An integer input
            
        Returns:
            The input multiplied by 2
        """
        return x * 2

    # Verify function name preserved
    assert expensive_function.__name__ == "expensive_function"

    # Verify docstring preserved
    assert expensive_function.__doc__ is not None
    assert "This is a test function" in expensive_function.__doc__


# ============================================================================
# Test: _generate_cache_key Function
# ============================================================================


def test_generate_cache_key_deterministic():
    """Test that cache key generation is deterministic."""
    key1 = _generate_cache_key("func_name", 1, 2, kwarg1="a", kwarg2="b")
    key2 = _generate_cache_key("func_name", 1, 2, kwarg1="a", kwarg2="b")

    assert key1 == key2
    assert len(key1) == 32  # MD5 hash is 32 characters


def test_generate_cache_key_different_for_different_inputs():
    """Test that different inputs generate different cache keys."""
    key1 = _generate_cache_key("func_name", 1, 2)
    key2 = _generate_cache_key("func_name", 3, 4)
    key3 = _generate_cache_key("other_func", 1, 2)

    assert key1 != key2
    assert key1 != key3
    assert key2 != key3


def test_generate_cache_key_with_unhashable_args():
    """Test cache key generation with unhashable arguments."""
    # Lists and dicts are unhashable but should be converted to strings
    key1 = _generate_cache_key("func_name", [1, 2, 3], {"a": 1})
    key2 = _generate_cache_key("func_name", [1, 2, 3], {"a": 1})

    # Should generate consistent keys
    assert key1 == key2
    assert len(key1) == 32


# ============================================================================
# Test: Different Data Types
# ============================================================================


def test_cache_with_different_data_types(mock_settings, call_counter):
    """Test caching with different return data types."""

    @cache_response(ttl_days=30)
    def return_dict(x: int) -> dict:
        call_counter["count"] += 1
        return {"value": x, "doubled": x * 2}

    @cache_response(ttl_days=30)
    def return_list(x: int) -> list:
        call_counter["count"] += 1
        return [x, x * 2, x * 3]

    @cache_response(ttl_days=30)
    def return_string(x: int) -> str:
        call_counter["count"] += 1
        return f"Value: {x}"

    # Test dict
    result1 = return_dict(5)
    assert call_counter["count"] == 1
    assert result1 == {"value": 5, "doubled": 10}

    result2 = return_dict(5)
    assert call_counter["count"] == 1  # Cache hit
    assert result2 == {"value": 5, "doubled": 10}

    # Test list
    call_counter["count"] = 0
    result3 = return_list(3)
    assert call_counter["count"] == 1
    assert result3 == [3, 6, 9]

    result4 = return_list(3)
    assert call_counter["count"] == 1  # Cache hit
    assert result4 == [3, 6, 9]

    # Test string
    call_counter["count"] = 0
    result5 = return_string(7)
    assert call_counter["count"] == 1
    assert result5 == "Value: 7"

    result6 = return_string(7)
    assert call_counter["count"] == 1  # Cache hit
    assert result6 == "Value: 7"

