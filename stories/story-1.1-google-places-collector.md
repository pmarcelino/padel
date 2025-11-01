# Story 1.1: Google Places Collector

**Priority**: P0 (Critical Path)  
**Layer**: 1 (Data Collection)  
**Dependencies**: Story 0.1 (Data Models), Story 0.2 (Configuration), Story 0.3 (Caching)  
**Estimated Effort**: Medium

---

## Description

Collect padel facilities from Google Places API. This collector will search for padel facilities in the Algarve region using the Google Places API with multiple query variations to ensure comprehensive coverage.

---

## Input Contract

- `api_key: str` - Google Places API key
- `region: str` - Geographic region to search (e.g., "Algarve, Portugal")

---

## Output Contract

Returns `List[Facility]` with basic facility information (excluding reviews, which are collected separately in Story 1.2).

Each `Facility` object should contain:
- `place_id`: Google Places unique identifier
- `name`: Facility name
- `address`: Full formatted address
- `city`: Extracted city name (Algarve municipality)
- `latitude`, `longitude`: Geographic coordinates
- `rating`: Average rating (0-5)
- `review_count`: Number of reviews
- `google_url`: Link to Google Maps
- `phone`: Phone number (optional)
- `website`: Website URL (optional)
- `facility_type`: Classification (club, sports_center, other)

---

## API Surface

```python
from src.config import settings

class GooglePlacesCollector:
    """Collects padel facility data from Google Places API."""
    
    def __init__(self, api_key: str, cache_enabled: bool = None) -> None:
        """
        Initialize the collector.
        
        Args:
            api_key: Google Places API key
            cache_enabled: Whether to enable response caching (defaults to settings.cache_enabled)
        """
        self.client = googlemaps.Client(key=api_key)
        self.cache_enabled = cache_enabled if cache_enabled is not None else settings.cache_enabled
        self.rate_limit_delay = settings.rate_limit_delay  # Read from config, not hardcoded
    
    def search_padel_facilities(self, region: str = "Algarve, Portugal") -> List[Facility]:
        """
        Search for padel facilities in a region.
        
        Args:
            region: Geographic region to search
            
        Returns:
            List of Facility objects
        """
        pass
```

---

## Technical Requirements

### Search Strategy

Use multiple query variations to maximize facility discovery:
- `"padel {region}"`
- `"padel court {region}"`
- `"padel club {region}"`
- `"centro de padel {region}"`

### Pagination

- Handle Google Places pagination using `next_page_token`
- Implement required 2-second delay between pagination requests
- Collect all pages until no more results

### Rate Limiting

- Implement configurable delay between individual API requests (use `settings.rate_limit_delay`)
- Read rate limit delay from configuration (Story 0.2), not hardcoded
- Default: 0.2-second delay between individual API requests
- Respect Google API rate limits

### Caching

- Use the caching decorator from Story 0.3
- Cache text search results for 30 days TTL
- Cache place details for 7 days TTL

### City Extraction

Extract city names for Algarve municipalities from addresses:
- Albufeira
- Aljezur
- Castro Marim
- Faro
- Lagoa
- Lagos
- Loulé
- Monchique
- Olhão
- Portimão
- São Brás de Alportel
- Silves
- Tavira
- Vila do Bispo
- Vila Real de Santo António

### Deduplication

- Track `place_id` to avoid duplicate API calls within the same collection run
- Use a set to track seen place IDs across query variations

### Error Handling

Follow error handling patterns defined in Story 0.2:
- **Data Collection Errors** (Pattern 1): Log errors but continue processing remaining facilities
- **API Rate Limit Errors** (Pattern 3): Retry with exponential backoff (max 3 attempts)
- **Validation Errors** (Pattern 2): Let Pydantic errors propagate for invalid facility data
- Skip facilities that cannot be parsed into valid `Facility` objects
- Gracefully handle network issues, invalid responses

---

## Acceptance Criteria

- [x] Search with multiple query variations (at least 4 different queries)
- [x] Pagination handling with proper delays (2s between pages)
- [x] Rate limiting implemented (0.2s delay between requests)
- [x] Caching enabled by default using `@cache_response` decorator
- [x] City extraction for all 15 Algarve municipalities
- [ ] Returns 90%+ of known facilities in the region (requires real API testing)
- [x] Deduplication by `place_id` within single collection run
- [x] Unit tests with mocked API responses
- [x] Integration test with real API (optional, marked with `@pytest.mark.integration`)
- [x] Proper error handling and logging
- [x] Type hints throughout
- [x] Docstrings for all public methods

---

## Files to Create

```
src/collectors/
├── __init__.py                  # Package initializer (typically empty)
└── google_places.py             # Main implementation

tests/test_collectors/
├── __init__.py                  # Package initializer (typically empty)
└── test_google_places.py        # Unit tests
```

**Note**: All `__init__.py` files can be empty unless exports are needed.

---

## Testing Requirements

### Unit Tests (Mocked API)

Test the following with mocked API responses:

1. **Basic Search**
   - Mock API returns sample facilities
   - Verify correct parsing into `Facility` objects

2. **Pagination**
   - Mock multi-page response
   - Verify all pages collected
   - Verify 2-second delay between pages

3. **Deduplication**
   - Mock responses with duplicate `place_id`
   - Verify duplicates are skipped

4. **City Extraction**
   - Test addresses from different Algarve cities
   - Verify correct city extraction

5. **Error Handling**
   - Mock API errors
   - Verify graceful handling

6. **Rate Limiting**
   - Verify 0.2s delay between requests

### Integration Test (Real API - Optional)

- Mark with `@pytest.mark.integration`
- Run actual API call (requires valid API key)
- Verify real facilities are returned
- Verify data quality and completeness

---

## Implementation Notes

### Google Places API Fields

Request the following fields from Place Details API:
- `place_id`
- `name`
- `formatted_address`
- `geometry` (location)
- `rating`
- `user_ratings_total`
- `url`
- `formatted_phone_number`
- `website`
- `types`

### Facility Type Determination

Map Google `types` to internal facility types:
- If `"gym"` or `"health"` in types → `"sports_center"`
- If `"point_of_interest"` in types → `"club"`
- Otherwise → `"other"`

### Performance Expectations

- Full Algarve region collection: < 30 minutes
- Typical facility count: 30-100 facilities
- API calls: ~100-200 (with caching, subsequent runs much faster)

---

## Dependencies

This story depends on the following being completed first:

- **Story 0.1**: `Facility` model must exist and be importable
- **Story 0.2**: `Settings` class must provide `google_api_key` and rate limit configs
- **Story 0.3**: `@cache_response` decorator must be available

---

## Success Criteria

✅ Collector can be instantiated with API key  
✅ Search returns list of valid `Facility` objects  
✅ No duplicate facilities in single run  
✅ Cities correctly extracted for 90%+ of facilities  
✅ Caching reduces API calls on subsequent runs  
✅ Tests pass with 100% coverage for collector logic  
✅ Code is type-safe and well-documented

