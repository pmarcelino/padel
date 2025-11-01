"""
Caching utilities for API responses.

This module provides a decorator-based caching system for functions that make
expensive API calls or computations. Cached results are stored as pickle files
in the configured cache directory with configurable TTL (time-to-live).

Usage:
    from src.utils.cache import cache_response

    @cache_response(ttl_days=30)
    def expensive_api_call(param1, param2):
        # API call logic
        return result

The decorator will:
- Generate a unique cache key based on function name and arguments
- Check if a valid cached result exists
- Return cached result if valid (not expired)
- Execute function and cache result if cache miss or expired
- Handle all errors gracefully (never prevent function execution)
"""

import hashlib
import logging
import pickle
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

from src.config import settings

# Setup module logger
logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar("T")


def _generate_cache_key(func_name: str, *args: Any, **kwargs: Any) -> str:
    """
    Generate a unique cache key from function name and arguments.

    Creates a deterministic MD5 hash from the function name and all arguments.
    This ensures that the same function called with the same arguments always
    produces the same cache key.

    Args:
        func_name: Name of the function being cached
        *args: Positional arguments passed to the function
        **kwargs: Keyword arguments passed to the function

    Returns:
        MD5 hash string (32 characters) representing the cache key

    Example:
        >>> key = _generate_cache_key("get_data", 123, format="json")
        >>> len(key)
        32
    """
    # Convert all arguments to a string representation
    # Sort kwargs to ensure deterministic ordering
    key_parts = [func_name]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

    # Combine into single string and hash
    key_string = "|".join(key_parts)
    cache_key = hashlib.md5(key_string.encode("utf-8")).hexdigest()

    return cache_key


def cache_response(ttl_days: int) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory for caching function results with TTL.

    Creates a decorator that caches the return value of a function based on its
    arguments. Cached results are stored as pickle files in the configured cache
    directory and expire after the specified TTL.

    The decorator handles all errors gracefully - if any cache operation fails,
    the function will still execute normally and return its result.

    Args:
        ttl_days: Time-to-live in days for cached responses. After this time,
                  cached results are considered expired and will be refreshed.

    Returns:
        Decorator function that adds caching behavior to the wrapped function

    Example:
        @cache_response(ttl_days=30)
        def get_place_details(place_id: str) -> dict:
            # Expensive API call
            return api_response

        # First call executes function and caches result
        result1 = get_place_details("place123")

        # Second call returns cached result (no API call)
        result2 = get_place_details("place123")

    Cache Storage Format:
        Cached data is stored as pickle files with the following structure:
        {
            'created_at': datetime,  # When cache was created
            'ttl_days': int,         # TTL value used
            'data': Any              # The actual cached result
        }
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key from function name and arguments
            cache_key = _generate_cache_key(func.__name__, *args, **kwargs)
            
            # Ensure cache directory is set
            if settings.cache_dir is None:
                logger.warning("Cache directory not configured, executing function without caching")
                return func(*args, **kwargs)
            
            cache_file = settings.cache_dir / f"{cache_key}.pkl"

            # Try to load from cache
            try:
                if cache_file.exists():
                    with open(cache_file, "rb") as f:
                        cached_data = pickle.load(f)

                    # Check if cache is still valid (not expired)
                    created_at = cached_data.get("created_at")
                    cached_ttl = cached_data.get("ttl_days", ttl_days)

                    if created_at and isinstance(created_at, datetime):
                        age = datetime.now() - created_at
                        max_age = timedelta(days=cached_ttl)

                        if age < max_age:
                            # Cache is valid, return cached data
                            logger.debug(
                                f"Cache hit for {func.__name__} (key: {cache_key}, "
                                f"age: {age.days} days)"
                            )
                            return cached_data["data"]
                        else:
                            logger.debug(
                                f"Cache expired for {func.__name__} (key: {cache_key}, "
                                f"age: {age.days} days, ttl: {cached_ttl} days)"
                            )
                    else:
                        logger.warning(
                            f"Invalid cache metadata for {func.__name__} (key: {cache_key})"
                        )

            except Exception as e:
                # Log error but continue to execute function
                logger.warning(
                    f"Error loading cache for {func.__name__} (key: {cache_key}): {e}"
                )

            # Cache miss or expired - execute function
            logger.debug(f"Cache miss for {func.__name__} (key: {cache_key})")
            result = func(*args, **kwargs)

            # Try to cache the result
            try:
                # Ensure cache directory exists
                settings.cache_dir.mkdir(parents=True, exist_ok=True)

                # Prepare cache data with metadata
                cache_data = {
                    "created_at": datetime.now(),
                    "ttl_days": ttl_days,
                    "data": result,
                }

                # Write to cache file atomically
                # (write to temp file, then rename to avoid corruption)
                temp_file = cache_file.with_suffix(".tmp")
                with open(temp_file, "wb") as f:
                    pickle.dump(cache_data, f)

                # Atomic rename
                temp_file.replace(cache_file)

                logger.debug(
                    f"Cached result for {func.__name__} (key: {cache_key}, "
                    f"ttl: {ttl_days} days)"
                )

            except Exception as e:
                # Log error but don't prevent function from returning result
                logger.warning(
                    f"Error caching result for {func.__name__} (key: {cache_key}): {e}"
                )

            return result

        return wrapper

    return decorator

