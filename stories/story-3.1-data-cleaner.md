# Story 3.1: Data Cleaner

## Overview

**Priority**: P0 (Critical Path)  
**Layer**: 3 - Processing  
**Dependencies**: Story 0.1 (Data Models)  
**Estimated Effort**: Small  
**Story Points**: 3

## Description

Implement a data cleaning and validation module that processes raw facility data collected from Google Places API. The cleaner ensures data quality by removing invalid entries, normalizing values, and validating against Algarve geographic bounds.

## Business Value

- Ensures data integrity for downstream analysis
- Prevents errors from invalid or out-of-bounds facilities
- Standardizes data format for consistent processing
- Reduces noise in opportunity scoring calculations

## Input Contract

```python
facilities: List[Facility]  # Raw facility data from collectors
```

**Data Source**: Output from Google Places Collector (Story 1.1) or any collector returning `List[Facility]`

**Expected Input Characteristics**:
- May contain facilities outside Algarve region
- May have missing city information
- May have invalid or out-of-range ratings
- May have invalid coordinates
- City names may have inconsistent formatting

## Output Contract

```python
List[Facility]  # Cleaned and validated facilities
```

**Output Guarantees**:
- All facilities have valid coordinates within Algarve bounds
- All facilities have a city assigned
- City names are normalized (title case, trimmed)
- Ratings are either None or in valid range [0, 5]
- All required fields are populated

## API Surface

```python
class DataCleaner:
    """Clean and validate facility data."""
    
    @staticmethod
    def clean_facilities(facilities: List[Facility]) -> List[Facility]:
        """
        Clean and validate facility data.
        
        Args:
            facilities: List of raw Facility objects
            
        Returns:
            List of cleaned Facility objects
            
        Operations:
        - Remove invalid coordinates
        - Filter to Algarve geographic bounds
        - Remove facilities without city
        - Normalize city names
        - Validate rating ranges (0-5)
        """
        pass
    
    @staticmethod
    def to_dataframe(facilities: List[Facility]) -> pd.DataFrame:
        """
        Convert facilities to pandas DataFrame for analysis.
        
        Args:
            facilities: List of Facility objects
            
        Returns:
            DataFrame with all facility data
        """
        pass
```

## Functional Requirements

### FR1: Coordinate Validation
- **Requirement**: Validate that facility coordinates fall within Algarve boundaries
- **Algarve Bounds**:
  - Latitude: 36.96° to 37.42° N
  - Longitude: -9.0° to -7.4° E
- **Behavior**: Remove facilities outside these bounds
- **Rationale**: Ensures we only analyze facilities relevant to Algarve market

### FR2: City Validation
- **Requirement**: Remove facilities without a city assigned
- **Behavior**: Filter out any facility where `city` is None or empty string
- **Rationale**: City is required for aggregation and analysis

### FR3: City Name Normalization
- **Requirement**: Standardize city name formatting
- **Operations**:
  - Strip leading/trailing whitespace
  - Convert to title case (e.g., "albufeira" → "Albufeira")
  - Apply through Facility model's built-in validator
- **Rationale**: Ensures consistent grouping in aggregation

### FR4: Rating Validation
- **Requirement**: Validate rating values are in valid range
- **Valid Range**: 0.0 to 5.0 (Google's rating system)
- **Behavior**: 
  - If rating < 0 or rating > 5: set to None
  - If rating is None: leave as None
- **Rationale**: Prevents calculation errors from invalid data

### FR5: DataFrame Conversion
- **Requirement**: Provide utility to convert facilities to pandas DataFrame
- **Behavior**: Use Facility.to_dict() method for each facility
- **Rationale**: Many analysis functions work with DataFrames

## Non-Functional Requirements

### Performance
- **Requirement**: Process 1000 facilities in < 1 second
- **Rationale**: Cleaning should not be a bottleneck in pipeline

### Data Loss
- **Requirement**: Log count of removed facilities and reasons
- **Rationale**: Transparency in data cleaning process

### Idempotency
- **Requirement**: Running cleaner multiple times produces same result
- **Rationale**: Predictable behavior for debugging

## Acceptance Criteria

### AC1: Coordinate Filtering
- [ ] Given a facility with latitude = 36.90 (below minimum), it is removed
- [ ] Given a facility with latitude = 37.45 (above maximum), it is removed
- [ ] Given a facility with longitude = -9.1 (below minimum), it is removed
- [ ] Given a facility with longitude = -7.3 (above maximum), it is removed
- [ ] Given a facility with valid Algarve coordinates, it is kept

### AC2: City Validation
- [ ] Given a facility with city = None, it is removed
- [ ] Given a facility with city = "", it is removed
- [ ] Given a facility with city = "Albufeira", it is kept

### AC3: City Normalization
- [ ] Given city = " albufeira ", output city = "Albufeira"
- [ ] Given city = "FARO", output city = "Faro"
- [ ] Given city = "lagos  ", output city = "Lagos"

### AC4: Rating Validation
- [ ] Given rating = -1.0, output rating = None
- [ ] Given rating = 5.5, output rating = None
- [ ] Given rating = None, output rating = None
- [ ] Given rating = 4.3, output rating = 4.3

### AC5: DataFrame Conversion
- [ ] Given list of facilities, returns DataFrame with correct columns
- [ ] DataFrame has same number of rows as input list
- [ ] All facility attributes are present as columns

### AC6: Test Coverage
- [ ] Unit test coverage = 100%
- [ ] All edge cases tested

## Test Cases

### Test Case 1: Valid Facility Passes Through
```python
facility = Facility(
    place_id="test123",
    name="Padel Club",
    city="Albufeira",
    latitude=37.0885,
    longitude=-8.2475,
    rating=4.5,
    ...
)
result = DataCleaner.clean_facilities([facility])
assert len(result) == 1
assert result[0].city == "Albufeira"
```

### Test Case 2: Invalid Coordinates Removed
```python
facility = Facility(
    ...,
    latitude=38.0,  # Too far north
    longitude=-8.0
)
result = DataCleaner.clean_facilities([facility])
assert len(result) == 0
```

### Test Case 3: Missing City Removed
```python
facility = Facility(
    ...,
    city=None,
    latitude=37.0,
    longitude=-8.0
)
result = DataCleaner.clean_facilities([facility])
assert len(result) == 0
```

### Test Case 4: Invalid Rating Corrected
```python
facility = Facility(..., rating=6.0)
result = DataCleaner.clean_facilities([facility])
assert result[0].rating is None
```

### Test Case 5: City Name Normalized
```python
facility = Facility(..., city=" faro ")
result = DataCleaner.clean_facilities([facility])
assert result[0].city == "Faro"
```

### Test Case 6: DataFrame Conversion
```python
facilities = [facility1, facility2, facility3]
df = DataCleaner.to_dataframe(facilities)
assert isinstance(df, pd.DataFrame)
assert len(df) == 3
assert "place_id" in df.columns
assert "city" in df.columns
```

## Implementation Guidelines

### Code Structure
```
src/processors/
├── __init__.py
└── cleaner.py         # DataCleaner class

tests/test_processors/
├── __init__.py
└── test_cleaner.py    # Unit tests
```

### Key Algorithms

**Cleaning Algorithm**:
1. Initialize empty list for cleaned facilities
2. For each facility in input:
   a. Check if city exists → skip if not
   b. Validate latitude bounds → skip if invalid
   c. Validate longitude bounds → skip if invalid
   d. Validate rating range → set to None if invalid
   e. City normalization handled by Pydantic validator
   f. Add to cleaned list
3. Return cleaned list

### Error Handling

Follow error handling patterns defined in Story 0.2:
- **Validation Errors** (Pattern 2): Let Pydantic errors propagate (indicates data model issue)
- **Data Collection Errors** (Pattern 1): Skip invalid facilities gracefully, log warning
- **Invalid Facility Object**: Skip gracefully, log warning
- **Empty Input List**: Return empty list (valid case)

### Logging

All data cleaning operations should log their results for transparency:

```python
import logging

logger = logging.getLogger(__name__)

def clean_facilities(facilities):
    initial_count = len(facilities)
    # ... cleaning logic ...
    final_count = len(cleaned)
    removed = initial_count - final_count
    
    logger.info(f"Cleaned {initial_count} facilities: {final_count} kept, {removed} removed")
    
    # Log specific reasons for removal
    if removed > 0:
        logger.debug(f"Removed: {removed_invalid_coords} invalid coordinates, "
                    f"{removed_no_city} missing city, {removed_bad_rating} invalid ratings")
```

**Note**: Add `import logging` and `logger = logging.getLogger(__name__)` at the top of the module.

## Integration Points

### Upstream Dependencies
- **Story 0.1**: Requires `Facility` model with:
  - All required fields defined
  - City name validator (normalize_city)
  - to_dict() method

### Downstream Consumers
- **Story 3.2**: Deduplicator receives cleaned facilities
- **Story 5.1**: Data collection CLI calls cleaner
- **Story 4.1**: Aggregator expects cleaned data

## Files to Create

### Implementation Files
- `src/processors/__init__.py` - Package initializer (typically empty)
- `src/processors/cleaner.py` - Main DataCleaner implementation

### Test Files
- `tests/test_processors/__init__.py` - Package initializer (typically empty)
- `tests/test_processors/test_cleaner.py` - Unit tests

**Note**: All `__init__.py` files can be empty unless exports are needed.

### Test Fixtures (in conftest.py or test file)
- `sample_valid_facility`
- `sample_invalid_coordinates_facility`
- `sample_no_city_facility`
- `sample_invalid_rating_facility`
- `sample_unnormalized_city_facility`

## Definition of Done

- [ ] `DataCleaner` class implemented in `src/processors/cleaner.py`
- [ ] `clean_facilities()` method works as specified
- [ ] `to_dataframe()` method works as specified
- [ ] All coordinate bounds correctly enforced
- [ ] City validation working
- [ ] Rating validation working
- [ ] City normalization delegated to Pydantic model
- [ ] Comprehensive unit tests in `tests/test_processors/test_cleaner.py`
- [ ] 100% code coverage achieved
- [ ] All test cases pass
- [ ] Type hints on all methods
- [ ] Docstrings on class and methods
- [ ] Code follows project style (black formatted)
- [ ] No linting errors

## Future Enhancements (Out of Scope)

- Configurable geographic bounds
- More sophisticated city name matching (fuzzy matching)
- Data quality metrics reporting
- Cleaning rules configuration file
- Support for multiple regions beyond Algarve

## Notes

- The Facility model's Pydantic validators handle some normalization automatically
- Cleaner should be stateless (all static methods)
- No external API calls required
- Fast operation - pure data validation
- Consider using pandas for batch validation if performance becomes an issue

