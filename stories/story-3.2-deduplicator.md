# Story 3.2: Deduplicator

## Metadata
- **Priority**: P0 (Critical Path)
- **Layer**: 3 (Processing)
- **Dependencies**: Story 0.1 (Data Models)
- **Estimated Effort**: Small
- **Status**: Complete

## Overview

Remove duplicate facilities from collected data using both exact and fuzzy matching strategies.

## Problem Statement

When collecting data from Google Places API using multiple search queries, the same facility may appear multiple times. We need to deduplicate these results to ensure:
1. Accurate facility counts per city
2. No duplicate markers on maps
3. Clean data for analysis and scoring

## Input Contract

```python
List[Facility]  # Raw facility list (may contain duplicates)
```

## Output Contract

```python
List[Facility]  # Deduplicated facility list
```

## API Surface

```python
class Deduplicator:
    """Remove duplicate facilities."""
    
    @staticmethod
    def deduplicate(facilities: List[Facility]) -> List[Facility]:
        """
        Remove duplicates based on:
        1. place_id (exact match)
        2. Name + approximate location (fuzzy match)
        
        Args:
            facilities: List of facilities (may contain duplicates)
            
        Returns:
            List of unique facilities
        """
```

## Functional Requirements

### FR1: Exact Place ID Deduplication
- Remove facilities with identical `place_id`
- Keep the first occurrence of each place_id
- This handles duplicates from multiple search queries

### FR2: Fuzzy Name + Location Matching
- Detect duplicates with same name but slightly different coordinates
- Group by:
  - City (exact match)
  - Name (case-insensitive, stripped)
  - Latitude (rounded to 3 decimal places ≈ 111m precision)
  - Longitude (rounded to 3 decimal places ≈ 111m precision)
- Keep first occurrence from each group

### FR3: Data Preservation
- When duplicates are found, keep the facility with highest completeness score
- **Completeness Score Algorithm:**
  ```python
  def completeness_score(facility: Facility) -> int:
      """Count non-null optional fields."""
      score = 0
      if facility.phone: score += 1
      if facility.website: score += 1
      if facility.indoor_outdoor: score += 1
      if facility.num_courts: score += 1
      if facility.postal_code: score += 1
      if facility.facility_type: score += 1
      return score
  ```
- If scores are equal, keep first occurrence
- Preserve all fields from the kept facility
- No data loss from deduplication process

## Non-Functional Requirements

### NFR1: Performance
- Handle up to 500 facilities efficiently
- Execution time < 1 second for typical dataset (50-100 facilities)

### NFR2: Reliability
- Never remove legitimate distinct facilities
- Handle edge cases (missing fields, special characters in names)

### NFR3: Testability
- 100% test coverage
- Test fixtures for various duplicate scenarios

## Implementation Details

### Deduplication Strategy

**Two-Pass Algorithm**:

1. **Pass 1**: Exact `place_id` matching
   - Iterate through facilities
   - Track seen place_ids in a set
   - Only keep first occurrence

2. **Pass 2**: Fuzzy name + location matching
   - Convert to pandas DataFrame for efficient grouping
   - Create normalized columns:
     - `name_lower`: lowercase, stripped name
     - `lat_round`: latitude rounded to 3 decimals
     - `lng_round`: longitude rounded to 3 decimals
   - Use `drop_duplicates()` on `['city', 'name_lower', 'lat_round', 'lng_round']`
   - Convert back to Facility objects

### Edge Cases to Handle

1. **Special characters in names**: "Padel Club" vs "Pádel Club"
   - Solution: Normalize to lowercase and strip whitespace
   
2. **Slight coordinate variations**: (37.0881, -8.2475) vs (37.0882, -8.2476)
   - Solution: Round to 3 decimal places (≈111m precision)
   
3. **Missing optional fields**: Some facilities have website, others don't
   - Solution: Keep first occurrence (assumes data completeness is similar)
   
4. **Same name, different locations**: "Padel Club" in Albufeira vs Faro
   - Solution: Include city in grouping criteria

## Acceptance Criteria

- [x] **AC1**: Remove exact place_id duplicates
  - Given 10 facilities with 3 duplicate place_ids
  - When deduplicate() is called
  - Then return 7 unique facilities

- [x] **AC2**: Remove fuzzy name + location duplicates
  - Given facilities with same name and coordinates (±0.001)
  - When deduplicate() is called
  - Then keep only one facility per location

- [x] **AC3**: Preserve distinct facilities in same city
  - Given 2 facilities with different names in same city
  - When deduplicate() is called
  - Then return both facilities

- [x] **AC4**: Handle case-insensitive name matching
  - Given "Padel Club" and "padel club" at same location
  - When deduplicate() is called
  - Then return only one facility

- [x] **AC5**: Keep facility with highest completeness score
  - Given two duplicate facilities with different field completeness
  - When deduplicate() is called
  - Then keep the facility with more non-null optional fields

- [x] **AC6**: Unit tests with duplicate fixtures
  - Test exact duplicates
  - Test fuzzy duplicates
  - Test legitimate distinct facilities
  - Test edge cases (special characters, missing fields)
  - **Test completeness score calculation**
  - **Test keeping most complete duplicate**

## Files to Create

```
src/processors/deduplicator.py        # Main implementation
tests/test_processors/test_deduplicator.py  # Unit tests
```

## Testing Strategy

### Unit Tests

1. **test_deduplicate_exact_place_id**
   - Create 5 facilities with 2 duplicate place_ids
   - Assert returns 3 unique facilities
   - Assert place_ids are unique

2. **test_deduplicate_fuzzy_name_location**
   - Create facilities with same name, city, and coordinates (±0.0001)
   - Assert returns 1 facility
   
3. **test_preserve_distinct_facilities**
   - Create facilities with different names in same city
   - Assert all facilities are kept
   
4. **test_case_insensitive_names**
   - Create "PADEL CLUB", "Padel Club", "padel club" at same location
   - Assert returns 1 facility
   
5. **test_empty_list**
   - Pass empty list
   - Assert returns empty list
   
6. **test_single_facility**
   - Pass list with 1 facility
   - Assert returns same facility
   
7. **test_no_duplicates**
   - Pass list with all unique facilities
   - Assert all facilities returned

8. **test_completeness_score**
   - Create facility with all optional fields filled: score = 6
   - Create facility with only phone and website: score = 2
   - Assert scores are calculated correctly

9. **test_keep_most_complete_duplicate**
   - Create two duplicates: one with phone/website, one with all fields
   - Assert the facility with all fields is kept
   - Assert facility with fewer fields is removed

### Test Fixtures

```python
@pytest.fixture
def duplicate_facilities():
    """Facilities with exact place_id duplicates."""
    return [
        Facility(place_id="test_1", name="Club A", ...),
        Facility(place_id="test_1", name="Club A", ...),  # Duplicate
        Facility(place_id="test_2", name="Club B", ...),
    ]

@pytest.fixture
def fuzzy_duplicate_facilities():
    """Facilities with fuzzy name/location duplicates."""
    return [
        Facility(place_id="test_1", name="Padel Club", 
                 latitude=37.0881, longitude=-8.2475, ...),
        Facility(place_id="test_2", name="padel club", 
                 latitude=37.0882, longitude=-8.2476, ...),  # Fuzzy duplicate
    ]
```

## Dependencies

### External Libraries
- `pandas`: DataFrame operations for efficient grouping
- `typing`: Type hints

### Internal Dependencies
- `src/models/facility.py`: Facility model with `to_dict()` method

## Success Criteria

- [x] All unit tests passing
- [x] 100% code coverage
- [x] Removes exact duplicates (place_id)
- [x] Removes fuzzy duplicates (name + location)
- [x] Preserves all legitimate distinct facilities
- [x] Execution time < 1 second for 100 facilities
- [x] Code reviewed and approved

## Notes

- The 3 decimal place rounding (≈111m precision) is chosen to catch near-duplicates while avoiding false positives for legitimately close facilities
- Completeness score ensures we keep the facility with the most information
- If completeness scores are equal, first occurrence is kept to maintain consistency with data collection order

## Integration Points

**Used By**:
- Story 5.1 (Data Collection CLI) - calls `deduplicate()` after cleaning

**Uses**:
- Story 0.1 (Data Models) - `Facility` model for input/output

