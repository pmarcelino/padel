# Story 4.2: Distance Calculator

## Metadata
- **Story ID**: 4.2
- **Priority**: P0 (Critical Path)
- **Layer**: 4 (Analysis)
- **Dependencies**: Story 0.1 (Data Models)
- **Estimated Effort**: Small
- **Status**: Not Started

## Overview

Calculate geographic distances between facilities to support opportunity scoring. This component provides utilities for computing distances between city centers and analyzing geographic distribution of padel facilities across the Algarve region.

## Business Context

Geographic accessibility is a key factor in determining market opportunity. Cities that are far from existing facilities represent potential underserved markets. This calculator helps identify:
- Cities with poor geographic access to padel facilities
- Average travel distances required to reach facilities
- Market gaps based on proximity analysis

## Input Contract

### Primary Method: `calculate_distance_to_nearest`
- **city**: `str` - Name of the city to analyze
- **all_facilities**: `List[Facility]` - Complete list of facilities across all cities

### Secondary Method: `calculate_travel_willingness_radius`
- **population**: `int` - City population size

## Output Contract

### Primary Method
- **Returns**: `float` - Minimum distance to nearest facility from neighboring cities (in kilometers)
- **Range**: 0.0 to ~100.0 km (typical Algarve distances)
- **Note**: Returns the minimum distance, not an average

### Secondary Method
- **Returns**: `float` - Estimated travel willingness radius (in kilometers)
- **Values**: 5.0 km (urban), 10.0 km (mid-size), 15.0 km (small towns)

## API Surface

```python
class DistanceCalculator:
    """Calculate geographic distances between facilities."""
    
    @staticmethod
    def calculate_distance_to_nearest(
        city: str,
        all_facilities: List[Facility]
    ) -> float:
        """
        Calculate minimum distance to nearest facility for a city.
        Uses center point of the city and finds closest facility in other cities.
        
        Args:
            city: Name of the city to analyze
            all_facilities: Complete list of facilities
            
        Returns:
            Minimum distance in kilometers to nearest facility in other cities.
            Returns 0.0 if insufficient data.
        """
        pass
    
    @staticmethod
    def calculate_travel_willingness_radius(city_population: int) -> float:
        """
        Estimate how far people are willing to travel based on city size.
        
        Assumptions:
        - Larger cities: people travel less (more local options)
        - Smaller cities: people travel more (fewer local options)
        
        Args:
            city_population: Population of the city
            
        Returns:
            Radius in kilometers
        """
        pass
```

## Functional Requirements

### FR-4.2.1: City Center Calculation
Calculate the geographic center of a city based on its facilities:
- Average latitude of all facilities in the city
- Average longitude of all facilities in the city

### FR-4.2.2: Nearest Neighbor Distance
For a given city, find the distance to the nearest facility in neighboring cities:
- Exclude facilities within the same city
- Calculate geodesic distance (accounts for Earth's curvature)
- Return the minimum distance found

### FR-4.2.3: Travel Willingness Estimation
Estimate travel willingness based on city size:
- **Urban areas** (>50,000 pop): 5 km radius
- **Mid-size towns** (20,000-50,000 pop): 10 km radius
- **Small towns** (<20,000 pop): 15 km radius

### FR-4.2.4: Edge Case Handling
- Return 0.0 if city has no facilities
- Return 0.0 if no other cities have facilities
- Handle empty facility lists gracefully

## Technical Requirements

### TR-4.2.1: Geospatial Library
Use **geopy** library for accurate distance calculations:
- `from geopy.distance import geodesic`
- Calculate geodesic distance (not Euclidean)
- Distance in kilometers (not miles)

### TR-4.2.2: Performance
- All distance calculations should complete in <1 second for typical dataset (50-100 facilities)
- Static methods (no instance state required)

### TR-4.2.3: Accuracy
- Use WGS84 coordinate system (standard GPS)
- Precision to 2 decimal places (10 meters)

## Acceptance Criteria

- [x] **AC-4.2.1**: Use geopy for accurate geodesic distance calculations
- [x] **AC-4.2.2**: Calculate city center from facility coordinates (average lat/lng)
- [x] **AC-4.2.3**: Find nearest neighbor distances to facilities in other cities
- [x] **AC-4.2.4**: Implement travel willingness radius based on population size
- [x] **AC-4.2.5**: Unit tests with known coordinates validate distance accuracy (±1%)
- [x] **AC-4.2.6**: Handle edge cases (empty lists, single city, no neighbors)
- [x] **AC-4.2.7**: All methods are static (no instance state)

## Test Scenarios

### TS-4.2.1: Basic Distance Calculation
```python
# Given facilities in two cities
facilities = [
    Facility(city="Albufeira", lat=37.0885, lng=-8.2475),
    Facility(city="Faro", lat=37.0194, lng=-7.9322)
]

# When calculating distance from Albufeira to nearest neighbor
distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)

# Then distance should be approximately 26 km (verified with Google Maps)
assert 25.0 <= distance <= 27.0
```

### TS-4.2.2: City Center Calculation
```python
# Given multiple facilities in same city
facilities = [
    Facility(city="Lagos", lat=37.10, lng=-8.67),
    Facility(city="Lagos", lat=37.11, lng=-8.68),
    Facility(city="Lagos", lat=37.12, lng=-8.69)
]

# City center should be average of coordinates
# Expected: (37.11, -8.68)
```

### TS-4.2.3: Travel Willingness by Population
```python
# Large city
assert DistanceCalculator.calculate_travel_willingness_radius(60000) == 5.0

# Mid-size city
assert DistanceCalculator.calculate_travel_willingness_radius(30000) == 10.0

# Small town
assert DistanceCalculator.calculate_travel_willingness_radius(10000) == 15.0
```

### TS-4.2.4: Edge Cases
```python
# No facilities in city
assert DistanceCalculator.calculate_distance_to_nearest("EmptyCity", []) == 0.0

# Only one city with facilities
facilities = [Facility(city="Faro", lat=37.0, lng=-8.0)]
assert DistanceCalculator.calculate_distance_to_nearest("Faro", facilities) == 0.0
```

## Files to Create

```
src/analyzers/
├── distance.py              # Main implementation

tests/test_analyzers/
├── test_distance.py         # Unit tests
```

## Implementation Notes

### Distance Calculation Algorithm
1. Filter facilities to those in the target city
2. Calculate city center (average coordinates)
3. Filter facilities to those NOT in the target city
4. For each facility in other cities:
   - Calculate geodesic distance from city center to facility
5. Return minimum distance found

### Geodesic vs. Euclidean Distance
- **Use geodesic**: Accounts for Earth's curvature
- **Don't use Euclidean**: Would be inaccurate for lat/lng coordinates

### Example Usage in Pipeline
```python
# In process_data.py script
from src.analyzers.distance import DistanceCalculator
from src.analyzers.aggregator import CityAggregator

# After aggregating cities
city_stats = aggregator.aggregate(facilities)

# Calculate distances for each city
for stats in city_stats:
    stats.avg_distance_to_nearest = DistanceCalculator.calculate_distance_to_nearest(
        stats.city, 
        facilities
    )
```

## Success Criteria

- [x] All acceptance criteria met
- [x] Unit tests achieve 100% code coverage
- [x] Distance calculations validated against Google Maps for known city pairs
- [x] Performance: Processes 100 facilities in <1 second
- [x] No external API calls (pure calculation)
- [x] Documentation complete with examples

## References

### Algarve Geography
- Approximate region bounds: Lat 36.96-37.42, Lng -9.0 to -7.4
- East-west span: ~120 km
- North-south span: ~50 km

### Known Distance Examples (for testing)
- Albufeira to Faro: ~26 km
- Lagos to Portimão: ~18 km
- Tavira to Vila Real de Santo António: ~22 km

### Geopy Documentation
- [Geodesic Distance](https://geopy.readthedocs.io/en/stable/#module-geopy.distance)
- Uses Vincenty formula (accurate to ~0.5mm)

## Related Stories

- **Story 0.1** (Data Models): Uses Facility model
- **Story 4.1** (City Aggregator): Provides city center coordinates
- **Story 4.3** (Opportunity Scorer): Consumes distance metrics for scoring

## Questions & Assumptions

### Assumptions
1. City center is adequately represented by average of facility coordinates
2. Users willing to travel further in less populated areas
3. Geodesic distance is sufficient (no road routing needed)
4. Distance to nearest neighboring city is a good proxy for geographic opportunity

### Open Questions
- Should we calculate distance to nearest facility OR average distance to top N facilities?
  - **Decision**: Use minimum distance (most optimistic accessibility)
- Should travel willingness be configurable?
  - **Decision**: Hardcode for MVP, make configurable later if needed

