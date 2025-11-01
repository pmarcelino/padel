# Story 0.2: Configuration Management

## Overview
**Priority**: P0 (Blocker)  
**Layer**: 0 (Foundation)  
**Dependencies**: None  
**Estimated Effort**: Small (2-4 hours)  
**Status**: Not Started

## Description
Create a centralized configuration management system using environment variables and Pydantic settings. This provides a single source of truth for all application configuration, including API keys, paths, and runtime parameters.

## Business Value
- Secure credential management
- Easy configuration changes without code modifications
- Consistent settings across all components
- Environment-specific configurations (dev/prod)

## Input Contract
- `.env` file with configuration key-value pairs
- Environment variables (optional, can override `.env`)

## Output Contract
A `Settings` singleton object that provides:
- Typed configuration attributes
- Validated values
- Default values for optional settings
- Path objects for file system operations

## API Surface

```python
# src/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys (required)
    google_api_key: str = Field(..., env='GOOGLE_API_KEY')
    
    # Optional LLM API Keys
    openai_api_key: Optional[str] = Field(None, env='OPENAI_API_KEY')
    anthropic_api_key: Optional[str] = Field(None, env='ANTHROPIC_API_KEY')
    llm_provider: str = Field('openai', env='LLM_PROVIDER')  # 'openai' or 'anthropic'
    llm_model: str = Field('gpt-4o-mini', env='LLM_MODEL')
    
    # Paths (auto-computed from project root)
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    cache_dir: Path
    exports_dir: Path
    
    # Data Collection Settings
    search_region: str = Field('Algarve, Portugal', env='SEARCH_REGION')
    cache_enabled: bool = Field(True, env='CACHE_ENABLED')
    cache_ttl_days: int = Field(30, env='CACHE_TTL_DAYS')
    rate_limit_delay: float = Field(0.2, env='RATE_LIMIT_DELAY')
    
    # Analysis Settings
    min_rating: float = Field(0.0, env='MIN_RATING')
    max_rating: float = Field(5.0, env='MAX_RATING')
    
    # Opportunity Scoring Weights (must sum to 1.0)
    population_weight: float = Field(0.2, env='POPULATION_WEIGHT')
    saturation_weight: float = Field(0.3, env='SATURATION_WEIGHT')
    quality_gap_weight: float = Field(0.2, env='QUALITY_GAP_WEIGHT')
    geographic_gap_weight: float = Field(0.3, env='GEOGRAPHIC_GAP_WEIGHT')
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# Singleton instance
settings = Settings()
```

### Usage Example

```python
from src.config import settings

# Access configuration
api_key = settings.google_api_key
data_path = settings.processed_data_dir / "facilities.csv"

# Settings are immutable after initialization
# settings.google_api_key = "new_key"  # This will raise an error
```

## Acceptance Criteria

### Required Features
- [ ] **Settings Class**: Pydantic BaseSettings with all configuration parameters
- [ ] **Environment Loading**: Automatically load from `.env` file with `python-dotenv`
- [ ] **API Key Validation**: 
  - Google API key is required (raises error if missing)
  - LLM API keys are optional
  - Validate key format (non-empty strings)
- [ ] **Path Management**: 
  - Auto-compute all data directory paths from project root
  - Use `pathlib.Path` objects (not strings)
  - Paths are absolute, not relative
- [ ] **Default Values**: Sensible defaults for all optional parameters
- [ ] **Type Safety**: Full type hints for all fields
- [ ] **Immutability**: Settings cannot be modified after initialization
- [ ] **Validation**: 
  - Weights sum to 1.0 (or close enough: 0.99-1.01)
  - Rating bounds are valid (0-5)
  - Rate limit delay > 0

### Testing Requirements
- [ ] Unit test: Load from valid `.env` file
- [ ] Unit test: Missing required key raises error
- [ ] Unit test: Default values are applied
- [ ] Unit test: Path computation is correct
- [ ] Unit test: Environment variables override `.env` values
- [ ] Unit test: Scoring weights validation
- [ ] Unit test: Settings singleton behavior (same instance)

### Documentation
- [ ] Docstrings for `Settings` class
- [ ] Docstring for each configuration field explaining its purpose
- [ ] Comment explaining path computation logic
- [ ] `.env.example` with all available configuration options

## Files to Create

### Production Code
1. **`src/config.py`**
   - `Settings` class with all configuration fields
   - Path initialization logic
   - Validation methods
   - Singleton instance export

2. **`.env.example`**
   - Template with all configuration keys
   - Comments explaining each option
   - Example values (non-sensitive)

### Test Code
3. **`tests/test_config.py`**
   - Test settings loading from `.env`
   - Test missing required keys
   - Test default values
   - Test path computation
   - Test environment variable override
   - Test validation logic
   - Test singleton behavior

### Supporting Files
4. **`tests/fixtures/.env.test`** (optional)
   - Test environment file for unit tests

## Technical Notes

### Path Computation Strategy

**Option 1: Compute in __init__ (Simpler)**
```python
# Auto-compute paths from project root
project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Compute derived paths
    self.data_dir = self.project_root / "data"
    self.raw_data_dir = self.data_dir / "raw"
    self.processed_data_dir = self.data_dir / "processed"
    self.cache_dir = self.data_dir / "cache"
    self.exports_dir = self.data_dir / "exports"
```

**Option 2: Use @computed_field (Pydantic v2, more elegant)**
```python
from pydantic import computed_field

project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

@computed_field
@property
def data_dir(self) -> Path:
    return self.project_root / "data"

@computed_field
@property
def raw_data_dir(self) -> Path:
    return self.data_dir / "raw"

# ... similar for other paths
```

**Recommendation**: Either approach works. Option 1 is simpler for MVP; Option 2 is more Pythonic.

### Environment Variable Precedence
1. System environment variables (highest priority)
2. `.env` file values
3. Default values in Field() (lowest priority)

### Validation Example (Pydantic v2)
```python
from pydantic import field_validator

@field_validator('google_api_key')
def validate_google_api_key(cls, v):
    if not v or len(v) < 10:
        raise ValueError("GOOGLE_API_KEY must be a valid API key")
    return v

@field_validator('geographic_gap_weight')
def validate_weights_sum(cls, v, info):
    """Ensure all weights sum to approximately 1.0"""
    # Note: In Pydantic v2, use info.data to access other field values
    total = (
        info.data.get('population_weight', 0) +
        info.data.get('saturation_weight', 0) +
        info.data.get('quality_gap_weight', 0) +
        v  # geographic_gap_weight
    )
    if not (0.99 <= total <= 1.01):
        raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
    return v
```

## Error Handling Patterns

This section defines standard error handling patterns for the entire application. All stories should follow these conventions:

### Pattern 1: Data Collection Errors
**Context**: Errors during API calls or data fetching  
**Strategy**: Log error and continue processing  
**Rationale**: Don't crash the entire pipeline if one facility fails  
```python
try:
    data = api_call()
except Exception as e:
    logger.warning(f"Failed to fetch data: {e}")
    continue  # Skip this item, continue with others
```

### Pattern 2: Validation Errors
**Context**: Pydantic model validation failures  
**Strategy**: Let errors propagate (don't catch)  
**Rationale**: Indicates a code bug or data model mismatch that needs fixing  
```python
# Don't wrap in try/except - let Pydantic errors propagate
facility = Facility(**data)  # Will raise ValidationError if data is invalid
```

### Pattern 3: API Rate Limit Errors
**Context**: HTTP 429 or rate limit responses  
**Strategy**: Retry with exponential backoff, then log and skip  
**Rationale**: Temporary errors that may succeed on retry  
```python
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        response = api_call()
        break
    except RateLimitError:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            time.sleep(wait_time)
        else:
            logger.error("Max retries exceeded")
            return None
```

### Pattern 4: User Input Errors
**Context**: Invalid command-line arguments or configuration  
**Strategy**: Return user-friendly error message and exit  
**Rationale**: User needs clear guidance to fix the issue  
```python
if not settings.google_api_key:
    print("ERROR: GOOGLE_API_KEY is required. Please set it in .env file.")
    sys.exit(1)
```

## Dependencies

### Python Packages
- `pydantic>=2.3.0` - Data validation and base models
- `pydantic-settings>=2.0.0` - Settings management (required for BaseSettings in Pydantic v2)
- `python-dotenv>=1.0.0` - Load `.env` files

### Internal Dependencies
None (this is a foundation layer component)

## Testing Strategy

### Unit Tests (Isolated)
```python
def test_settings_loads_from_env(tmp_path):
    """Test settings loads correctly from .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=test_key_123456789\n")
    
    settings = Settings(_env_file=str(env_file))
    assert settings.google_api_key == "test_key_123456789"

def test_missing_required_key_raises_error():
    """Test missing GOOGLE_API_KEY raises ValidationError."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, google_api_key=None)

def test_default_values_applied():
    """Test default values are used when not specified."""
    settings = Settings(google_api_key="test_key")
    assert settings.search_region == "Algarve, Portugal"
    assert settings.cache_enabled is True
    assert settings.cache_ttl_days == 30

def test_paths_are_computed_correctly():
    """Test data directory paths are auto-computed."""
    settings = Settings(google_api_key="test_key")
    assert settings.data_dir == settings.project_root / "data"
    assert settings.cache_dir == settings.data_dir / "cache"

def test_environment_variables_override_env_file(monkeypatch, tmp_path):
    """Test environment variables take precedence over .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=from_file\n")
    
    monkeypatch.setenv("GOOGLE_API_KEY", "from_env")
    settings = Settings(_env_file=str(env_file))
    
    assert settings.google_api_key == "from_env"

def test_scoring_weights_validation():
    """Test that scoring weights must sum to 1.0."""
    with pytest.raises(ValidationError):
        Settings(
            google_api_key="test",
            population_weight=0.5,
            saturation_weight=0.5,
            quality_gap_weight=0.5,
            geographic_gap_weight=0.5  # Sum = 2.0, should fail
        )
```

## Edge Cases to Handle

1. **Missing `.env` file**: Should use defaults and environment variables
2. **Empty API key**: Should raise validation error
3. **Invalid weight sum**: Should raise validation error
4. **Negative values**: Rate limit delay cannot be negative
5. **Path with spaces**: Ensure Path objects handle spaces correctly
6. **Windows paths**: Test path handling on Windows (use pathlib)

## Non-Goals (Out of Scope)

- ❌ Dynamic configuration reloading (settings are immutable after init)
- ❌ Configuration UI or admin panel
- ❌ Remote configuration (only local `.env` files)
- ❌ Encrypted credentials (use OS-level secrets management if needed)

## Success Criteria

- [ ] Settings can be imported and used in any module: `from src.config import settings`
- [ ] Missing Google API key prevents application startup with clear error
- [ ] All tests pass with 100% coverage
- [ ] `.env.example` is complete and documented
- [ ] No hardcoded paths or configuration values elsewhere in codebase

## Related Stories
- **Blocks**: All Layer 1+ stories depend on this
- **Blocked by**: None
- **Related**: Story 0.1 (Models may use settings for validation)

## Questions & Decisions

### Q: Should we use Pydantic v1 or v2?
**A**: Use Pydantic v2 (>=2.3.0) for better performance and modern API.

### Q: Where should the `.env` file live?
**A**: Project root (same level as `src/` and `app/`)

### Q: How to handle missing optional LLM keys?
**A**: Set as `Optional[str]` with `None` default. LLM features gracefully disabled.

### Q: Should paths be created automatically?
**A**: No. Settings only defines paths. Directory creation happens in individual components.

## Implementation Checklist

- [ ] Create `src/config.py` with Settings class
- [ ] Add all required and optional fields
- [ ] Implement path computation in `__init__`
- [ ] Add validators for API keys and weights
- [ ] Create singleton instance
- [ ] Write `.env.example` with documentation
- [ ] Write comprehensive unit tests
- [ ] Verify all tests pass
- [ ] Add docstrings to all public APIs
- [ ] Update `.gitignore` to exclude `.env` (but not `.env.example`)

---

**Story Ready**: ✅  
**Assignee**: Unassigned  
**Estimated Completion**: 2-4 hours  
**Actual Completion**: TBD

