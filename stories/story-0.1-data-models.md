# Story 0.1: Data Models & Validation

## Overview
**Priority**: P0 (Blocker)  
**Dependencies**: None  
**Estimated Effort**: Small  
**Layer**: 0 (Foundation)

## Description
Create Pydantic models for data validation and type safety. These models will serve as the foundation for all data structures in the application, ensuring data integrity and providing clear contracts between system components.

## Contracts

### Input Contract
None (foundational models)

### Output Contract
- `Facility` model with validation
- `CityStats` model with validation
- Exports to dict/JSON/CSV

## Requirements

### Facility Model
The `Facility` model must include the following fields:

**Identifiers:**
- `place_id: str` - Google Places ID (required)
- `name: str` - Facility name (required, min_length=1)

**Location:**
- `address: str` - Full address
- `city: str` - City name (normalized to Title Case)
- `postal_code: Optional[str]` - Postal code
- `latitude: float` - Latitude (required, range: -90 to 90)
- `longitude: float` - Longitude (required, range: -180 to 180)

**Social Metrics:**
- `rating: Optional[float]` - Average rating (range: 0 to 5)
- `review_count: int` - Number of reviews (default: 0, min: 0)
- `google_url: Optional[str]` - Google Maps URL

**Facility Details (optional):**
- `facility_type: Optional[str]` - Type: "club", "sports_center", "other"
- `num_courts: Optional[int]` - Number of courts (min: 1)
- `indoor_outdoor: Optional[str]` - Court type: "indoor", "outdoor", "both", or None
- `phone: Optional[str]` - Phone number
- `website: Optional[str]` - Website URL

**Metadata:**
- `collected_at: datetime` - Collection timestamp (auto-generated)
- `last_updated: datetime` - Last update timestamp (auto-generated)

**Validators (using Pydantic v2 `@field_validator`):**
- `validate_indoor_outdoor`: Ensure value is one of: 'indoor', 'outdoor', 'both', or None
- `normalize_city`: Strip whitespace and convert to Title Case

**Methods:**
- `to_dict() -> dict`: Convert model to dictionary for CSV export (with ISO format timestamps)

### CityStats Model
The `CityStats` model must include the following fields:

**Basic Info:**
- `city: str` - City name (required)

**Facility Counts:**
- `total_facilities: int` - Total number of facilities (min: 0)

**Rating Statistics:**
- `avg_rating: Optional[float]` - Average rating (range: 0 to 5)
- `median_rating: Optional[float]` - Median rating (range: 0 to 5)
- `total_reviews: int` - Total review count (default: 0, min: 0)

**Geographic:**
- `center_lat: float` - City center latitude
- `center_lng: float` - City center longitude

**Population:**
- `population: Optional[int]` - City population (min: 0)

**Calculated Metrics:**
- `facilities_per_capita: Optional[float]` - Facilities per 10,000 residents
- `avg_distance_to_nearest: Optional[float]` - Average distance to nearest facility (km)

**Opportunity Scoring:**
- `opportunity_score: float` - Final score (default: 0.0, range: 0 to 100)
- `population_weight: float` - Population component (default: 0.0, range: 0 to 1)
- `saturation_weight: float` - Saturation component (default: 0.0, range: 0 to 1)
- `quality_gap_weight: float` - Quality gap component (default: 0.0, range: 0 to 1)
- `geographic_gap_weight: float` - Geographic gap component (default: 0.0, range: 0 to 1)

**Methods:**
- `calculate_opportunity_score()`: Calculate weighted opportunity score using formula:
  ```
  opportunity_score = (
      population_weight * 0.2 +
      saturation_weight * 0.3 +
      quality_gap_weight * 0.2 +
      geographic_gap_weight * 0.3
  ) * 100
  ```

## Acceptance Criteria

- [ ] `Facility` model implemented with all required fields
- [ ] `Facility` model includes `indoor_outdoor` field with validation
- [ ] `CityStats` model implemented with all required fields
- [ ] Validators for ratings (0-5 range)
- [ ] Validators for coordinates (latitude: -90 to 90, longitude: -180 to 180)
- [ ] Validator for `indoor_outdoor` field (only allows: 'indoor', 'outdoor', 'both', None)
- [ ] City name normalization (strip + Title Case)
- [ ] `to_dict()` method on `Facility` converts all fields to dict format
- [ ] `to_dict()` serializes datetime fields to ISO format strings
- [ ] `calculate_opportunity_score()` method on `CityStats` implements correct formula
- [ ] All models use Pydantic's BaseModel
- [ ] All models include proper type hints
- [ ] All models include field descriptions where appropriate
- [ ] 100% test coverage on models

## Files to Create

```
src/models/
├── __init__.py            # Package initializer (can be empty or export models)
├── facility.py            # Facility model
└── city.py                # CityStats model

tests/test_models/
├── __init__.py            # Package initializer (typically empty)
├── test_facility.py       # Facility model tests
└── test_city.py           # CityStats model tests
```

**Note**: All `__init__.py` files can be empty unless you want to export classes for easier imports. For example:
```python
# src/models/__init__.py
from .facility import Facility
from .city import CityStats

__all__ = ['Facility', 'CityStats']
```

## Test Requirements

### Facility Model Tests (`test_facility.py`)
- [ ] Test valid facility creation
- [ ] Test required fields validation
- [ ] Test latitude validation (valid range)
- [ ] Test longitude validation (valid range)
- [ ] Test rating validation (0-5 range, None allowed)
- [ ] Test review_count validation (min: 0)
- [ ] Test indoor_outdoor validation (only valid values accepted)
- [ ] Test invalid indoor_outdoor raises ValueError
- [ ] Test city name normalization (strips whitespace, Title Case)
- [ ] Test to_dict() includes all fields
- [ ] Test to_dict() converts datetime to ISO format string
- [ ] Test optional fields can be None
- [ ] Test datetime auto-generation for collected_at and last_updated

### CityStats Model Tests (`test_city.py`)
- [ ] Test valid city stats creation
- [ ] Test required fields validation
- [ ] Test rating validation (0-5 range, None allowed)
- [ ] Test opportunity score calculation formula
- [ ] Test opportunity score bounds (0-100)
- [ ] Test weight bounds (0-1 for all weights)
- [ ] Test facilities_per_capita calculation
- [ ] Test all numeric fields accept valid ranges
- [ ] Test default values for scores and weights

## Technical Notes

### Pydantic Version
Use Pydantic v2.x with the following imports:
```python
from pydantic import BaseModel, Field, field_validator
```

### Validation Strategy
- Use `Field()` for range validation (ge, le constraints)
- Use `@field_validator` decorators for custom validation logic (Pydantic v2 syntax)
- Use descriptive error messages in validators
- Note: Pydantic v2 uses `@field_validator('field_name')` instead of `@validator('field_name')`

### Type Hint Conventions
- Use `Optional[Type]` syntax (not `Type | None`) for consistency across Python 3.10+
- Always use `from typing import Optional` for clarity
- All function parameters and return types must have type hints

### Serialization
- `to_dict()` should handle None values gracefully
- DateTime fields must be converted to ISO format strings for CSV compatibility
- All numeric types should remain as numbers (not converted to strings)

## Example Usage (for reference)

```python
# Creating a facility
facility = Facility(
    place_id="ChIJ123abc",
    name="Padel Club Algarve",
    address="Rua Example, 123",
    city="albufeira",  # Will be normalized to "Albufeira"
    latitude=37.0885,
    longitude=-8.2475,
    rating=4.5,
    review_count=150,
    indoor_outdoor="both"
)

# Export to dict
data = facility.to_dict()

# Creating city stats
stats = CityStats(
    city="Albufeira",
    total_facilities=10,
    avg_rating=4.2,
    center_lat=37.0885,
    center_lng=-8.2475,
    population=42388,
    population_weight=0.65,
    saturation_weight=0.45,
    quality_gap_weight=0.30,
    geographic_gap_weight=0.55
)

# Calculate score
stats.calculate_opportunity_score()
print(stats.opportunity_score)  # Should be between 0-100
```

## Success Criteria

This story is considered complete when:
1. All models are implemented with proper validation
2. All acceptance criteria are met
3. Test coverage is 100% for both models
4. All tests pass
5. Code follows Python best practices and PEP 8
6. Models can be imported and used in other modules

## Related Stories

**Blocks:**
- Story 1.1: Google Places Collector (needs Facility model)
- Story 3.1: Data Cleaner (needs Facility model)
- Story 3.2: Deduplicator (needs Facility model)
- Story 4.1: City Aggregator (needs both models)

**Related Documentation:**
- See Technical Design Document sections 5.1 and 5.2 for detailed model specifications

