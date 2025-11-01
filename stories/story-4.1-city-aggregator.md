# Story 4.1: City Aggregator

## Overview
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1 (Data Models)  
**Estimated Effort**: Medium  
**Layer**: 4 (Analysis)

## Description
Aggregate facility data by city to compute city-level statistics. This component processes a list of facilities and groups them by city, calculating key metrics like average ratings, total reviews, geographic centers, and facilities per capita. The output provides the foundation for opportunity scoring and city-level analysis.

## Contracts

### Input Contract
- `facilities: List[Facility]` - List of cleaned and deduplicated facility objects

### Output Contract
- `List[CityStats]` - List of city statistics objects, one per unique city

### API Surface
```python
class CityAggregator:
    """Aggregate facility data by city."""
    
    # Algarve city populations (2021 estimates)
    CITY_POPULATIONS: Dict[str, int]
    
    def aggregate(self, facilities: List[Facility]) -> List[CityStats]
```

## Requirements

### City Population Data

**Source**: 2021 Census Data from INE Portugal (Instituto Nacional de Estatística)  
**Update Schedule**: Should be refreshed with new census data (typically every 10 years)  
**Configurability**: Consider moving to configuration file for easier updates

The aggregator must include population data for all 15 Algarve municipalities:

- Albufeira: 42,388
- Aljezur: 5,347
- Castro Marim: 6,747
- Faro: 64,560
- Lagoa: 23,676
- Lagos: 31,049
- Loulé: 72,162
- Monchique: 5,958
- Olhão: 45,396
- Portimão: 59,896
- São Brás de Alportel: 11,381
- Silves: 37,126
- Tavira: 26,167
- Vila do Bispo: 5,717
- Vila Real de Santo António: 19,156

**Note**: Hardcoded for MVP. Future enhancement: Load from external data source or configuration file.

### Aggregation Logic

**For each city, calculate:**

1. **Total Facilities**: Count of all facilities in the city

2. **Rating Statistics**:
   - `avg_rating`: Mean of all facility ratings (ignore null values)
   - `median_rating`: Median of all facility ratings (ignore null values)
   - If no facilities have ratings, both should be `None`

3. **Review Statistics**:
   - `total_reviews`: Sum of all review counts across facilities

4. **Geographic Center**:
   - `center_lat`: Mean latitude of all facilities in the city
   - `center_lng`: Mean longitude of all facilities in the city

5. **Population Data**:
   - `population`: Lookup from `CITY_POPULATIONS` dictionary
   - If city not found in dictionary, set to `None`

6. **Facilities Per Capita**:
   - If population is available: `(total_facilities / population) * 10000`
   - Result is facilities per 10,000 residents
   - If population is `None`, set `facilities_per_capita` to `None`

### Data Handling

- Use pandas for efficient grouping and aggregation
- Handle missing or null rating values gracefully
- Ensure all numeric calculations handle edge cases (division by zero, empty groups)
- Preserve city name formatting from input data

## Acceptance Criteria

- [x] `CityAggregator` class implemented with `CITY_POPULATIONS` constant
- [x] `aggregate()` method accepts `List[Facility]` and returns `List[CityStats]`
- [x] Groups facilities by city correctly
- [x] Calculates total facilities per city
- [x] Calculates average rating (ignoring null values)
- [x] Calculates median rating (ignoring null values)
- [x] Returns `None` for avg/median rating when no ratings exist
- [x] Calculates total review counts by summing all facility reviews
- [x] Calculates geographic center (mean lat/lng)
- [x] Looks up population from `CITY_POPULATIONS` dictionary
- [x] Calculates facilities per capita (per 10,000 residents) when population available
- [x] Sets `facilities_per_capita` to `None` when population unavailable
- [x] Returns one `CityStats` object per unique city
- [x] Handles empty facility list (returns empty list)
- [x] Handles facilities with missing ratings gracefully
- [x] Unit tests cover all aggregation logic
- [x] Test coverage ≥ 90%

## Files to Create

```
src/analyzers/
├── __init__.py            # Package initializer (typically empty)
└── aggregator.py          # CityAggregator class

tests/test_analyzers/
├── __init__.py            # Package initializer (typically empty)
└── test_aggregator.py     # CityAggregator tests
```

**Note**: All `__init__.py` files can be empty unless exports are needed.

## Test Requirements

### Unit Tests (`test_aggregator.py`)

**Basic Functionality:**
- [x] Test aggregation with valid facilities from multiple cities
- [x] Test aggregation with facilities from single city
- [x] Test aggregation with empty facility list
- [x] Test city grouping (facilities correctly grouped by city)

**Rating Calculations:**
- [x] Test average rating calculation with valid ratings
- [x] Test median rating calculation with valid ratings
- [x] Test rating calculation ignores null/None values
- [x] Test returns None for avg/median when no ratings exist
- [x] Test rating calculation with mixed null and valid values

**Count Calculations:**
- [x] Test total facilities count per city
- [x] Test total review count summation
- [x] Test review count with zero reviews

**Geographic Calculations:**
- [x] Test center latitude calculation (mean)
- [x] Test center longitude calculation (mean)
- [x] Test geographic center with single facility
- [x] Test geographic center with multiple facilities

**Population & Per Capita:**
- [x] Test population lookup for known cities
- [x] Test population lookup for unknown cities (returns None)
- [x] Test facilities per capita calculation (correct formula)
- [x] Test facilities per capita when population is None
- [x] Test facilities per capita calculation precision

**Edge Cases:**
- [x] Test with facility having no reviews (review_count=0)
- [x] Test with all facilities having null ratings
- [x] Test with city name not in CITY_POPULATIONS
- [x] Test DataFrame conversion and grouping
- [x] Test with very large numbers (overflow protection)

**Integration:**
- [x] Test output CityStats objects are valid Pydantic models
- [x] Test all returned CityStats have required fields populated
- [x] Test with realistic sample data (10+ facilities, 3+ cities)

## Technical Notes

### Implementation Strategy

1. **Convert to DataFrame**: Use `pd.DataFrame([f.to_dict() for f in facilities])` or `pd.DataFrame([f.model_dump() for f in facilities])` (Pydantic v2)
2. **Group by city**: Use `df.groupby('city')`
3. **Aggregate metrics**: Use pandas aggregation functions (mean, median, sum, count)
4. **Handle nulls**: Use pandas null-safe functions (`isna().all()`, `dropna()`)
5. **Create CityStats**: Instantiate `CityStats` object for each city with calculated values

### Pandas Best Practices

- Use `.mean()` and `.median()` which automatically ignore NaN values
- Check for all-null columns with `.isna().all()` before aggregating
- Use `.sum()` for totals (review counts)
- Use `.groupby().agg()` for efficient multi-metric aggregation

### Error Handling

- Handle empty DataFrames (no facilities)
- Handle missing 'city' field (should not occur if data is cleaned)
- Handle division by zero (when population is 0, though unlikely)
- Validate output CityStats objects

## Example Usage

```python
from src.analyzers.aggregator import CityAggregator
from src.models.facility import Facility

# Sample facilities
facilities = [
    Facility(
        place_id="test1",
        name="Club A",
        address="Address 1",
        city="Albufeira",
        latitude=37.0885,
        longitude=-8.2475,
        rating=4.5,
        review_count=150
    ),
    Facility(
        place_id="test2",
        name="Club B",
        address="Address 2",
        city="Albufeira",
        latitude=37.0900,
        longitude=-8.2500,
        rating=4.2,
        review_count=80
    ),
    Facility(
        place_id="test3",
        name="Club C",
        address="Address 3",
        city="Faro",
        latitude=37.0194,
        longitude=-7.9322,
        rating=4.7,
        review_count=200
    )
]

# Aggregate
aggregator = CityAggregator()
city_stats = aggregator.aggregate(facilities)

# Results:
# - 2 CityStats objects (Albufeira, Faro)
# - Albufeira: 2 facilities, avg_rating=4.35, total_reviews=230
# - Faro: 1 facility, avg_rating=4.7, total_reviews=200
# - Both have facilities_per_capita calculated
```

## Success Criteria

This story is considered complete when:
1. `CityAggregator` class is fully implemented
2. All acceptance criteria are met
3. Test coverage ≥ 90%
4. All tests pass
5. Code follows Python best practices and PEP 8
6. Aggregation logic is efficient (handles 100+ facilities quickly)
7. Output integrates seamlessly with downstream components (Story 4.3: Opportunity Scorer)

## Related Stories

**Dependencies (must be complete first):**
- Story 0.1: Data Models & Validation (provides `Facility` and `CityStats` models)

**Blocks (cannot start until this is complete):**
- Story 4.3: Opportunity Scorer (requires CityStats with calculated metrics)
- Story 5.2: Data Processing CLI (orchestrates aggregation)

**Can develop in parallel with:**
- Story 4.2: Distance Calculator (independent analysis component)
- Story 1.x: Collection stories (if not already complete)
- Story 3.x: Processing stories (if not already complete)

**Related Documentation:**
- See Technical Design Document section 8.1 for detailed implementation
- See Technical Design Document section 5.2 for CityStats model specification

