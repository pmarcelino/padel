# Story 9.1: Fix Zero-Facility Cities in Aggregation

## Overview
**Priority**: P0 (Critical - Bug Fix)  
**Dependencies**: Story 4.1 (City Aggregator)  
**Estimated Effort**: Medium  
**Layer**: 4 (Analysis) - Bugfix

## Problem Statement

Currently, `CityAggregator.aggregate()` only produces `CityStats` for cities that have at least one facility. This is a critical bug because:

```python
# Current behavior
for city_name, city_group in df.groupby('city'):
    # Only loops over cities that HAVE facilities in the dataset
```

**Impact:**
- Cities with zero facilities are completely invisible in the analysis
- Example: If Monchique has 5,958 population but **zero padel facilities**, it never appears
- **These are the biggest opportunities** - high population, zero competition, but they're missing from results
- You only analyze cities that already have facilities, missing greenfield opportunities

## Description

Modify the `CityAggregator` to produce `CityStats` for **all 15 Algarve cities**, regardless of whether they have facilities in the dataset. For zero-facility cities:
- `total_facilities = 0`
- `avg_rating = None` (no facilities to rate)
- `median_rating = None`
- `total_reviews = 0`
- `facilities_per_capita = 0`
- Geographic center must come from city center coordinates (see Story 9.2)

## Contracts

### Input Contract
- `facilities: List[Facility]` - List of cleaned and deduplicated facility objects (may not include all cities)

### Output Contract  
- `List[CityStats]` - **Must include all 15 Algarve cities**, even those with zero facilities

## Requirements

### All Cities Must Appear

The aggregator must produce `CityStats` for all cities in `CITY_POPULATIONS`:

```python
CITY_POPULATIONS = {
    "Albufeira": 42388,
    "Aljezur": 5347,
    "Castro Marim": 6747,
    "Faro": 64560,
    "Lagoa": 23676,
    "Lagos": 31049,
    "Loulé": 72162,
    "Monchique": 5958,
    "Olhão": 45396,
    "Portimão": 59896,
    "São Brás de Alportel": 11381,
    "Silves": 37126,
    "Tavira": 26167,
    "Vila do Bispo": 5717,
    "Vila Real de Santo António": 19156,
}
```

### Zero-Facility City Stats

For cities with no facilities in the dataset:
- `total_facilities = 0`
- `avg_rating = None`
- `median_rating = None`  
- `total_reviews = 0`
- `facilities_per_capita = 0.0` (when population is available)
- `center_lat` and `center_lng` from city center coordinates (Story 9.2 dependency)

### Implementation Strategy

1. Start with all cities from `CITY_POPULATIONS`
2. Aggregate facilities for cities that have them (existing logic)
3. For cities not in the facility dataset:
   - Create `CityStats` with zero/null values
   - Use city center coordinates for geographic center
4. Return complete list of all 15 cities

## Acceptance Criteria

- [ ] `aggregate()` returns exactly 15 `CityStats` objects (one per Algarve city)
- [ ] All cities in `CITY_POPULATIONS` appear in results
- [ ] Cities with facilities have correct aggregated stats (existing behavior preserved)
- [ ] Cities without facilities have:
  - [ ] `total_facilities = 0`
  - [ ] `avg_rating = None`
  - [ ] `median_rating = None`
  - [ ] `total_reviews = 0`
  - [ ] `facilities_per_capita = 0.0`
  - [ ] Valid `center_lat` and `center_lng` from city centers
- [ ] Population data is present for all cities
- [ ] No city is missing from the output
- [ ] Unit tests verify all 15 cities are returned
- [ ] Unit tests verify zero-facility cities have correct stats
- [ ] Integration test with real data confirms all cities present

## Files to Modify

```
src/analyzers/
└── aggregator.py          # CityAggregator.aggregate() method

tests/test_analyzers/
└── test_aggregator.py     # Add tests for zero-facility cities
```

## Test Requirements

### New Unit Tests (`test_aggregator.py`)

**Zero-Facility Cities:**
- [ ] Test that all 15 cities appear when only 1 city has facilities
- [ ] Test that all 15 cities appear when 0 cities have facilities (empty input)
- [ ] Test zero-facility city has `total_facilities=0`
- [ ] Test zero-facility city has `avg_rating=None`
- [ ] Test zero-facility city has `median_rating=None`
- [ ] Test zero-facility city has `total_reviews=0`
- [ ] Test zero-facility city has `facilities_per_capita=0.0`
- [ ] Test zero-facility city has valid center coordinates

**Mixed Scenarios:**
- [ ] Test with 10 facilities across 3 cities - verify all 15 cities in output
- [ ] Test facilities in all 15 cities - verify correct stats for each
- [ ] Test partial coverage (7 cities with facilities) - verify all 15 present

**Regression Tests:**
- [ ] Existing tests still pass (cities with facilities work as before)
- [ ] Test coverage remains ≥ 90%

## Technical Notes

### Implementation Approach

```python
def aggregate(self, facilities: List[Facility]) -> List[CityStats]:
    # Step 1: Aggregate facilities for cities that have them
    facility_stats = {}  # city_name -> stats dict
    if facilities:
        df = pd.DataFrame([f.model_dump() for f in facilities])
        for city_name, city_group in df.groupby('city'):
            # Existing aggregation logic
            facility_stats[city_name] = {...}
    
    # Step 2: Create CityStats for ALL cities
    all_city_stats = []
    for city_name, population in self.CITY_POPULATIONS.items():
        if city_name in facility_stats:
            # City has facilities - use aggregated stats
            stats = CityStats(**facility_stats[city_name])
        else:
            # Zero-facility city - use defaults
            center = self.CITY_CENTERS[city_name]  # From Story 9.2
            stats = CityStats(
                city=city_name,
                total_facilities=0,
                avg_rating=None,
                median_rating=None,
                total_reviews=0,
                center_lat=center['lat'],
                center_lng=center['lng'],
                population=population,
                facilities_per_capita=0.0
            )
        all_city_stats.append(stats)
    
    return all_city_stats
```

### Edge Cases

- Empty facility list → All 15 cities with zero stats
- Facilities in cities not in `CITY_POPULATIONS` → Include them with `population=None`
- All 15 cities have facilities → Existing behavior (no zero-stat cities)

## Success Criteria

This story is considered complete when:
1. All 15 Algarve cities appear in aggregation results
2. Zero-facility cities have correct zero/null values
3. Cities with facilities still work correctly (no regression)
4. All acceptance criteria met
5. Test coverage ≥ 90%
6. All tests pass
7. Integration with Story 9.2 (city center coordinates) works correctly

## Related Stories

**Dependencies:**
- Story 4.1: City Aggregator (original implementation - must refactor)
- Story 9.2: City Center Coordinates (needed for zero-facility city centers)

**Blocks:**
- Story 9.3: Fix Distance Calculation (depends on having all cities in results)
- Story 4.3: Opportunity Scorer (benefits from seeing all cities)

**Enables:**
- Proper identification of greenfield opportunities
- Complete market analysis across all Algarve municipalities
- Accurate opportunity scoring for underserved markets

## Business Impact

**Before Fix:**
- Missing high-opportunity cities with zero facilities
- Incomplete market analysis
- Can't identify greenfield opportunities

**After Fix:**
- All cities visible in analysis
- Proper identification of underserved markets
- Complete opportunity ranking including greenfield locations
- Example: Monchique (5,958 pop, 0 facilities) becomes visible as opportunity

