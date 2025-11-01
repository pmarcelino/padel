# Story 5.2: Data Processing CLI

**Priority**: P0 (Critical Path)  
**Dependencies**: Stories 4.1, 4.2, 4.3  
**Estimated Effort**: Small  
**Layer**: 5 (CLI & Orchestration)

---

## Description

Create a CLI script to process collected facility data and calculate analytics. This script orchestrates all analysis components to transform raw data into actionable insights with opportunity scores.

---

## Input Contract

- **File**: `data/raw/facilities.csv`
- **Format**: CSV with Facility model fields
- **Required Fields**: 
  - place_id, name, address, city
  - latitude, longitude
  - rating, review_count
  - All other Facility model fields

---

## Output Contract

### Files Created:
1. **`data/processed/facilities.csv`**
   - Cleaned facility data (copy from raw)
   - Ready for visualization

2. **`data/processed/city_stats.csv`**
   - One row per city
   - All CityStats model fields including:
     - total_facilities, avg_rating, median_rating
     - population, facilities_per_capita
     - avg_distance_to_nearest
     - opportunity_score and all component weights

---

## Script Behavior

The script should execute the following steps in order:

### 1. Load Raw Data
- Read `data/raw/facilities.csv`
- Convert to list of `Facility` objects
- Display count of loaded facilities

### 2. Aggregate by City
- Use `CityAggregator` to group facilities by city
- Calculate city-level statistics
- Display count of cities analyzed

### 3. Calculate Geographic Metrics
- Use `DistanceCalculator` for each city
- Calculate `avg_distance_to_nearest` (distance to nearest facility in neighboring cities)
- Update `CityStats` objects with distance data

### 4. Calculate Opportunity Scores
- Use `OpportunityScorer` to calculate normalized scores
- Apply scoring formula:
  - Population weight (20%)
  - Saturation weight (30%, inverted)
  - Quality gap weight (20%, inverted)
  - Geographic gap weight (30%)
- Final scores: 0-100 scale
- **Graceful degradation**: If population data is missing for a city, default population_weight to 0.5 (neutral)

### 5. Sort Results
- Sort cities by opportunity_score (descending)
- Highest opportunity cities appear first

### 6. Save Processed Data
- Create `data/processed/` directory if needed
- Save facilities CSV
- Save city_stats CSV
- Use proper CSV formatting (headers, no index)

### 7. Display Summary
- Print processing summary
- Show top 5 cities with:
  - City name
  - Opportunity score
  - Number of facilities
  - Average rating
  - Population

---

## Acceptance Criteria

- [x] **Load from CSV**: Successfully reads raw facilities CSV and converts to Facility objects
- [x] **Call all analyzers in sequence**: Properly orchestrates CityAggregator, DistanceCalculator, and OpportunityScorer
- [x] **Display top 5 cities**: Prints formatted summary of highest opportunity cities
- [x] **Save processed data**: Creates both output CSV files in `data/processed/`
- [x] **Error handling**: Gracefully handles missing raw data file with helpful error message
- [x] **Progress logging**: Prints clear status messages for each step
- [x] **Runnable**: Executable via `python scripts/process_data.py`
- [x] **Performance**: Completes processing in under 2 minutes for typical dataset (50-100 facilities)

---

## Files to Create

```
scripts/
└── process_data.py         # Main processing script
```

---

## API Surface

The script uses these components (already implemented in dependencies):

```python
# From Story 4.1
from src.analyzers.aggregator import CityAggregator
aggregator = CityAggregator()
city_stats = aggregator.aggregate(facilities: List[Facility]) -> List[CityStats]

# From Story 4.2
from src.analyzers.distance import DistanceCalculator
distance_calc = DistanceCalculator()
distance = distance_calc.calculate_distance_to_nearest(city: str, facilities: List[Facility]) -> float

# From Story 4.3
from src.analyzers.scorer import OpportunityScorer
scorer = OpportunityScorer()
scored_stats = scorer.calculate_scores(city_stats: List[CityStats]) -> List[CityStats]

# From Story 0.1
from src.models.facility import Facility
from src.models.city import CityStats

# From Story 0.2
from src.config import settings
```

---

## Example Output

```
📊 Starting Data Processing
============================================================

1. Loading raw data...
   Loaded 67 facilities

2. Aggregating by city...
   15 cities analyzed

3. Calculating geographic metrics...
   Distance calculations complete

4. Computing opportunity scores...
   Opportunity scores calculated

5. Saving processed data...
   ✓ Saved: data/processed/facilities.csv
   ✓ Saved: data/processed/city_stats.csv

✅ Processing complete!

Top 5 Cities by Opportunity Score:
------------------------------------------------------------
1. Lagos: 78.3/100
   Facilities: 4, Avg Rating: 3.80⭐, Population: 31,049

2. Portimão: 72.1/100
   Facilities: 8, Avg Rating: 4.10⭐, Population: 59,896

3. Tavira: 68.5/100
   Facilities: 3, Avg Rating: 4.00⭐, Population: 26,167

4. Albufeira: 65.2/100
   Facilities: 12, Avg Rating: 4.30⭐, Population: 42,388

5. Faro: 61.8/100
   Facilities: 15, Avg Rating: 4.50⭐, Population: 64,560

Next step: streamlit run app/app.py
```

---

## Error Handling

### Missing Raw Data File
```
❌ Error: Raw data not found at data/raw/facilities.csv
Please run the data collection script first:
  python scripts/collect_data.py
```

### Invalid Data Format
```
❌ Error: Invalid facility data in CSV
Expected columns: place_id, name, address, city, latitude, longitude, ...
```

### Empty Dataset
```
⚠️  Warning: No facilities found in raw data
Processing cannot continue with empty dataset
```

---

## Testing Considerations

While the story doesn't require writing tests, the implementation should be testable:

- Mock `pd.read_csv()` for testing
- Test with sample fixture data
- Verify CSV output format
- Test error handling paths
- Validate score calculations match expected results

---

## Implementation Notes

1. **Path Management**: Use `settings.raw_data_dir` and `settings.processed_data_dir` from config
2. **Data Conversion**: Handle datetime fields when loading from CSV (ISO format strings)
3. **Pandas Integration**: Use `CityStats.model_dump()` (Pydantic v2) or similar for DataFrame conversion
4. **Progress Feedback**: Print after each major step for user visibility
5. **Directory Creation**: Use `mkdir(parents=True, exist_ok=True)` to ensure output directory exists
6. **Missing Population Data**: OpportunityScorer should gracefully handle cities without population data by defaulting their population_weight to 0.5 (see Story 4.3 edge case handling)

---

## Definition of Done

- [x] Script runs successfully from command line
- [x] Processes sample dataset without errors
- [x] Generates both required output files
- [x] Output CSVs have correct schema
- [x] Top 5 cities displayed with proper formatting
- [x] Error messages are clear and actionable
- [x] Code follows project style guidelines (type hints, docstrings)
- [x] Integration verified with downstream Story 6.1 (Streamlit app can load the output files)

