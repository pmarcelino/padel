# Story 9.4: Step-Based Geographic Gap Normalization

## Overview
**Priority**: P1 (Enhancement - Nice to Have)  
**Dependencies**: Story 4.3 (Opportunity Scorer), Story 9.3 (Fix Distance Calculation)  
**Estimated Effort**: Small  
**Layer**: 4 (Analysis) - Enhancement

## Problem Statement

Currently, geographic gap normalization uses a continuous linear scale:

```python
def _normalize_geographic_gap(self, value: float) -> float:
    capped_value = min(value, 20.0)
    return capped_value / 20.0  # Continuous 0-1 scale
```

**Issues with Current Approach:**
- Continuous scale makes subtle distinctions that may not be meaningful
- Hard to explain: "This city scores 0.73 vs 0.68 for geographic gap"
- Doesn't match how people think about distance: "Is it close, medium, or far?"

**Preferred Approach:**
Use step-based buckets that are simpler and clearer for decision-making:
- **0-5 km** → 0.25 (low opportunity - close to existing facilities)
- **5-10 km** → 0.50 (medium opportunity - moderate distance)
- **10-20 km** → 0.75 (high opportunity - far from facilities)
- **>20 km** → 1.0 (very high opportunity - very far from facilities)

## Description

Replace the continuous linear normalization of geographic gap with a step-based function using distance buckets. This makes scoring easier to understand and aligns with how business decisions are made.

## Contracts

### Input Contract
- `value: float` - Average distance to nearest facility (km)

### Output Contract  
- `float` - Normalized geographic gap weight (0.25, 0.50, 0.75, or 1.0)

### API Surface (Updated)

```python
class OpportunityScorer:
    """Calculate opportunity scores for cities."""
    
    # Geographic gap distance buckets (km)
    GEOGRAPHIC_GAP_BUCKETS = {
        "close": (0, 5, 0.25),      # (min_km, max_km, weight)
        "medium": (5, 10, 0.50),
        "far": (10, 20, 0.75),
        "very_far": (20, float('inf'), 1.0),
    }
    
    def _normalize_geographic_gap(self, value: float) -> float:
        """
        Normalize geographic gap using step-based buckets.
        
        Args:
            value: Average distance to nearest facility (km)
            
        Returns:
            Normalized value: 0.25, 0.50, 0.75, or 1.0
        """
        pass
```

## Requirements

### Step Function Implementation

```python
def _normalize_geographic_gap(self, value: float) -> float:
    """
    Normalize geographic gap using step-based buckets.
    
    Distance buckets:
    - 0-5 km: 0.25 (close to facilities - low geographic opportunity)
    - 5-10 km: 0.50 (medium distance - medium opportunity)
    - 10-20 km: 0.75 (far from facilities - high opportunity)  
    - >20 km: 1.0 (very far - very high opportunity)
    
    Args:
        value: Average distance to nearest facility (km)
        
    Returns:
        Normalized value between 0.25 and 1.0 (discrete steps)
    """
    if value is None or value < 0:
        return 0.5  # Default for invalid values
    
    if value < 5:
        return 0.25
    elif value < 10:
        return 0.50
    elif value < 20:
        return 0.75
    else:  # value >= 20
        return 1.0
```

### Bucket Configuration

Make buckets configurable via class constants for easy tuning:

```python
GEOGRAPHIC_GAP_BUCKETS = {
    "close": (0, 5, 0.25),       # (min_km, max_km, weight)
    "medium": (5, 10, 0.50),
    "far": (10, 20, 0.75),
    "very_far": (20, float('inf'), 1.0),
}
```

### Edge Cases

1. **Negative distance**: Return default (0.5) - shouldn't happen but handle gracefully
2. **None/null distance**: Return default (0.5)
3. **Zero distance**: Return 0.25 (facility at city center)
4. **Very large distance** (>100km): Still returns 1.0 (capped at highest bucket)

## Acceptance Criteria

- [ ] `_normalize_geographic_gap()` uses step-based buckets
- [ ] 0-5 km returns 0.25
- [ ] 5-10 km returns 0.50
- [ ] 10-20 km returns 0.75
- [ ] ≥20 km returns 1.0
- [ ] Bucket thresholds are configurable via class constants
- [ ] Edge cases handled (None, negative, zero)
- [ ] Unit tests verify all bucket ranges
- [ ] Unit tests verify edge cases
- [ ] Documentation explains bucket rationale
- [ ] Update any existing tests that rely on continuous normalization

## Files to Modify

```
src/analyzers/
└── scorer.py              # OpportunityScorer._normalize_geographic_gap()

tests/test_analyzers/
└── test_scorer.py         # Update tests for step-based normalization
```

## Test Requirements

### Updated Unit Tests (`test_scorer.py`)

**Bucket Tests:**
- [ ] Test 0 km → 0.25
- [ ] Test 2.5 km → 0.25 (within 0-5 bucket)
- [ ] Test 4.99 km → 0.25 (edge of 0-5 bucket)
- [ ] Test 5.0 km → 0.50 (start of 5-10 bucket)
- [ ] Test 7.5 km → 0.50 (within 5-10 bucket)
- [ ] Test 9.99 km → 0.50 (edge of 5-10 bucket)
- [ ] Test 10.0 km → 0.75 (start of 10-20 bucket)
- [ ] Test 15.0 km → 0.75 (within 10-20 bucket)
- [ ] Test 19.99 km → 0.75 (edge of 10-20 bucket)
- [ ] Test 20.0 km → 1.0 (start of >20 bucket)
- [ ] Test 50.0 km → 1.0 (far beyond 20km)
- [ ] Test 100.0 km → 1.0 (very far)

**Edge Cases:**
- [ ] Test None → 0.5 (default)
- [ ] Test negative value (-5.0) → 0.5 (default)
- [ ] Test boundary precision (5.0 exactly, 10.0 exactly, 20.0 exactly)

**Integration:**
- [ ] Test opportunity score calculation with step-based geographic gaps
- [ ] Verify final scores are intuitive
- [ ] Compare before/after scores for sample cities

**Regression:**
- [ ] All other normalization methods unchanged
- [ ] Population, saturation, quality gap still use continuous normalization
- [ ] Test coverage remains ≥ 90%

## Technical Notes

### Why Step-Based?

**Advantages:**
1. **Simpler to explain**: "This city is 'far' from facilities" vs "This city scores 0.73"
2. **Matches decision-making**: Business decisions are bucket-based, not continuous
3. **Reduces noise**: Small distance variations (15.2km vs 16.8km) don't change score
4. **More stable**: Less sensitive to measurement precision

**Trade-offs:**
- Less granular distinction between cities in the same bucket
- For Algarve (small region), most cities will be in 0-10km range

### Alternative Bucket Schemes

Could consider different buckets if needed:
- Finer granularity: 0-3, 3-7, 7-15, >15km
- Coarser granularity: 0-10, 10-20, >20km
- Non-linear weights: 0.1, 0.4, 0.7, 1.0 (emphasize extremes)

Current scheme (0.25, 0.50, 0.75, 1.0) provides good balance for MVP.

### Impact on Opportunity Scores

**Before (Continuous):**
- City at 6km: geographic_gap_weight = 6/20 = 0.30
- City at 8km: geographic_gap_weight = 8/20 = 0.40
- City at 15km: geographic_gap_weight = 15/20 = 0.75

**After (Step-Based):**
- City at 6km: geographic_gap_weight = 0.50
- City at 8km: geographic_gap_weight = 0.50
- City at 15km: geographic_gap_weight = 0.75

Cities in the 5-10km range will score **higher** than before (0.50 vs 0.30-0.50).

## Example Usage

```python
from src.analyzers.scorer import OpportunityScorer

scorer = OpportunityScorer()

# Test different distances
print(scorer._normalize_geographic_gap(3.0))   # 0.25 (close)
print(scorer._normalize_geographic_gap(7.5))   # 0.50 (medium)
print(scorer._normalize_geographic_gap(15.0))  # 0.75 (far)
print(scorer._normalize_geographic_gap(25.0))  # 1.0 (very far)

# Use in full scoring
city_stats = aggregator.aggregate(facilities)
city_stats = distance_calc.calculate_distances(city_stats, facilities)
city_stats = scorer.calculate_scores(city_stats)

for stats in city_stats:
    print(f"{stats.city}: distance={stats.avg_distance_to_nearest:.1f}km, "
          f"gap_weight={stats.geographic_gap_weight:.2f}")
# Output:
# Albufeira: distance=3.2km, gap_weight=0.25
# Monchique: distance=15.8km, gap_weight=0.75
# Vila do Bispo: distance=22.0km, gap_weight=1.00
```

## Success Criteria

This story is considered complete when:
1. Geographic gap normalization uses step-based buckets
2. All bucket ranges work correctly
3. All acceptance criteria met
4. Test coverage ≥ 90%
5. All tests pass
6. Opportunity scores are intuitive and explainable
7. Documentation updated with bucket rationale

## Related Stories

**Dependencies:**
- Story 4.3: Opportunity Scorer (must modify _normalize_geographic_gap method)
- Story 9.3: Fix Distance Calculation (ensures accurate distances before bucketing)

**Related:**
- Story 9.5: Robust Normalization (optional enhancement to other normalizations)

**Impacts:**
- Opportunity scores will change slightly (expected)
- Cities in 5-10km range will score higher (more appropriate)
- Score explanations become simpler ("far" vs "0.73")

## Business Impact

**Improved Decision-Making:**
- Clear categories: "close, medium, far, very far"
- Easier to explain to stakeholders
- Aligns with how people think about distance

**Score Stability:**
- Less sensitive to small measurement variations
- More robust to data quality issues
- Consistent scoring for cities in same distance range

**Example:**
- **Before**: "City A scores 68.3 and City B scores 71.2"
- **After**: "Both cities are 'medium distance' from facilities, scoring similarly"

