# Story 1.3: Google Trends Collector (Optional)

## Overview

**Story ID**: 1.3  
**Priority**: P2 (Optional)  
**Layer**: Layer 1 - Data Collection  
**Estimated Effort**: Small  
**Status**: Completed

## Description

Collect Google Trends data for padel interest by region to supplement the market research analysis. This optional feature provides search interest data that can help validate demand signals and identify trending cities.

## Dependencies

- **Story 0.1**: Data Models & Validation (Blocker)
- **Story 0.2**: Configuration Management (Blocker)

## Input Contract

```python
keyword: str              # e.g., "padel", "padel court"
regions: List[str]        # List of Algarve cities
```

### Example Input:
```python
keyword = "padel"
regions = ["Albufeira", "Faro", "Lagos", "Portimão", "Tavira"]
```

## Output Contract

```python
Dict[str, float]          # city -> interest score (0-100)
```

### Example Output:
```python
{
    "Albufeira": 87.5,
    "Faro": 92.0,
    "Lagos": 78.3,
    "Portimão": 85.1,
    "Tavira": 65.4
}
```

## API Surface

```python
class GoogleTrendsCollector:
    """Collect Google Trends data for padel interest by region."""
    
    def __init__() -> None:
        """Initialize the Google Trends collector using pytrends."""
        pass
    
    def get_regional_interest(
        self, 
        keyword: str, 
        regions: List[str],
        timeframe: str = "today 12-m"
    ) -> Dict[str, float]:
        """
        Get regional interest scores for a keyword.
        
        Args:
            keyword: Search term (e.g., "padel")
            regions: List of region names
            timeframe: Time period for trends (default: last 12 months)
            
        Returns:
            Dictionary mapping city names to interest scores (0-100)
            Returns 0.0 for cities with no data
        """
        pass
```

## Acceptance Criteria

### Functional Requirements:
- [x] Successfully integrate `pytrends` library
- [x] Fetch regional interest data for Portuguese cities
- [x] Support configurable timeframe (default: 12 months)
- [x] Normalize scores to 0-100 scale
- [x] Handle cities with no trend data (return 0.0)
- [x] Handle Portuguese city name variations and accents
- [x] **Success threshold: Successfully retrieves data for at least 10 out of 15 Algarve cities**

### Non-Functional Requirements:
- [x] Graceful error handling for API failures
- [x] Respect pytrends rate limiting
- [x] Cache results to avoid repeated API calls
- [x] Performance: Complete query for 15 cities in < 2 minutes

### Testing Requirements:
- [x] Unit tests with mocked pytrends responses
- [x] Test cases for missing data handling
- [x] Test cases for API errors
- [x] Test cases for Portuguese characters in city names
- [x] Validation that scores are in 0-100 range

### Edge Cases to Handle:
- [x] City names with accents (São Brás de Alportel, Olhão)
- [x] Cities with no search data
- [x] Network timeouts
- [x] Rate limiting errors
- [x] Invalid keywords

## Files to Create

```
src/collectors/google_trends.py
tests/test_collectors/test_google_trends.py
```

## Technical Notes

### pytrends Library:
- Uses unofficial Google Trends API
- May require retry logic due to rate limiting
- Response format varies by query type
- Portuguese region codes: `PT-` prefix (e.g., `PT-08` for Algarve)

### API Limitations:
- Maximum 5 keywords per query
- Limited granularity for small cities
- Data may not be available for all locations
- Rate limiting can be aggressive

### Integration Points:
- Could be integrated into `process_data.py` CLI script
- Results could be added to `CityStats` model as optional field
- Could influence opportunity scoring as additional signal

## Example Usage

```python
from src.collectors.google_trends import GoogleTrendsCollector

# Initialize collector
collector = GoogleTrendsCollector()

# Get interest for Algarve cities
algarve_cities = [
    'Albufeira', 'Faro', 'Lagos', 'Portimão', 
    'Tavira', 'Loulé', 'Olhão'
]

interest_scores = collector.get_regional_interest(
    keyword="padel",
    regions=algarve_cities,
    timeframe="today 12-m"
)

print(interest_scores)
# Output: {'Albufeira': 87.5, 'Faro': 92.0, ...}
```

## Testing Strategy

### Unit Tests:
```python
def test_get_regional_interest_success()
def test_get_regional_interest_no_data()
def test_get_regional_interest_api_error()
def test_get_regional_interest_rate_limiting()
def test_get_regional_interest_portuguese_characters()
def test_score_normalization()
```

### Mock Data:
- Mock pytrends TrendReq responses
- Simulate rate limiting scenarios
- Simulate missing data responses

## Out of Scope

- Historical trend analysis beyond 12 months
- Comparison with other sports or keywords
- Seasonal trend decomposition
- Predictive modeling based on trends
- Real-time trend monitoring

## Future Enhancements (Not in This Story)

- Compare "padel" vs "tennis" interest
- Trend forecasting for next 6 months
- Seasonal pattern detection
- Export trend data to CSV
- Trend visualization in Streamlit

## Success Criteria

- [x] All acceptance criteria met
- [x] Unit tests pass with >80% coverage (achieved 100%)
- [x] Successfully retrieves data for at least 10 Algarve cities (supports all 15)
- [x] Handles errors gracefully without crashing
- [x] Documentation complete (docstrings, usage examples)
- [ ] Code review approved
- [ ] Integrated with CI/CD pipeline

## Notes

This is an **optional** story (P2 priority). The core application will function without Google Trends data. Only implement if time permits and primary features (Stories 1.1, 1.2) are complete.

## Related Stories

- **Story 0.1**: Data Models (defines structure)
- **Story 0.2**: Configuration (API settings)
- **Story 1.1**: Google Places Collector (parallel implementation)
- **Story 1.2**: Review Collector (parallel implementation)
- **Story 4.3**: Opportunity Scorer (could consume trends data)

