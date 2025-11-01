# Story 1.2: Review Collector

## Overview

**Priority**: P1 (Nice to Have)  
**Dependencies**: Story 0.1 (Data Models), Story 0.2 (Configuration), Story 0.3 (Caching)  
**Estimated Effort**: Small  
**Layer**: Layer 1 (Data Collection)

## Description

Fetch Google reviews for padel facilities using the Google Places API. This collector will retrieve review texts that can later be analyzed by the LLM-based indoor/outdoor analyzer to enrich facility data.

## Business Value

- Enables enrichment of facility data with user-generated content
- Provides raw material for LLM analysis to determine indoor/outdoor status
- Captures customer sentiment and facility characteristics
- Supports future feature expansions (e.g., sentiment analysis, feature extraction)

## Input Contract

### Function Signature
```python
def get_reviews(place_id: str, max_reviews: int = 20) -> List[str]
```

### Parameters
- **place_id** (str, required): Google Place ID for the facility
- **max_reviews** (int, optional): Maximum number of reviews to fetch (default: 20)

### Constraints
- `place_id` must be a valid Google Place ID
- `max_reviews` must be a positive integer
- Google Places API may return fewer reviews than requested

## Output Contract

### Return Type
`List[str]` - List of review text strings

### Output Format
- Returns only the text content of reviews (no metadata)
- Reviews are returned in order as provided by Google API
- Empty list if no reviews are available
- Empty list if API call fails

### Example Output
```python
[
    "Great padel club with excellent outdoor courts. The facilities are well maintained.",
    "Indoor courts are perfect for rainy days. Highly recommended!",
    "Nice place but can get crowded on weekends. Both indoor and outdoor options available."
]
```

## API Surface

```python
class ReviewCollector:
    """Collect Google reviews for facilities."""
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize the review collector.
        
        Args:
            api_key: Google Places API key
        """
        pass
    
    def get_reviews(self, place_id: str, max_reviews: int = 20) -> List[str]:
        """
        Fetch reviews for a place.
        
        Args:
            place_id: Google Place ID
            max_reviews: Maximum number of reviews to fetch
            
        Returns:
            List of review texts
        """
        pass
```

## Acceptance Criteria

### Functional Requirements
- [ ] Fetch reviews via Google Places API (Place Details endpoint)
- [ ] Extract only text content from review objects (ignore ratings, dates, etc.)
- [ ] Handle missing reviews gracefully (return empty list)
- [ ] Handle API errors gracefully (log error, return empty list)
- [ ] Limit results to `max_reviews` parameter
- [ ] Filter out empty review texts

### Non-Functional Requirements
- [ ] Rate limiting (0.2s delay between requests)
- [ ] **HTTP 429 handling with exponential backoff:**
  - [ ] Detect rate limit errors (HTTP 429)
  - [ ] Implement exponential backoff (1s, 2s, 4s)
  - [ ] Maximum retry count: 3 attempts
  - [ ] Log rate limiting events
- [ ] Respect Google API quotas
- [ ] Log warnings for API failures
- [ ] Execution time < 1 second per facility (excluding retries)

### Testing Requirements
- [ ] Unit tests with mocked API responses
- [ ] Test case: Facility with reviews (returns list of texts)
- [ ] Test case: Facility without reviews (returns empty list)
- [ ] Test case: API error (returns empty list, logs error)
- [ ] Test case: Reviews with empty text fields (filters them out)
- [ ] Test case: max_reviews parameter limits results
- [ ] Test coverage: >90%

## Files to Create

### Implementation
- `src/collectors/review_collector.py` - Main ReviewCollector class

### Tests
- `tests/test_collectors/test_review_collector.py` - Unit tests with mocked API

## Technical Specifications

### Dependencies
```python
import googlemaps
from typing import List
import time
```

### Google Places API Fields
Request the following field from the Place Details API:
- `reviews` - Array of review objects

### Review Object Structure (from Google API)
```json
{
  "reviews": [
    {
      "author_name": "User Name",
      "rating": 5,
      "text": "Review text content here",
      "time": 1234567890
    }
  ]
}
```

### Rate Limiting Strategy
- Add 0.2-second delay after each API call
- Use `time.sleep(self.rate_limit_delay)` from config
- **Handle HTTP 429 (Rate Limit Exceeded) responses:**
  - Implement exponential backoff (1s, 2s, 4s)
  - Maximum 3 retry attempts
  - Log rate limiting events for monitoring

### Error Handling
Follow error handling patterns defined in Story 0.2:
- **API Rate Limit Errors** (Pattern 3): Retry with exponential backoff (max 3 attempts)
- **Data Collection Errors** (Pattern 1): Catch all exceptions during API calls
- Log error with facility place_id
- Return empty list on any error
- Do not raise exceptions (fail gracefully)

## Integration Points

### Upstream Dependencies
- **Story 0.2**: Uses `Settings.google_api_key` for API authentication
- **Story 0.2**: Uses `Settings.rate_limit_delay` for throttling
- **Story 0.3**: Could optionally use caching (not required for MVP)

### Downstream Consumers
- **Story 2.1**: LLM Indoor/Outdoor Analyzer will consume review texts
- **Story 5.1**: Data Collection CLI will orchestrate review fetching

## Usage Example

```python
from src.collectors.review_collector import ReviewCollector
from src.config import settings

# Initialize collector
collector = ReviewCollector(api_key=settings.google_api_key)

# Fetch reviews for a facility
place_id = "ChIJN1t_tDeuEmsRUsoyG83frY4"
reviews = collector.get_reviews(place_id, max_reviews=20)

# Process reviews
print(f"Fetched {len(reviews)} reviews")
for i, review in enumerate(reviews, 1):
    print(f"{i}. {review[:100]}...")
```

## Testing Strategy

### Unit Tests (Mocked API)

```python
def test_get_reviews_success(mock_googlemaps):
    """Test successful review fetching."""
    # Mock API response with reviews
    # Assert correct extraction of text content
    # Assert max_reviews limit is respected

def test_get_reviews_no_reviews(mock_googlemaps):
    """Test facility without reviews."""
    # Mock API response with empty reviews array
    # Assert returns empty list

def test_get_reviews_api_error(mock_googlemaps):
    """Test API error handling."""
    # Mock API exception
    # Assert returns empty list
    # Assert error is logged

def test_get_reviews_filters_empty_text(mock_googlemaps):
    """Test filtering of empty review texts."""
    # Mock API response with some empty text fields
    # Assert only non-empty texts are returned
```

### Manual Testing Checklist
- [ ] Test with real Google API key
- [ ] Verify reviews match Google Maps website
- [ ] Check rate limiting works (no quota errors)
- [ ] Verify error handling with invalid place_id
- [ ] Test with facility that has 100+ reviews (respects max_reviews)

## Performance Considerations

- **API Call Time**: ~0.5-1.0 seconds per facility
- **Rate Limiting**: 0.2 seconds delay between calls
- **Throughput**: ~3-5 facilities per second
- **Cost**: 1 Place Details request = 1 API call per facility

## Future Enhancements (Out of Scope)

- Cache reviews to reduce API calls
- Fetch review metadata (ratings, dates, author)
- Support pagination for facilities with 100+ reviews
- Filter reviews by language
- Filter reviews by recency (last N months)
- Sentiment analysis integration

## Definition of Done

- [ ] Code implemented and follows style guide
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Code coverage >90%
- [ ] Code reviewed and approved
- [ ] Documentation/docstrings complete
- [ ] Manual testing completed
- [ ] No linter errors
- [ ] Integration with Story 2.1 verified

## Notes

- Google Places API returns a maximum of 5 reviews by default
- For more reviews, would need to use the new Places API (Next Gen) which supports up to 50 reviews
- Current implementation uses the standard Places API for simplicity
- Reviews are in English and Portuguese (Algarve region)

