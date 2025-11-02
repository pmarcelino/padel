# Story 9.0: Opportunity Score Model Improvements - Overview

## Overview
**Priority**: P0 (Critical - Bug Fix Epic)  
**Dependencies**: Stories 4.1, 4.2, 4.3  
**Estimated Effort**: Large (Epic consisting of 5 sub-stories)  
**Layer**: 4 (Analysis) - Improvements

## Problem Statement

The current opportunity score model has critical bugs that cause it to miss the **biggest opportunities** - cities with high population and zero facilities. These issues make the analysis incomplete and misleading.

### Critical Issues Identified

1. **Zero-Facility Cities Are Invisible** (Story 9.1)
   - Cities without facilities never appear in analysis
   - Example: Monchique (5,958 pop, 0 facilities) is completely missing
   - You only analyze cities that already have facilities
   - **Impact**: Missing greenfield opportunities

2. **No City Center Coordinates** (Story 9.2)
   - City centers calculated from facility locations (doesn't work for zero-facility cities)
   - Need actual city center coordinates for proper distance calculations
   - **Impact**: Can't calculate distances for zero-facility cities

3. **Distance Calculation Fails** (Story 9.3)
   - Zero-facility cities return `distance = 0.0` (wrong)
   - Should calculate distance from city center to nearest facility anywhere
   - **Impact**: Geographic gap scores are backwards for underserved cities

4. **Geographic Gap Uses Continuous Scale** (Story 9.4)
   - Current: 0-20km mapped linearly to 0-1
   - Preferred: Step-based buckets (0-5km, 5-10km, 10-20km, >20km)
   - **Impact**: Harder to explain, doesn't match decision-making

5. **Normalization Sensitive to Outliers** (Story 9.5 - Optional)
   - Min-max normalization can be dominated by one large city
   - **Impact**: Potentially affects score distribution (monitor for MVP)

## Epic Structure

This epic consists of 5 stories:

### Story 9.1: Fix Zero-Facility Cities in Aggregation
**Priority: P0 (Critical)**
- Modify `CityAggregator` to produce `CityStats` for all 15 cities
- Ensure cities with zero facilities appear with correct zero/null values
- Dependency: Story 9.2

### Story 9.2: Add City Center Coordinates
**Priority: P0 (Critical)**
- Add `CITY_CENTERS` constant with actual city center coordinates
- Enable geographic analysis for zero-facility cities
- No dependencies (can start immediately)

### Story 9.3: Fix Distance Calculation for Zero-Facility Cities
**Priority: P0 (Critical)**
- Calculate distance from city center to nearest facility for zero-facility cities
- Fix incorrect `0.0` distance for underserved cities
- Dependencies: Stories 9.1, 9.2

### Story 9.4: Step-Based Geographic Gap Normalization
**Priority: P1 (Enhancement)**
- Replace continuous normalization with step-based buckets
- Simpler, clearer scores
- Dependency: Story 9.3

### Story 9.5: Robust Normalization (Optional)
**Priority: P2 (Optional)**
- Consider robust normalization to reduce outlier sensitivity
- Monitor MVP scores first; implement only if needed
- Dependency: Story 4.3

## Implementation Order

```
Phase 1 (Parallel):
├── Story 9.2: Add City Center Coordinates (no dependencies)

Phase 2 (After Phase 1):
├── Story 9.1: Fix Zero-Facility Cities (depends on 9.2)

Phase 3 (After Phase 2):
├── Story 9.3: Fix Distance Calculation (depends on 9.1, 9.2)

Phase 4 (After Phase 3):
├── Story 9.4: Step-Based Geographic Gap (depends on 9.3)

Phase 5 (Optional - After Validation):
└── Story 9.5: Robust Normalization (optional)
```

**Critical Path**: 9.2 → 9.1 → 9.3  
**Total Estimated Time**: 2-3 days for critical stories (9.1-9.3)

## Business Impact

### Before Fixes
- **Missing opportunities**: Zero-facility cities invisible
- **Incomplete analysis**: Only analyzing cities with existing facilities
- **Wrong scores**: Zero-facility cities scored as saturated (0.0 distance)
- **Confusing scores**: Continuous scales hard to explain

### After Fixes
- **All 15 cities visible**: Complete market coverage
- **Accurate scoring**: Zero-facility cities correctly identified as high-opportunity
- **Proper distance metrics**: "15km from nearest facility" instead of "0km"
- **Clear explanations**: "Far from facilities" instead of "0.73 geographic gap weight"

### Expected Outcome Examples

**Monchique (currently missing):**
- Population: 5,958
- Facilities: 0
- Distance to nearest: ~15km
- **Expected score**: High (low saturation, good population, far from competitors)

**Vila do Bispo (currently missing or scored wrong):**
- Population: 5,717
- Facilities: 0
- Distance to nearest: ~22km
- **Expected score**: Very high (zero facilities, far from all competitors)

## Acceptance Criteria for Epic

- [ ] All 15 Algarve cities appear in analysis results
- [ ] Zero-facility cities have correct stats (0 facilities, null ratings, 0.0 per capita)
- [ ] Zero-facility cities have accurate distance calculations (>0 km when facilities exist elsewhere)
- [ ] Geographic gap uses step-based normalization (0.25, 0.50, 0.75, 1.0)
- [ ] All existing tests still pass (no regression)
- [ ] New tests cover all edge cases
- [ ] Opportunity scores make intuitive business sense
- [ ] Documentation updated for all changes
- [ ] Test coverage remains ≥ 90%

## Test Strategy

### Integration Testing
After completing Stories 9.1-9.3, run full pipeline test:
- Input: Realistic facility dataset (mix of cities with/without facilities)
- Expected output: All 15 cities in results
- Validate: Zero-facility cities have correct stats and distances

### Validation Scenarios
1. **All 15 cities have facilities** → Should work as before (regression test)
2. **10 cities have facilities, 5 don't** → All 15 appear, correct stats for both groups
3. **0 cities have facilities** → All 15 appear with zero stats, distances all calculated

### Score Validation
Compare opportunity scores before/after:
- Zero-facility cities should score higher (now visible)
- Cities with facilities should have similar scores (minor changes only)
- Rankings should make intuitive business sense

## Files Affected

```
src/analyzers/
├── aggregator.py          # Stories 9.1, 9.2
├── distance.py            # Story 9.3
└── scorer.py              # Stories 9.4, 9.5

tests/test_analyzers/
├── test_aggregator.py     # Stories 9.1, 9.2
├── test_distance.py       # Story 9.3
└── test_scorer.py         # Stories 9.4, 9.5
```

## Risks & Mitigation

### Risk 1: Breaking Changes to Existing Code
**Mitigation**: 
- Extensive regression testing
- Maintain backward compatibility where possible
- Test coverage ≥ 90%

### Risk 2: Opportunity Scores Change Significantly
**Mitigation**: 
- Expected behavior (fixing bugs)
- Document score changes
- Validate scores make business sense before deploying

### Risk 3: Performance Degradation
**Mitigation**: 
- With only 15 cities and ~100-200 facilities, performance is not a concern
- All changes are O(n) or better
- Expected runtime: <10ms for entire pipeline

## Success Criteria

This epic is considered complete when:
1. All critical stories (9.1-9.3) are complete
2. All 15 Algarve cities appear in analysis
3. Zero-facility cities have accurate stats and distances
4. Opportunity scores are validated and make business sense
5. All tests pass with ≥ 90% coverage
6. No regressions in existing functionality
7. Documentation is updated
8. Story 9.4 is complete (step-based normalization)
9. Story 9.5 is evaluated (implement only if needed)

## Related Stories

**Dependencies (Must Be Complete First):**
- Story 4.1: City Aggregator
- Story 4.2: Distance Calculator
- Story 4.3: Opportunity Scorer

**Impacts:**
- Story 5.2: Data Processing CLI (will use improved scores)
- Story 6.1: Streamlit Main App (will display all cities)
- Story 6.2: Interactive Map Component (will show all cities)
- Story 6.3: Dashboard & Charts (will visualize improved scores)

## Next Steps

1. **Review this overview** with stakeholders
2. **Start with Story 9.2** (no dependencies, quick win)
3. **Proceed to Stories 9.1, 9.3** (critical path)
4. **Validate scores** after critical stories
5. **Implement Story 9.4** (enhancement)
6. **Evaluate Story 9.5** (optional, based on validation results)

## Notes

- This epic fixes critical bugs that make the analysis incomplete
- Zero-facility cities are the **biggest opportunities** but currently invisible
- Implementation is straightforward; main effort is in comprehensive testing
- Expected total time: 2-3 days for critical path (9.1-9.3)
- Stories 9.4-9.5 can be done later if needed to ship faster

---

**Last Updated**: Story planning based on opportunity score model analysis  
**Status**: Ready for implementation  
**Estimated Epic Completion**: 3-4 days (including optional stories)

