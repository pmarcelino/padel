# Story 7.1: Integration Tests

**Priority**: P0 (Must Have)  
**Layer**: 7 (Integration & Testing)  
**Dependencies**: All previous stories (0.1-6.4)  
**Estimated Effort**: Medium

---

## Description

Create end-to-end integration tests that validate the entire data pipeline from collection to processing to visualization. These tests ensure that all components work together correctly and that the system produces accurate, complete results when all pieces are integrated.

Unlike unit tests that mock dependencies, integration tests use real components interacting with each other (though may still mock external APIs for reliability).

---

## Input Contract

- Completed implementation of all previous stories
- Test fixtures and sample data
- Mock API responses for external services (Google Places API, LLM APIs)

---

## Output Contract

A comprehensive integration test suite that:
- Tests the complete data pipeline
- Validates data flow between components
- Ensures CSV export/import works correctly
- Verifies cache behavior across multiple runs
- Validates error handling and recovery
- Achieves 80%+ overall code coverage

---

## Test Structure

```
tests/
├── test_integration/
│   ├── __init__.py
│   ├── test_pipeline.py          # End-to-end pipeline tests
│   ├── test_cli.py                # CLI script integration tests
│   ├── test_data_flow.py          # Data transformation tests
│   └── fixtures/
│       ├── mock_api_responses.json
│       ├── sample_facilities.csv
│       └── sample_city_stats.csv
```

---

## Testing Scenarios

### 1. End-to-End Data Pipeline

**Test**: `test_full_pipeline_collection_to_processing`

**Steps**:
1. Initialize GooglePlacesCollector with mocked API responses
2. Collect facilities (mocked to return 20 sample facilities)
3. Clean data using DataCleaner
4. Deduplicate using Deduplicator
5. Aggregate by city using CityAggregator
6. Calculate distances using DistanceCalculator
7. Calculate opportunity scores using OpportunityScorer
8. Save to CSV
9. Verify output files exist and contain expected data

**Assertions**:
- All components execute without errors
- Data flows correctly through each stage
- Output CSV files are valid and parseable
- No data loss between stages
- Calculated metrics are within expected ranges

---

### 2. CLI Script Integration

**Test**: `test_collect_data_cli_script`

**Steps**:
1. Mock Google Places API responses
2. Execute `collect_data.py` programmatically
3. Verify raw data file created
4. Check data quality and completeness

**Assertions**:
- Script completes successfully
- Output file `data/raw/facilities.csv` exists
- CSV contains valid facility records
- Progress logging output is generated
- Execution time is reasonable

---

**Test**: `test_process_data_cli_script`

**Steps**:
1. Create sample `data/raw/facilities.csv`
2. Execute `process_data.py` programmatically
3. Verify processed data files created
4. Check city statistics calculations

**Assertions**:
- Script completes successfully
- Output files `data/processed/facilities.csv` and `data/processed/city_stats.csv` exist
- All cities from input are present in output
- Opportunity scores calculated correctly
- Top cities displayed in correct order

---

### 3. CSV Export/Import Integration

**Test**: `test_csv_export_import_roundtrip`

**Steps**:
1. Create sample facilities in memory
2. Convert to DataFrame and export to CSV
3. Import CSV back into Facility objects
4. Verify data integrity

**Assertions**:
- All fields preserved (no data loss)
- Datetime fields correctly serialized/deserialized
- Optional fields (None values) handled correctly
- Floating point precision maintained
- City names preserved exactly

---

**Test**: `test_city_stats_csv_export_import`

**Steps**:
1. Create sample CityStats objects
2. Export to CSV
3. Import and recreate objects
4. Verify calculations match

**Assertions**:
- All metrics preserved
- Opportunity score weights maintained
- Calculated fields can be recomputed

---

### 4. Cache Behavior Integration

**Test**: `test_cache_reduces_api_calls`

**Steps**:
1. Clear cache directory
2. Run collection with mocked API (track call count)
3. Run collection again (should use cache)
4. Verify second run makes fewer API calls

**Assertions**:
- First run caches responses
- Second run reads from cache
- Cache files created in correct location
- TTL respected

---

**Test**: `test_cache_expiration`

**Steps**:
1. Create cached response with old timestamp
2. Run collection
3. Verify expired cache is refreshed

**Assertions**:
- Expired cache detected
- New API call made
- Cache file updated

---

### 5. Error Handling Integration

**Test**: `test_pipeline_handles_invalid_facilities`

**Steps**:
1. Create dataset with mix of valid and invalid facilities
   - Missing city
   - Invalid coordinates
   - Invalid rating values
2. Run through cleaning pipeline
3. Verify invalid facilities filtered out

**Assertions**:
- Invalid facilities removed
- Valid facilities preserved
- No exceptions raised
- Warning logs generated

---

**Test**: `test_pipeline_handles_empty_input`

**Steps**:
1. Run pipeline with empty facility list
2. Verify graceful handling

**Assertions**:
- No crashes
- Empty output files created
- Appropriate warnings logged

---

**Test**: `test_api_error_recovery`

**Steps**:
1. Mock API to fail on some requests
2. Run collection
3. Verify collector continues despite errors

**Assertions**:
- Partial results collected
- Errors logged
- Script completes (doesn't crash)

---

### 6. Data Transformation Validation

**Test**: `test_coordinate_normalization`

**Steps**:
1. Create facilities with coordinates outside Algarve
2. Run through cleaner
3. Verify out-of-bounds facilities removed

**Assertions**:
- Only Algarve coordinates (lat: 36.96-37.42, lng: -9.0 to -7.4) remain
- Boundary cases handled correctly

---

**Test**: `test_city_name_normalization`

**Steps**:
1. Create facilities with various city name formats
   - "albufeira", "ALBUFEIRA", "Albufeira", " Albufeira "
2. Run through cleaning
3. Verify all normalized to "Albufeira"

**Assertions**:
- Consistent capitalization (Title Case)
- Whitespace trimmed
- Grouping by city works correctly

---

**Test**: `test_deduplication_integration`

**Steps**:
1. Create dataset with duplicates:
   - Exact place_id duplicates
   - Same name + similar coordinates
2. Run through deduplicator
3. Count resulting unique facilities

**Assertions**:
- All exact duplicates removed
- Fuzzy duplicates detected
- Most complete record retained

---

### 7. Aggregation & Scoring Integration

**Test**: `test_city_aggregation_with_real_data`

**Steps**:
1. Create realistic dataset with multiple cities
2. Run aggregation
3. Verify statistics calculated correctly

**Assertions**:
- All cities represented
- Avg/median ratings correct
- Total reviews summed correctly
- Center coordinates reasonable

---

**Test**: `test_opportunity_scoring_integration`

**Steps**:
1. Create dataset with known characteristics:
   - City A: High population, low facilities → High score
   - City B: Low population, many facilities → Low score
2. Run scoring
3. Verify scores match expectations

**Assertions**:
- Scoring formula applied correctly
- Weights normalized (0-1)
- Final score in range 0-100
- Ranking makes logical sense

---

### 8. LLM Enrichment Integration (If Implemented)

**Test**: `test_llm_indoor_outdoor_enrichment`

**Steps**:
1. Mock LLM API to return structured responses
2. Create facilities with reviews
3. Run enrichment
4. Verify indoor/outdoor field populated

**Assertions**:
- Only facilities without indoor/outdoor value enriched
- Confidence threshold respected
- API errors handled gracefully

---

### 9. Performance Benchmarking

**Test**: `test_pipeline_performance_benchmark`

**Steps**:
1. Create dataset with 100 facilities across 15 cities
2. Use pytest-benchmark to measure execution time
3. Run full pipeline (aggregate → distance → score)
4. Verify performance meets requirements

**Assertions**:
- Total pipeline time < 120 seconds
- Performance regression detection (compare against baseline)

**Example**:
```python
def test_pipeline_performance(benchmark):
    """Benchmark full pipeline execution time."""
    facilities = generate_sample_facilities(count=100)
    
    def run_pipeline():
        aggregator = CityAggregator()
        city_stats = aggregator.aggregate(facilities)
        
        distance_calc = DistanceCalculator()
        for stats in city_stats:
            stats.avg_distance_to_nearest = distance_calc.calculate_distance_to_nearest(
                stats.city, facilities
            )
        
        scorer = OpportunityScorer()
        return scorer.calculate_scores(city_stats)
    
    result = benchmark(run_pipeline)
    assert benchmark.stats['mean'] < 120  # 2 minutes
```

---

## Acceptance Criteria

- [ ] Test full data pipeline (collect → clean → deduplicate → aggregate → score → save)
- [ ] Test both CLI scripts (`collect_data.py`, `process_data.py`)
- [ ] Test CSV export/import roundtrip for both facilities and city stats
- [ ] Test cache behavior (creation, reading, expiration)
- [ ] Test error handling (invalid data, empty input, API errors)
- [ ] Test data transformation (coordinate validation, city normalization, deduplication)
- [ ] Test aggregation and scoring with realistic data
- [ ] **Performance benchmarks implemented using pytest-benchmark**
- [ ] **Baseline performance metrics documented**
- [ ] **Performance regression tests fail if execution time increases >20%**
- [ ] Achieve 80%+ overall code coverage (measured with pytest-cov)
- [ ] All tests pass consistently
- [ ] Tests run in reasonable time (< 2 minutes for full suite)
- [ ] Integration tests can be run with `pytest tests/test_integration/`
- [ ] Coverage report generated with `pytest --cov=src --cov-report=html`

---

## Files to Create

```
tests/test_integration/__init__.py
tests/test_integration/test_pipeline.py
tests/test_integration/test_cli.py
tests/test_integration/test_data_flow.py
tests/test_integration/fixtures/mock_api_responses.json
tests/test_integration/fixtures/sample_facilities.csv
tests/test_integration/fixtures/sample_city_stats.csv
```

---

## Testing Utilities

### Mock API Response Helper

Create reusable mock data generators:

```python
def generate_mock_facility_data(count: int, city: str) -> List[Dict]:
    """Generate mock Google Places API responses."""
    pass

def generate_mock_reviews(count: int, keywords: List[str]) -> List[str]:
    """Generate mock review texts with specified keywords."""
    pass
```

### Fixture Setup

Create pytest fixtures for common test scenarios:

```python
@pytest.fixture
def sample_facilities() -> List[Facility]:
    """Sample facilities covering various edge cases."""
    pass

@pytest.fixture
def temp_data_dir(tmp_path) -> Path:
    """Temporary data directory for test outputs."""
    pass

@pytest.fixture
def mocked_google_api(mocker):
    """Mock Google Places API responses."""
    pass
```

---

## Performance Requirements

- Full integration test suite completes in < 2 minutes
- Individual test cases complete in < 10 seconds
- Cache tests verify performance improvement (2x+ faster with cache)
- **Performance benchmarks using pytest-benchmark:**
  - Pipeline processing time < 120 seconds for 100 facilities
  - City aggregation < 1 second for 100 facilities
  - Opportunity scoring < 1 second for 15 cities
  - Distance calculations < 5 seconds for 15 cities

---

## Coverage Requirements

Achieve minimum 80% coverage across:
- `src/collectors/` - API interaction and data collection
- `src/processors/` - Data cleaning and deduplication
- `src/analyzers/` - Aggregation and scoring logic
- `src/models/` - Data validation
- `src/utils/` - Caching and utilities

Exclude from coverage:
- `app/` - Streamlit UI (test manually)
- `scripts/` - CLI entry points (test via integration)
- `tests/` - Test code itself

---

## Test Execution

### Run All Integration Tests
```bash
pytest tests/test_integration/ -v
```

### Run With Coverage
```bash
pytest tests/test_integration/ --cov=src --cov-report=term-missing --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_integration/test_pipeline.py -v
```

### Run Specific Test Case
```bash
pytest tests/test_integration/test_pipeline.py::test_full_pipeline_collection_to_processing -v
```

---

## Dependencies

This story requires all previous stories to be completed:

**Layer 0 (Foundation)**:
- Story 0.1: Data Models
- Story 0.2: Configuration Management
- Story 0.3: Caching Utilities

**Layer 1 (Data Collection)**:
- Story 1.1: Google Places Collector
- Story 1.2: Review Collector (optional)
- Story 1.3: Google Trends Collector (optional)

**Layer 2 (Enrichment)**:
- Story 2.1: LLM Indoor/Outdoor Analyzer (optional)

**Layer 3 (Processing)**:
- Story 3.1: Data Cleaner
- Story 3.2: Deduplicator

**Layer 4 (Analysis)**:
- Story 4.1: City Aggregator
- Story 4.2: Distance Calculator
- Story 4.3: Opportunity Scorer

**Layer 5 (CLI)**:
- Story 5.1: Data Collection CLI
- Story 5.2: Data Processing CLI

**Layer 6 (Visualization)** - Partially:
- Story 6.1: Streamlit Main App (CSV loading validation)

---

## Success Criteria

✅ All integration tests pass consistently  
✅ 80%+ code coverage achieved  
✅ End-to-end pipeline works without errors  
✅ CLI scripts can be executed programmatically  
✅ CSV export/import preserves all data  
✅ Cache behavior validated  
✅ Error handling tested and working  
✅ Test suite runs in < 2 minutes  
✅ Coverage report generated and reviewed  
✅ No critical gaps in test coverage identified

---

## Implementation Notes

### Mocking Strategy

- **External APIs**: Always mock (Google Places, LLM APIs) for reliability
- **File System**: Use pytest `tmp_path` fixture for temporary directories
- **Time/Dates**: Mock datetime for reproducible tests
- **Internal Components**: Use real implementations (no mocking)

### Test Isolation

- Each test should be independent
- Clean up temporary files after tests
- Reset cache directory between tests
- Don't rely on test execution order

### Test Data

- Use realistic sample data based on actual Algarve facilities
- Include edge cases (missing data, boundary values, etc.)
- Create fixtures that can be reused across tests

### Debugging Failed Tests

- Use `pytest -v -s` to see print statements
- Use `pytest --pdb` to drop into debugger on failure
- Generate HTML coverage report to identify gaps

### Required Testing Packages

Add to project dependencies:
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-benchmark>=4.0.0     # For performance benchmarking
pytest-mock>=3.11.0         # For mocking helpers
```

---

## Documentation Requirements

- Add docstrings to all test functions explaining what they test
- Document mock data format and expectations
- Include examples of running tests in README
- Document coverage requirements and how to check them


