# Story 9.2: Add City Center Coordinates

## Overview
**Priority**: P0 (Critical - Prerequisite for Story 9.1 and 9.3)  
**Dependencies**: None  
**Estimated Effort**: Small  
**Layer**: 4 (Analysis) - Data Addition

## Problem Statement

Currently, city center coordinates are calculated as the mean of facility locations:

```python
center_lat = float(city_group['latitude'].mean())  # From facilities
center_lng = float(city_group['longitude'].mean())  # From facilities
```

**The Problem:**
- This fails for cities with **zero facilities** - there are no coordinates to average
- Zero-facility cities need geographic centers for distance calculations
- Distance calculations need to measure "How far is this city from the nearest padel court anywhere?"
- Without city centers, we can't calculate distances for greenfield opportunities

**Why We Need This:**
- Story 9.1 needs city centers to create `CityStats` for zero-facility cities
- Story 9.3 needs city centers to calculate "distance from city center to nearest facility"
- Proper geographic analysis requires actual city centers, not facility-based approximations

## Description

Add a `CITY_CENTERS` constant to `CityAggregator` containing the actual geographic center (latitude/longitude) for all 15 Algarve municipalities. These are fixed coordinates representing the city center, independent of where facilities are located.

## Contracts

### API Surface

```python
class CityAggregator:
    """Aggregate facility data by city."""
    
    # Existing constant
    CITY_POPULATIONS: Dict[str, int]
    
    # NEW: City center coordinates
    CITY_CENTERS: Dict[str, Dict[str, float]]  # {city_name: {"lat": float, "lng": float}}
```

## Requirements

### City Center Coordinates

Add actual city center coordinates for all 15 Algarve municipalities:

```python
CITY_CENTERS = {
    "Albufeira": {"lat": 37.0885, "lng": -8.2475},
    "Aljezur": {"lat": 37.3185, "lng": -8.8052},
    "Castro Marim": {"lat": 37.2167, "lng": -7.4333},
    "Faro": {"lat": 37.0194, "lng": -7.9322},
    "Lagoa": {"lat": 37.1332, "lng": -8.4539},
    "Lagos": {"lat": 37.1028, "lng": -8.6742},
    "Loulé": {"lat": 37.1417, "lng": -8.0224},
    "Monchique": {"lat": 37.3167, "lng": -8.5500},
    "Olhão": {"lat": 37.0264, "lng": -7.8410},
    "Portimão": {"lat": 37.1390, "lng": -8.5376},
    "São Brás de Alportel": {"lat": 37.1522, "lng": -7.8831},
    "Silves": {"lat": 37.1911, "lng": -8.4380},
    "Tavira": {"lat": 37.1276, "lng": -7.6486},
    "Vila do Bispo": {"lat": 37.0833, "lng": -8.9167},
    "Vila Real de Santo António": {"lat": 37.1944, "lng": -7.4167},
}
```

**Source:** Approximate city center coordinates from OpenStreetMap / Google Maps
**Precision:** Coordinates accurate to ~100m, sufficient for distance calculations
**Format:** Decimal degrees (WGS84 / GPS standard)

### Usage in Aggregator

For cities **with facilities:**
- Continue using facility-based center (mean of facility coordinates) - this represents the "center of padel activity"
- City center coordinates serve as fallback/validation

For cities **without facilities:**
- Use `CITY_CENTERS` coordinates directly
- This enables distance calculations in Story 9.3

## Acceptance Criteria

- [ ] `CITY_CENTERS` constant added to `CityAggregator` class
- [ ] All 15 Algarve cities have city center coordinates
- [ ] Coordinates are in decimal degrees format (lat/lng)
- [ ] Coordinates are validated (latitude: 36.9 to 37.4, longitude: -8.9 to -7.4 for Algarve)
- [ ] Dictionary structure matches specification: `{city_name: {"lat": float, "lng": float}}`
- [ ] Unit test verifies all 15 cities present in `CITY_CENTERS`
- [ ] Unit test validates coordinate ranges (Algarve bounding box)
- [ ] Documentation explains source and usage of coordinates

## Files to Modify

```
src/analyzers/
└── aggregator.py          # Add CITY_CENTERS constant

tests/test_analyzers/
└── test_aggregator.py     # Add validation tests for CITY_CENTERS
```

## Test Requirements

### New Unit Tests (`test_aggregator.py`)

**Constant Validation:**
- [ ] Test `CITY_CENTERS` contains all 15 cities
- [ ] Test all cities in `CITY_CENTERS` match cities in `CITY_POPULATIONS`
- [ ] Test all coordinates are valid floats
- [ ] Test latitude values in valid range (36.9 to 37.4)
- [ ] Test longitude values in valid range (-8.9 to -7.4)
- [ ] Test dictionary structure is correct (city -> {"lat", "lng"})

**Integration:**
- [ ] Test city center coordinates can be accessed in `aggregate()` method
- [ ] Test city centers are used for zero-facility cities (integration with Story 9.1)

## Technical Notes

### Coordinate Sources

Coordinates obtained from:
1. OpenStreetMap (primary source - open data)
2. Google Maps (validation)
3. Administrative center points (not geographic centroid)

**Why administrative centers:** 
- More relevant for business analysis
- Where population is concentrated
- Where facilities would likely be built

### Validation

Algarve bounding box (approximate):
- Latitude: 36.9°N to 37.4°N
- Longitude: 8.9°W to 7.4°W

Any coordinates outside this range indicate data entry errors.

### Future Enhancements

Consider for later stories:
- Load coordinates from external configuration file (JSON/YAML)
- Validate coordinates against geocoding API
- Add multiple points per city (neighborhoods for large cities)
- Include city boundary polygons for more precise "is in city" checks

## Example Usage

```python
from src.analyzers.aggregator import CityAggregator

aggregator = CityAggregator()

# Access city center
monchique_center = aggregator.CITY_CENTERS["Monchique"]
print(f"Monchique center: {monchique_center['lat']}, {monchique_center['lng']}")
# Output: Monchique center: 37.3167, -8.55

# Use in aggregation for zero-facility cities
city_stats = aggregator.aggregate([])  # Empty facility list
for stats in city_stats:
    print(f"{stats.city}: ({stats.center_lat}, {stats.center_lng})")
# All 15 cities will have valid center coordinates
```

## Success Criteria

This story is considered complete when:
1. `CITY_CENTERS` constant is added with all 15 cities
2. All coordinates are accurate (validated against maps)
3. All acceptance criteria met
4. Validation tests pass
5. Coordinates are documented with source information
6. Ready for integration with Story 9.1 and 9.3

## Related Stories

**Enables:**
- Story 9.1: Fix Zero-Facility Cities (needs city centers for `CityStats` creation)
- Story 9.3: Fix Distance Calculation (needs city centers for zero-facility distance calculations)

**Future Considerations:**
- Could be extracted to configuration file (Story 0.2 enhancement)
- Could be validated against geocoding API (future data quality story)
- Could support multiple points per city for large municipalities

## Business Impact

**Enables:**
- Proper geographic analysis for all cities
- Accurate distance calculations for greenfield opportunities
- Foundation for spatial analysis and mapping
- City center points can be used in future stories (nearest beach, nearest highway, etc.)

