# Story 9.5: Robust Normalization (Optional)

## Overview
**Priority**: P2 (Optional Enhancement - Future Consideration)  
**Dependencies**: Story 4.3 (Opportunity Scorer)  
**Estimated Effort**: Medium  
**Layer**: 4 (Analysis) - Enhancement

## Problem Statement

Current normalization uses min-max scaling:

```python
normalized_value = (value - min) / (max - min + epsilon)
```

**Issue: Sensitivity to Outliers**

If Loulé has 72,162 population and all other cities are <20,000, the min-max normalization compresses all smaller cities to near-zero population weights.

**Example:**
- Loulé: 72,162 → weight = 1.0
- Albufeira: 42,388 → weight = 0.55
- Monchique: 5,958 → weight = 0.02

The problem: One large outlier (Loulé) dominates the normalization, making smaller cities' population differences invisible.

## Description

**OPTIONAL STORY** - Consider implementing robust normalization that is less sensitive to outliers. This uses percentile-based scaling or IQR (Interquartile Range) instead of min/max.

**Note:** With only 15 Algarve cities that are reasonably distributed, min-max is probably fine for the MVP. This story is for future consideration if weird scores emerge where one big city dominates all rankings.

## Contracts

### API Surface (Proposed)

```python
class OpportunityScorer:
    """Calculate opportunity scores for cities."""
    
    # Normalization strategy: "minmax" or "robust"
    NORMALIZATION_STRATEGY = "minmax"  # Default: existing behavior
    
    def _normalize_value(
        self, 
        value: float, 
        all_values: List[float],
        method: str = "minmax"
    ) -> float:
        """
        Normalize a value using specified method.
        
        Methods:
        - "minmax": Standard min-max normalization (current)
        - "robust": Percentile-based normalization (less sensitive to outliers)
        
        Args:
            value: Value to normalize
            all_values: All values for context
            method: Normalization method ("minmax" or "robust")
            
        Returns:
            Normalized value between 0-1
        """
        pass
```

## Requirements

### Robust Normalization Approach

**Method 1: Percentile Clipping**
```python
def _normalize_robust(value: float, all_values: List[float]) -> float:
    """
    Normalize using percentile-based clipping.
    
    - Clip values to 5th-95th percentile range
    - Then apply min-max normalization
    - Reduces impact of extreme outliers
    """
    p5 = np.percentile(all_values, 5)
    p95 = np.percentile(all_values, 95)
    clipped_value = np.clip(value, p5, p95)
    clipped_values = np.clip(all_values, p5, p95)
    
    min_val = clipped_values.min()
    max_val = clipped_values.max()
    return (clipped_value - min_val) / (max_val - min_val + 1e-6)
```

**Method 2: IQR-Based Scaling**
```python
def _normalize_iqr(value: float, all_values: List[float]) -> float:
    """
    Normalize using Interquartile Range (IQR).
    
    - Uses median and IQR instead of min/max
    - More robust to outliers
    """
    q1 = np.percentile(all_values, 25)
    q3 = np.percentile(all_values, 75)
    iqr = q3 - q1
    median = np.median(all_values)
    
    normalized = (value - median) / (iqr + 1e-6)
    # Scale to 0-1 range (with clipping)
    return np.clip((normalized + 2) / 4, 0, 1)  # Assumes most values within 2*IQR
```

### When to Use

**Use robust normalization if:**
1. One city has population >>2x the next largest
2. Opportunity scores are dominated by a single metric
3. Stakeholders complain that "only Loulé ever scores high"
4. Small cities show no differentiation in scores

**Keep min-max normalization if:**
1. All 15 cities are reasonably distributed (current state)
2. Scores make intuitive sense
3. No complaints about outlier dominance

## Acceptance Criteria

**If Implemented:**
- [ ] Add `NORMALIZATION_STRATEGY` configurable option
- [ ] Implement `_normalize_robust()` or `_normalize_iqr()` method
- [ ] Default to "minmax" (no behavior change unless configured)
- [ ] Allow per-metric configuration (robust for population, minmax for others)
- [ ] Unit tests verify robust normalization works correctly
- [ ] Unit tests compare minmax vs robust on sample data
- [ ] Documentation explains when to use each method
- [ ] Configuration via environment variable or config file

**For MVP (Not Implementing):**
- [ ] Document this story as future consideration
- [ ] Add monitoring/logging to detect if one city dominates scores
- [ ] Set up alert threshold: "If one city scores >90 and all others <50, consider robust normalization"

## Files to Modify (If Implemented)

```
src/analyzers/
└── scorer.py              # Add robust normalization methods

src/config.py              # Add NORMALIZATION_STRATEGY config

tests/test_analyzers/
└── test_scorer.py         # Test robust normalization
```

## Test Requirements (If Implemented)

### Unit Tests

**Robust Normalization:**
- [ ] Test percentile clipping with outlier dataset
- [ ] Test IQR scaling with outlier dataset
- [ ] Compare minmax vs robust on same dataset
- [ ] Verify robust reduces outlier impact

**Edge Cases:**
- [ ] Test with no outliers (both methods should be similar)
- [ ] Test with extreme outliers (10x difference)
- [ ] Test with all same values (should default to 0.5)
- [ ] Test with 2 values only

**Configuration:**
- [ ] Test strategy can be set via config
- [ ] Test per-metric strategy configuration
- [ ] Test invalid strategy raises error

## Technical Notes

### Current Algarve Distribution

Population distribution (2021):
- **Loulé**: 72,162 (max)
- **Faro**: 64,560
- **Portimão**: 59,896
- **Olhão**: 45,396
- **Albufeira**: 42,388
- ... (others 5,000-40,000)

**Analysis:** Loulé is only ~1.1x larger than Faro, not a dramatic outlier. Min-max normalization is likely fine for MVP.

### When Robust Normalization Helps

**Example with extreme outlier:**
```
Cities: [5000, 6000, 7000, 8000, 200000]  # One huge city

Min-Max Normalization:
- 5000 → 0.00
- 6000 → 0.005
- 7000 → 0.01
- 8000 → 0.015
- 200000 → 1.00
(Small cities compressed to near-zero)

Robust Normalization (IQR):
- 5000 → 0.2
- 6000 → 0.4
- 7000 → 0.6
- 8000 → 0.8
- 200000 → 1.00
(Better differentiation among smaller cities)
```

### Performance Considerations

- Robust normalization requires percentile calculations (O(n log n))
- For 15 cities, performance difference is negligible (<1ms)
- Could matter if expanding to hundreds of cities

## Example Usage (If Implemented)

```python
from src.analyzers.scorer import OpportunityScorer
from src.config import Config

# Default: min-max normalization
scorer = OpportunityScorer()
scores = scorer.calculate_scores(city_stats)

# Enable robust normalization
Config.NORMALIZATION_STRATEGY = "robust"
scorer = OpportunityScorer()
scores = scorer.calculate_scores(city_stats)

# Per-metric configuration
scorer = OpportunityScorer(
    population_normalization="robust",  # Use robust for population
    saturation_normalization="minmax",  # Use minmax for others
)
```

## Decision Criteria

**Implement this story if:**
1. After implementing Stories 9.1-9.4, you notice opportunity scores are dominated by population
2. Small cities (5,000-10,000 pop) all get nearly identical low scores
3. Stakeholders request better differentiation among smaller cities
4. Expanding analysis beyond Algarve to regions with more outliers

**Skip this story if:**
1. Current scores make intuitive sense
2. Good differentiation among all 15 cities
3. No complaints about outlier dominance
4. Focus on shipping MVP quickly

## Success Criteria (If Implemented)

This story is considered complete when:
1. Robust normalization methods implemented
2. Configurable via environment variable or config file
3. Default behavior unchanged (min-max)
4. All acceptance criteria met
5. Test coverage ≥ 90%
6. Documentation explains when to use each method
7. Scores validated with both methods on real data

## Related Stories

**Dependencies:**
- Story 4.3: Opportunity Scorer (must modify normalization methods)

**Related:**
- Story 9.4: Step-Based Geographic Gap (another normalization improvement)
- Story 0.2: Configuration Management (for strategy configuration)

**Future:**
- Could apply to other regions with more extreme distributions
- Could apply to other metrics (facility density, review counts)

## Business Impact (If Implemented)

**Improved Scoring:**
- Better differentiation among smaller cities
- Less dominance by large cities
- More balanced opportunity identification

**Risk:**
- Adds complexity to scoring algorithm
- Harder to explain to stakeholders
- May not be needed for Algarve dataset

**Recommendation:** Monitor scores after implementing Stories 9.1-9.4. If Loulé/Faro dominate all rankings, revisit this story. Otherwise, mark as "not needed for MVP."

