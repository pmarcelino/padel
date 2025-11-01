# Story 0.3: Caching Utilities

**Priority**: P0 (Blocker)  
**Dependencies**: None  
**Estimated Effort**: Small  
**Layer**: 0 (Foundation)

---

## Overview

Create a generic caching system for API responses to reduce costs, improve performance, and respect API rate limits. The caching system should be implemented as a Python decorator that can be applied to any function making external API calls.

---

## Business Value

- **Cost Reduction**: Minimize repeated API calls to Google Places API (which costs money)
- **Performance**: Speed up data collection by avoiding redundant network requests
- **Rate Limit Compliance**: Reduce likelihood of hitting API rate limits
- **Development Speed**: Enable faster iteration during development without hitting API repeatedly

---

## Technical Requirements

### Input Contract
- **Function to Cache**: Any Python function that returns serializable data

### Output Contract
- **Cached Function**: Same function with automatic caching behavior
- **Cache Storage**: Persistent file-based cache in `data/cache/` directory
- **TTL Support**: Configurable time-to-live for cached responses

---

## Functional Requirements

### FR-1: Decorator Interface
The system must provide a `@cache_response(ttl_days)` decorator that can be applied to any function:

```python
@cache_response(ttl_days=30)
def expensive_api_call(param1, param2):
    # API call logic
    return result
```

### FR-2: Cache Key Generation
- Generate unique cache keys based on:
  - Function name
  - All positional arguments
  - All keyword arguments
- Use MD5 hash for key generation
- Ensure deterministic key generation for same inputs

### FR-3: File-Based Storage
- Store cached responses as pickle files in `data/cache/`
- Naming convention: `{cache_key}.pkl`
- Automatically create cache directory if it doesn't exist

### FR-4: TTL (Time-To-Live) Management
- Support configurable TTL in days (parameter to decorator)
- Check file modification time to determine cache age
- Automatically invalidate and refresh expired cache entries
- Re-execute function and update cache when expired

### FR-5: Cache Hit/Miss Behavior
- **Cache Hit**: Return cached result immediately (no function execution)
- **Cache Miss**: Execute function, cache result, then return result
- **Cache Expired**: Same as cache miss

---

## Non-Functional Requirements

### NFR-1: Performance
- Cache lookup should be < 10ms
- No significant overhead for cache miss scenario

### NFR-2: Reliability
- Handle pickle serialization errors gracefully
- Handle file system errors (permissions, disk full)
- Never crash the calling function due to cache issues

### NFR-3: Compatibility
- Support Python 3.10+
- Work with any serializable return type (dict, list, objects, primitives)
- Preserve function signature and docstrings (use `@wraps`)

---

## Acceptance Criteria

- [x] `@cache_response(ttl_days)` decorator implemented
- [x] File-based cache in `data/cache/` directory
- [x] Cache key generation from function name and arguments
- [x] TTL expiration logic correctly invalidates old cache
- [x] Cache hit returns cached data without executing function
- [x] Cache miss executes function and stores result
- [x] Expired cache refreshes automatically
- [x] Tests with mock functions demonstrating:
  - [x] Cache hit scenario
  - [x] Cache miss scenario
  - [x] Cache expiration scenario
  - [x] Cache key uniqueness (different args = different keys)
  - [x] Cache key consistency (same args = same key)
- [x] Error handling for pickle failures
- [x] Error handling for file system issues
- [x] Function metadata preserved with `@wraps`

---

## Files to Create

```
src/utils/
├── __init__.py
└── cache.py                    # Main caching implementation

tests/test_utils/
├── __init__.py
└── test_cache.py               # Unit tests
```

---

## API Specification

### Module: `src/utils/cache.py`

#### Function: `cache_response(ttl_days: int) -> Callable`
**Description**: Decorator factory that creates a caching decorator with specified TTL.

**Parameters**:
- `ttl_days` (int): Time-to-live in days for cached responses

**Returns**: Decorator function

**Example Usage**:
```python
from src.utils.cache import cache_response

@cache_response(ttl_days=30)
def get_place_details(place_id: str) -> dict:
    # Expensive API call
    return api_response
```

#### Function: `_generate_cache_key(*args, **kwargs) -> str`
**Description**: Internal function to generate MD5 hash from function arguments.

**Parameters**:
- `*args`: Positional arguments
- `**kwargs`: Keyword arguments

**Returns**: MD5 hash string (32 characters)

---

## Implementation Guidance

### Cache Key Generation Algorithm
1. Combine function name with all arguments into a string
2. Encode string as UTF-8 bytes
3. Calculate MD5 hash
4. Return hexdigest

### TTL Check Algorithm
1. Check if cache file exists
2. If exists, load pickle file
3. Extract stored timestamp from cache metadata
4. Calculate age: `current_time - stored_timestamp`
5. If age < TTL, return cached data
6. If age >= TTL, invalidate and re-execute

### Cache Storage Format
- Use Python's `pickle` module for serialization
- Binary mode file operations
- **Store metadata with data** (not rely on file mtime):
  ```python
  cache_data = {
      'created_at': datetime.now(),
      'ttl_days': ttl_days,
      'data': result
  }
  ```
- Atomic writes (write to temp file, then rename)
- Note: Storing timestamp inside pickle is more reliable than using file modification time, which can change if files are copied/moved

---

## Testing Strategy

### Unit Tests Required

#### Test 1: Cache Miss - First Call
- Execute decorated function
- Verify function executes (e.g., via mock)
- Verify result is returned
- Verify cache file is created

#### Test 2: Cache Hit - Second Call
- Execute decorated function twice with same args
- Verify function only executes once
- Verify cached result returned on second call

#### Test 3: Cache Key Uniqueness
- Execute decorated function with different args
- Verify different cache files created
- Verify correct results returned for each

#### Test 4: Cache Key Consistency
- Execute decorated function multiple times with same args
- Verify same cache key generated each time

#### Test 5: TTL Expiration
- Create cached result with old timestamp
- Execute decorated function
- Verify function re-executes (cache expired)
- Verify new cache file created

#### Test 6: TTL Not Expired
- Create cached result with recent timestamp
- Execute decorated function
- Verify function does NOT execute (cache valid)
- Verify cached result returned

#### Test 7: Error Handling - Pickle Failure
- Mock pickle to raise exception
- Verify function still executes and returns result
- Verify no exception propagates to caller

#### Test 8: Error Handling - File System Failure
- Mock file operations to raise exception
- Verify function still executes and returns result
- Verify no exception propagates to caller

#### Test 9: Cache Metadata Storage
- Execute decorated function and create cache
- Load cache file and verify metadata structure
- Verify 'created_at', 'ttl_days', and 'data' keys exist
- Verify timestamp is stored correctly

---

## Edge Cases to Handle

1. **Cache directory doesn't exist**: Create it automatically
2. **Corrupted cache file**: Delete and re-execute function
3. **Unpicklable return value**: Log warning, don't cache, return result
4. **Disk full**: Log error, execute function without caching
5. **Concurrent access**: Use file locking or accept race condition
6. **Function with unhashable arguments**: Convert to string representation

---

## Integration Points

This story has no dependencies but will be used by:
- **Story 1.1** (Google Places Collector): Cache API responses
- **Story 1.2** (Review Collector): Cache review fetches
- **Story 1.3** (Google Trends Collector): Cache trends data

---

## Definition of Done

- [x] All code implemented and follows project style guide
- [x] All unit tests pass
- [x] Code coverage ≥ 90% for cache module (achieved 95%)
- [x] Docstrings complete for all public functions
- [x] Type hints added for all functions
- [x] Manual testing confirms cache works with real API calls
- [x] Cache directory auto-created on first use
- [x] No performance regression (< 10ms overhead - achieved 0.30ms)
- [ ] Code reviewed and approved
- [ ] Documentation updated

---

## Future Enhancements (Out of Scope)

- Cache invalidation API (manual clear)
- Cache statistics (hit rate, size)
- Compression for large cached objects
- Database-based cache (SQLite)
- Distributed cache (Redis)
- Cache warming strategies

