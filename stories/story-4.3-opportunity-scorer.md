# Story 4.3: Opportunity Scorer

## Overview
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1, 4.1, 4.2  
**Estimated Effort**: Medium  
**Layer**: 4 (Analysis)

## Description
Calculate opportunity scores for cities based on multiple weighted factors. The scorer normalizes various city metrics (population, saturation, quality gaps, and geographic gaps) into a unified 0-100 score that helps identify the most promising locations for new padel facilities.

## Contracts

### Input Contract
- `city_stats: List[CityStats]` - List of city statistics with distances already calculated
  - Must include: `population`, `facilities_per_capita`, `avg_rating`, `avg_distance_to_nearest`
  - These fields are populated by previous stories (4.1 and 4.2)

### Output Contract
- `List[CityStats]` - Same list with opportunity scores calculated
  - Each `CityStats` object will have:
    - `population_weight: float` (0-1)
    - `saturation_weight: float` (0-1)
    - `quality_gap_weight: float` (0-1)
    - `geographic_gap_weight: float` (0-1)
    - `opportunity_score: float` (0-100)

## API Surface

```python
class OpportunityScorer:
    """Calculate opportunity scores for cities."""
    
    # Formula weights (must sum to 1.0)
    POPULATION_WEIGHT_FACTOR = 0.2
    SATURATION_WEIGHT_FACTOR = 0.3
    QUALITY_GAP_WEIGHT_FACTOR = 0.2
    GEOGRAPHIC_GAP_WEIGHT_FACTOR = 0.3
    
    def __init__(self):
        """Initialize scorer and validate formula weights."""
        # Validate that weights sum to 1.0
        total = (
            self.POPULATION_WEIGHT_FACTOR +
            self.SATURATION_WEIGHT_FACTOR +
            self.QUALITY_GAP_WEIGHT_FACTOR +
            self.GEOGRAPHIC_GAP_WEIGHT_FACTOR
        )
        if not (0.9999 <= total <= 1.0001):  # Allow tiny floating point errors
            raise ValueError(f"Formula weights must sum to 1.0, got {total}")
    
    def calculate_scores(self, city_stats: List[CityStats]) -> List[CityStats]:
        """
        Calculate opportunity scores using normalized weights.
        
        Formula:
        Opportunity Score = (Population Weight × 0.2) 
                          + (Low Saturation Weight × 0.3)
                          + (Quality Gap Weight × 0.2)
                          + (Geographic Gap Weight × 0.3)
        
        Args:
            city_stats: List of CityStats with metrics populated
            
        Returns:
            Same list with scores calculated
        """
        pass
    
    def _normalize_population(self, value: float, all_values: List[float]) -> float:
        """
        Normalize population (higher is better).
        
        Args:
            value: Population for a specific city
            all_values: All population values for normalization
            
        Returns:
            Normalized value between 0-1 (higher population = higher score)
        """
        pass
    
    def _normalize_saturation(self, value: float, all_values: List[float]) -> float:
        """
        Normalize saturation (lower is better - inverted).
        
        Args:
            value: Facilities per capita for a specific city
            all_values: All saturation values for normalization
            
        Returns:
            Normalized value between 0-1 (lower saturation = higher score)
        """
        pass
    
    def _normalize_quality_gap(self, value: float, all_values: List[float]) -> float:
        """
        Normalize quality gap (lower rating = higher opportunity - inverted).
        
        Args:
            value: Average rating for a specific city
            all_values: All rating values for normalization
            
        Returns:
            Normalized value between 0-1 (lower rating = higher opportunity)
        """
        pass
    
    def _normalize_geographic_gap(self, value: float) -> float:
        """
        Normalize geographic gap (larger distance = higher opportunity).
        
        Args:
            value: Average distance to nearest facility (km)
            
        Returns:
            Normalized value between 0-1 (larger distance = higher score, capped at 20km)
        """
        pass
```

## Requirements

### Opportunity Score Calculation

The opportunity score is calculated using a weighted formula with four components:

1. **Population Weight (20%)**: Higher population = more potential customers
   - Normalized from all city populations
   - Higher is better
   - Range: 0-1

2. **Saturation Weight (30%)**: Lower facilities per capita = less competition
   - Calculated as `facilities_per_capita` (facilities per 10,000 residents)
   - **Inverted**: Lower saturation = higher score
   - Range: 0-1

3. **Quality Gap Weight (20%)**: Lower average rating = room for quality differentiation
   - Based on `avg_rating` of existing facilities
   - **Inverted**: Lower rating = higher opportunity
   - Range: 0-1

4. **Geographic Gap Weight (30%)**: Larger distance to competitors = geographic opportunity
   - Based on `avg_distance_to_nearest` (km)
   - Higher distance = higher score
   - Capped at 20km maximum
   - Range: 0-1

**Final Formula:**
```
opportunity_score = (
    population_weight * 0.2 +
    saturation_weight * 0.3 +
    quality_gap_weight * 0.2 +
    geographic_gap_weight * 0.3
) * 100
```

### Normalization Strategy

All weights must be normalized to 0-1 range using min-max normalization:

```
normalized_value = (value - min) / (max - min + epsilon)
```

Where:
- `min`: Minimum value across all cities
- `max`: Maximum value across all cities
- `epsilon`: Small constant (1e-6) to avoid division by zero

**Inverted metrics** (saturation and quality gap) should be normalized then inverted:
```
inverted_weight = 1 - normalized_value
```

### Edge Cases

1. **Missing Data**: If a metric is None or unavailable, default weight to 0.5 (neutral)
2. **Single City**: If only one city, all weights default to 0.5
3. **Zero Variance**: If all cities have the same value, default weight to 0.5
4. **Division by Zero**: Use epsilon (1e-6) to prevent division errors

## Acceptance Criteria

- [ ] `OpportunityScorer` class implemented
- [ ] `calculate_scores()` method normalizes all four weight components
- [ ] Population weight normalized correctly (higher population = higher weight)
- [ ] Saturation weight normalized and inverted (lower saturation = higher weight)
- [ ] Quality gap weight normalized and inverted (lower rating = higher weight)
- [ ] Geographic gap weight normalized correctly (larger distance = higher weight)
- [ ] Geographic gap capped at 20km maximum
- [ ] Final opportunity score is between 0-100
- [ ] All individual weights are between 0-1
- [ ] Edge cases handled (None values, single city, zero variance)
- [ ] **Formula weights (0.2, 0.3, 0.2, 0.3) sum to 1.0 and are validated at class level**
- [ ] **Weight validation ensures formula weights sum exactly to 1.0**
- [ ] Formula weights match specification (0.2, 0.3, 0.2, 0.3)
- [ ] Method calls `CityStats.calculate_opportunity_score()` to set final score
- [ ] Unit tests validate score calculations
- [ ] Unit tests cover all edge cases
- [ ] **Unit test verifies weight sum validation**

## Files to Create

```
src/analyzers/
├── __init__.py
└── scorer.py              # OpportunityScorer class

tests/test_analyzers/
├── __init__.py
└── test_scorer.py         # OpportunityScorer tests
```

## Test Requirements

### Unit Tests (`test_scorer.py`)

**Basic Functionality:**
- [ ] Test opportunity score calculation with valid data
- [ ] Test final score is between 0-100
- [ ] Test all weights are between 0-1
- [ ] Test formula weights are correct (0.2, 0.3, 0.2, 0.3)
- [ ] **Test formula weights sum to 1.0 at initialization**
- [ ] **Test ValueError is raised if weights don't sum to 1.0**

**Normalization Tests:**
- [ ] Test population normalization (higher = higher weight)
- [ ] Test saturation normalization and inversion (lower = higher weight)
- [ ] Test quality gap normalization and inversion (lower = higher weight)
- [ ] Test geographic gap normalization (higher = higher weight)
- [ ] Test geographic gap capped at 20km

**Edge Cases:**
- [ ] Test with None values (defaults to 0.5)
- [ ] Test with single city (all weights = 0.5)
- [ ] Test with zero variance (all same values → weights = 0.5)
- [ ] Test with empty list
- [ ] Test division by zero protection

**Integration with CityStats:**
- [ ] Test that `calculate_opportunity_score()` is called on each CityStats
- [ ] Test that weights are properly set on CityStats objects
- [ ] Test that opportunity_score is properly set

**Realistic Scenarios:**
- [ ] Test with sample Algarve data (varied populations, ratings)
- [ ] Test ranking: high population + low saturation = high score
- [ ] Test ranking: low rating + far distance = high score
- [ ] Test ranking: high saturation + high rating = low score

## Technical Notes

### Normalization Formula

Min-max normalization:
```python
def normalize(value, values):
    if not values or value is None:
        return 0.5
    min_val = min(values)
    max_val = max(values)
    if max_val - min_val < 1e-6:  # No variance
        return 0.5
    return (value - min_val) / (max_val - min_val + 1e-6)
```

### Weight Interpretation

**High Opportunity Indicators:**
- Large population (more potential customers)
- Low facilities per capita (less competition)
- Low average ratings (quality gap to exploit)
- Far from existing facilities (geographic gap)

**Low Opportunity Indicators:**
- Small population (fewer potential customers)
- High facilities per capita (saturated market)
- High average ratings (hard to compete on quality)
- Close to existing facilities (crowded market)

### Performance Considerations

- The scorer operates on a small dataset (~15 cities in Algarve)
- No caching needed
- O(n) complexity where n = number of cities
- Should complete in <1ms

## Example Usage

```python
from src.analyzers.scorer import OpportunityScorer
from src.models.city import CityStats

# Sample city stats (after aggregation and distance calculation)
city_stats = [
    CityStats(
        city="Albufeira",
        total_facilities=10,
        avg_rating=4.0,
        median_rating=4.0,
        total_reviews=1000,
        center_lat=37.0,
        center_lng=-8.0,
        population=42388,
        facilities_per_capita=2.36,  # 10 / 42388 * 10000
        avg_distance_to_nearest=5.0
    ),
    CityStats(
        city="Faro",
        total_facilities=15,
        avg_rating=4.5,
        median_rating=4.5,
        total_reviews=1500,
        center_lat=37.0,
        center_lng=-7.9,
        population=64560,
        facilities_per_capita=2.32,  # 15 / 64560 * 10000
        avg_distance_to_nearest=3.0
    ),
    CityStats(
        city="Monchique",
        total_facilities=1,
        avg_rating=3.5,
        median_rating=3.5,
        total_reviews=50,
        center_lat=37.3,
        center_lng=-8.5,
        population=5958,
        facilities_per_capita=1.68,  # 1 / 5958 * 10000
        avg_distance_to_nearest=15.0
    )
]

# Calculate opportunity scores
scorer = OpportunityScorer()
scored_stats = scorer.calculate_scores(city_stats)

# Results
for stats in scored_stats:
    print(f"{stats.city}: {stats.opportunity_score:.1f}/100")
    print(f"  Population: {stats.population_weight:.2f}")
    print(f"  Saturation: {stats.saturation_weight:.2f}")
    print(f"  Quality Gap: {stats.quality_gap_weight:.2f}")
    print(f"  Geographic Gap: {stats.geographic_gap_weight:.2f}")
```

**Expected Behavior:**
- Monchique should score high (low saturation, low rating, far distance)
- Faro might score medium (high population, but saturated and high ratings)
- Scores should be intuitive and correlate with business opportunity

## Success Criteria

This story is considered complete when:
1. `OpportunityScorer` class is implemented with all methods
2. All acceptance criteria are met
3. Test coverage is 100%
4. All tests pass (including edge cases)
5. Scores are validated against realistic scenarios
6. Code follows Python best practices and PEP 8
7. Normalization logic is documented and correct
8. Final scores make intuitive business sense

## Related Stories

**Depends On:**
- Story 0.1: Data Models & Validation (needs CityStats model)
- Story 4.1: City Aggregator (provides population and rating metrics)
- Story 4.2: Distance Calculator (provides geographic gap metrics)

**Enables:**
- Story 5.2: Data Processing CLI (uses scorer to rank cities)
- Story 6.1: Streamlit Main App (displays opportunity scores)
- Story 6.3: Dashboard & Charts (visualizes opportunity scores)

**Related Documentation:**
- See Technical Design Document section 8.2 for detailed scoring algorithm
- See Technical Design Document section 5.2 for CityStats model specification

