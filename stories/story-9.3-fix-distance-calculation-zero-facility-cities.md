# Story 9.3: Fix Distance Calculation for Zero-Facility Cities

## Overview
**Priority**: P0 (Critical - Bug Fix)  
**Dependencies**: Story 4.2 (Distance Calculator), Story 9.1 (Zero-Facility Cities), Story 9.2 (City Centers)  
**Estimated Effort**: Medium  
**Layer**: 4 (Analysis) - Bugfix

## Problem Statement

Currently, `DistanceCalculator.calculate_distance_to_nearest()` fails for zero-facility cities:

```python
city_facilities = [f for f in all_facilities if f.city == city]
if not city_facilities:
    return 0.0  # ❌ Returns 0.0 for cities with no facilities!
```

**Impact:**
- Zero-facility cities get `avg_distance_to_nearest = 0.0`
- This gives them the **worst** geographic gap score (0.0 / 20.0 = 0)
- **Should be the opposite!** Cities far from any facility should score highest
- Example: Monchique with no facilities and 15km from nearest court gets scored as if it has facilities on every corner

**What Should Happen:**
For zero-facility cities, calculate distance from **city center coordinates** to nearest facility in **any other city**. This properly captures: "How far is this city from the nearest padel court anywhere?"

## Description

Fix `DistanceCalculator` to correctly handle zero-facility cities by:
1. Detecting when a city has no facilities
2. Using city center coordinates (from Story 9.2) as the reference point
3. Finding the nearest facility across **all cities** (not just within-city)
4. Calculating distance from city center to that nearest facility

This ensures cities with no facilities get accurate geographic gap scores representing how underserved they are.

## Contracts

### Input Contract (Updated)
- `city_stats: List[CityStats]` - All city statistics (including zero-facility cities from Story 9.1)
- `all_facilities: List[Facility]` - All facilities across all cities

### Output Contract
- `List[CityStats]` - Same list with `avg_distance_to_nearest` correctly calculated
  - For cities **with facilities**: Distance between facilities within the city (existing behavior)
  - For cities **without facilities**: Distance from city center to nearest facility anywhere

### API Surface (Updated)

```python
class DistanceCalculator:
    """Calculate distances between facilities and cities."""
    
    def calculate_distances(
        self, 
        city_stats: List[CityStats], 
        all_facilities: List[Facility]
    ) -> List[CityStats]:
        """
        Calculate average distance to nearest facility for each city.
        
        For cities WITH facilities:
            - Calculate distance from each facility to its nearest neighbor
            - Average across all facilities in the city
        
        For cities WITHOUT facilities:
            - Calculate distance from city center to nearest facility anywhere
            - This represents: "How far do residents need to travel to play?"
        """
        pass
    
    def _calculate_distance_for_city(
        self,
        city_stats: CityStats,
        all_facilities: List[Facility]
    ) -> float:
        """
        Calculate distance for a single city.
        
        Returns:
            Distance in kilometers (0.0 if unable to calculate)
        """
        pass
```

## Requirements

### Zero-Facility City Logic

```python
def _calculate_distance_for_city(self, city_stats: CityStats, all_facilities: List[Facility]) -> float:
    city_facilities = [f for f in all_facilities if f.city == city_stats.city]
    
    if not city_facilities:
        # NEW: Zero-facility city - use city center
        if not all_facilities:
            return 0.0  # No facilities anywhere - can't calculate
        
        # Find nearest facility from city center
        city_center = (city_stats.center_lat, city_stats.center_lng)
        nearest_distance = min(
            self._haversine_distance(
                city_center[0], city_center[1],
                facility.latitude, facility.longitude
            )
            for facility in all_facilities
        )
        return nearest_distance
    
    # Existing logic for cities with facilities
    # ... (calculate distances between facilities within city)
```

### Edge Cases

1. **No facilities anywhere**: `avg_distance_to_nearest = 0.0` (can't calculate, but shouldn't happen in production)
2. **One facility in the entire region**: Zero-facility cities calculate distance to that one facility
3. **City center coordinates missing**: Should not happen (Story 9.2 ensures all cities have centers)
4. **City center equals facility location**: Distance = 0.0 (mathematically correct, though unlikely)

### Validation

- Zero-facility cities should typically have distances > 0 km (unless a facility is at exact city center)
- Zero-facility cities far from any facility (e.g., >20km) should score highest in geographic gap
- Cities with facilities should have distances unchanged (no regression)

## Acceptance Criteria

- [x] Zero-facility cities no longer return `0.0` distance incorrectly
- [x] Zero-facility city distance is calculated from city center coordinates
- [x] Distance is measured to nearest facility **anywhere** (not just within city)
- [x] Cities with facilities use existing logic (no regression)
- [x] `_haversine_distance()` correctly calculates distance from city center to facility (using geodesic)
- [x] Edge case: No facilities anywhere returns `0.0` (graceful degradation)
- [x] Edge case: One facility total - all zero-facility cities calculate distance to it
- [x] Unit tests verify zero-facility city distance calculation
- [x] Unit tests verify city center coordinates are used
- [x] Integration test with realistic data confirms correct distances

## Files to Modify

```
src/analyzers/
└── distance.py            # DistanceCalculator._calculate_distance_for_city()

tests/test_analyzers/
└── test_distance.py       # Add tests for zero-facility cities
```

## Test Requirements

### New Unit Tests (`test_distance.py`)

**Zero-Facility City Tests:**
- [ ] Test zero-facility city gets distance from city center to nearest facility
- [ ] Test zero-facility city distance is > 0 when facilities exist elsewhere
- [ ] Test zero-facility city finds nearest facility across all cities
- [ ] Test city center coordinates are used correctly
- [ ] Test haversine distance calculation with city center as origin

**Edge Cases:**
- [ ] Test zero-facility city when no facilities exist anywhere (returns 0.0)
- [ ] Test zero-facility city when only one facility exists in region
- [ ] Test zero-facility city when nearest facility is very far (>50km)
- [ ] Test zero-facility city when nearest facility is very close (<1km)

**Mixed Scenarios:**
- [ ] Test dataset with 3 cities: 2 with facilities, 1 without
- [ ] Verify city with facilities uses within-city distance (existing behavior)
- [ ] Verify city without facilities uses city-center-to-nearest distance
- [ ] Test all 15 Algarve cities with realistic facility distribution

**Regression Tests:**
- [ ] Existing tests for cities with facilities still pass
- [ ] Distance calculations for facility-rich cities unchanged
- [ ] Test coverage remains ≥ 90%

## Technical Notes

### Haversine Distance Formula

Already implemented in `DistanceCalculator`. Accepts:
- `lat1, lng1`: Origin coordinates (city center for zero-facility cities)
- `lat2, lng2`: Destination coordinates (facility location)
- Returns: Distance in kilometers

### Performance Considerations

- For zero-facility cities, must iterate through all facilities to find nearest
- With ~100-200 facilities total, this is O(n) per zero-facility city
- Expected performance: <1ms per city
- No optimization needed for dataset of this size

### Geographic Gap Scoring Impact

**Before Fix:**
- Zero-facility city: `avg_distance_to_nearest = 0.0`
- Geographic gap weight: `0.0 / 20.0 = 0.0` (worst possible)
- Opportunity score: Artificially low

**After Fix:**
- Zero-facility city 15km from nearest facility: `avg_distance_to_nearest = 15.0`
- Geographic gap weight: `15.0 / 20.0 = 0.75` (high opportunity)
- Opportunity score: Correctly reflects underserved market

## Example Usage

```python
from src.analyzers.distance import DistanceCalculator
from src.analyzers.aggregator import CityAggregator

# Get all city stats (including zero-facility cities)
aggregator = CityAggregator()
city_stats = aggregator.aggregate(facilities)

# Calculate distances
distance_calc = DistanceCalculator()
city_stats_with_distances = distance_calc.calculate_distances(city_stats, facilities)

# Results:
for stats in city_stats_with_distances:
    if stats.total_facilities == 0:
        print(f"{stats.city}: 0 facilities, {stats.avg_distance_to_nearest:.1f}km to nearest")
        # Example: "Monchique: 0 facilities, 15.3km to nearest"
    else:
        print(f"{stats.city}: {stats.total_facilities} facilities, avg {stats.avg_distance_to_nearest:.1f}km between them")
        # Example: "Albufeira: 10 facilities, avg 2.5km between them"
```

## Success Criteria

This story is considered complete when:
1. Zero-facility cities have accurate distance calculations
2. Distances are measured from city centers to nearest facility
3. Cities with facilities still work correctly (no regression)
4. All acceptance criteria met
5. Test coverage ≥ 90%
6. All tests pass
7. Geographic gap scores make intuitive sense for zero-facility cities

## Related Stories

**Dependencies:**
- Story 4.2: Distance Calculator (original implementation - must refactor)
- Story 9.1: Fix Zero-Facility Cities (creates CityStats for zero-facility cities)
- Story 9.2: City Center Coordinates (provides city center coordinates)

**Enables:**
- Story 4.3: Opportunity Scorer (benefits from accurate geographic gap weights)
- Story 9.4: Step-Based Geographic Gap (improved geographic gap scoring)

**Impacts:**
- Opportunity scores will change for zero-facility cities (expected)
- Cities like Monchique will now show as high-opportunity (correct behavior)
- Dashboard rankings will update to reflect true geographic gaps

## Business Impact

**Before Fix:**
- Zero-facility cities scored as if saturated with facilities (wrong)
- Missed identifying underserved markets
- Geographic gap analysis incomplete

**After Fix:**
- Zero-facility cities correctly identified as high-opportunity
- Accurate "distance to nearest facility" for all cities
- Proper identification of geographic gaps and underserved markets
- Example: Monchique (0 facilities, 15km from nearest) becomes visible as opportunity

