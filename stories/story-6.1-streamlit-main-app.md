# Story 6.1: Streamlit Main App Structure

## Overview

**Priority**: P0 (Critical Path)  
**Dependencies**: Story 5.2 (Data Processing CLI)  
**Estimated Effort**: Small (4-6 hours)  
**Layer**: 6 (Visualization)

## Description

Create the main Streamlit application structure that serves as the entry point for the Algarve Padel Market Research tool. This app will load processed data, provide filtering capabilities, display key metrics, and organize content into navigable tabs.

## Business Value

Provides users with an intuitive web interface to explore padel facility data and opportunity scores without requiring technical knowledge or command-line interaction.

## Input Contract

**Required Data Files**:
- `data/processed/facilities.csv` - Cleaned and deduplicated facility data
- `data/processed/city_stats.csv` - City-level aggregations with opportunity scores

**Expected CSV Schema**:

`facilities.csv`:
```
place_id, name, address, city, postal_code, latitude, longitude, 
rating, review_count, google_url, facility_type, num_courts, 
indoor_outdoor, phone, website, collected_at, last_updated
```

`city_stats.csv`:
```
city, total_facilities, avg_rating, median_rating, total_reviews,
center_lat, center_lng, population, facilities_per_capita,
avg_distance_to_nearest, opportunity_score, population_weight,
saturation_weight, quality_gap_weight, geographic_gap_weight
```

## Output Contract

**Deliverable**: Fully functional Streamlit web application

**Application Features**:
1. **Data Loading**: Cached data loading from CSV files
2. **Sidebar Filters**: 
   - Multi-select city filter
   - Minimum rating slider
3. **Key Metrics Dashboard**: 4-column metric display
4. **Tab Navigation**: Overview, Map, and Analysis tabs
5. **Error Handling**: Graceful handling of missing data files

**Launch Command**: `streamlit run app/app.py`

## Technical Requirements

### Page Configuration
```python
st.set_page_config(
    page_title="Algarve Padel Market Research",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### Data Loading Function
- Use `@st.cache_data` decorator for performance
- Load both facilities and city stats DataFrames
- Handle `FileNotFoundError` gracefully
- Display helpful error messages with next steps

### Sidebar Filters
1. **City Multi-Select**:
   - Options: All cities from `city_stats.csv`
   - Default: All cities selected
   - Label: "Select Cities"

2. **Rating Slider**:
   - Range: 0.0 to 5.0
   - Step: 0.5
   - Default: 0.0 (show all)
   - Label: "Minimum Rating"

### Key Metrics (4 Columns)
Display the following metrics in a row:
1. **Total Facilities**: Count of filtered facilities
2. **Average Rating**: Mean rating with ⭐ emoji
3. **Total Reviews**: Sum of review counts (formatted with commas)
4. **Top Opportunity**: City name with highest opportunity score

### Tab Navigation
Create three tabs:
1. **📊 Overview**: General statistics and summaries
2. **🗺️ Map**: Interactive map view (component from Story 6.2)
3. **📈 Analysis**: Charts and analytics (component from Story 6.3)

### Data Filtering Logic
Apply filters to both DataFrames:
- Filter facilities by selected cities AND minimum rating
- Filter city stats by selected cities only
- Recalculate metrics based on filtered data

## Acceptance Criteria

### Functional Requirements
- [ ] App loads successfully with valid data files
- [ ] Displays error message with instructions if data files are missing
- [ ] Sidebar filters update immediately when changed
- [ ] Key metrics recalculate based on active filters
- [ ] All three tabs render without errors
- [ ] App is responsive and maintains state across tab switches
- [ ] Data caching works (no reload on re-renders)

### Non-Functional Requirements
- [ ] Page load time < 2 seconds with cached data
- [ ] Clean, modern UI with consistent styling
- [ ] Wide layout utilizes full screen width
- [ ] Sidebar is expanded by default
- [ ] No console errors or warnings

### Code Quality
- [ ] Type hints for function parameters
- [ ] Docstrings for main functions
- [ ] Proper error handling with user-friendly messages
- [ ] Code follows Python style guidelines (Black formatting)

## Files to Create

```
app/
├── app.py                     # Main Streamlit application (NEW)
└── components/
    ├── __init__.py           # Package initializer (NEW)
    └── (map_view.py, dashboard.py to be added in later stories)
```

## Implementation Notes

### Stub Functions for Tabs

Since Stories 6.2 and 6.3 will implement the actual tab content, create placeholder functions that clearly indicate they're temporary:

```python
def render_overview(facilities_df, cities_df):
    """
    Render overview tab - TEMPORARY PLACEHOLDER.
    
    TODO: Implement in Story 6.3 (Dashboard & Charts)
    """
    st.info("📊 Overview dashboard will be implemented in Story 6.3")
    st.write("Preview of city data:")
    st.dataframe(cities_df.head())

def render_map(facilities_df, cities_df):
    """
    Render map tab - TEMPORARY PLACEHOLDER.
    
    TODO: Implement in Story 6.2 (Interactive Map Component)
    """
    st.info("🗺️ Interactive map will be implemented in Story 6.2")
    st.write(f"Will display {len(facilities_df)} facilities on map")

def render_analysis(cities_df):
    """
    Render analysis tab - TEMPORARY PLACEHOLDER.
    
    TODO: Implement in Story 6.3 (Dashboard & Charts)
    """
    st.info("📈 Analysis charts will be implemented in Story 6.3")
    st.write(f"Will show analytics for {len(cities_df)} cities")
```

**Alternative (More Strict)**:
```python
def render_overview(facilities_df, cities_df):
    """Placeholder - implemented in Story 6.3."""
    raise NotImplementedError("Overview rendering will be implemented in Story 6.3")
```

**Recommendation**: Use informational messages (first approach) for better UX during development. The app should be runnable even with placeholder content.

### Error Handling Example
```python
try:
    facilities_df, cities_df = load_data()
except FileNotFoundError:
    st.error("📁 Data not found. Please run data collection first.")
    st.code("python scripts/collect_data.py")
    st.code("python scripts/process_data.py")
    st.stop()
```

### Data Filtering Pattern
```python
filtered_facilities = facilities_df[
    (facilities_df['city'].isin(selected_cities)) &
    (facilities_df['rating'] >= min_rating)
]

filtered_cities = cities_df[cities_df['city'].isin(selected_cities)]
```

## Testing Strategy

### Manual Testing Checklist
- [ ] Run with valid data files present
- [ ] Run with missing data files (test error handling)
- [ ] Test city filter with single city selected
- [ ] Test city filter with no cities selected
- [ ] Test rating slider at different thresholds
- [ ] Verify metrics update correctly when filters change
- [ ] Navigate between all three tabs
- [ ] Refresh page and verify cache works
- [ ] Test on different screen sizes (desktop, tablet)

### Edge Cases to Handle
1. **No cities selected**: Display message "Please select at least one city"
2. **High rating threshold**: May result in 0 facilities, handle gracefully
3. **Empty CSV files**: Display appropriate error
4. **Malformed CSV**: Handle parsing errors
5. **Missing columns**: Validate expected schema

## Integration Points

### Depends On
- **Story 5.2**: Requires processed CSV files to exist
  - `data/processed/facilities.csv`
  - `data/processed/city_stats.csv`

### Enables
- **Story 6.2 (Map Component)**: Will integrate into "🗺️ Map" tab
- **Story 6.3 (Dashboard)**: Will integrate into "📈 Analysis" tab
- **Story 6.4 (Export)**: Will add export buttons to UI

## Definition of Done

- [ ] Code is written and committed
- [ ] App launches successfully with `streamlit run app/app.py`
- [ ] All acceptance criteria are met
- [ ] Manual testing checklist completed
- [ ] Error handling tested with missing files
- [ ] Code is formatted with Black
- [ ] Comments and docstrings added
- [ ] Screenshots of working app captured (optional)
- [ ] Ready for Stories 6.2 and 6.3 integration

## Future Enhancements (Out of Scope)

- Custom theming/branding
- User authentication
- Save filter preferences
- Downloadable reports from main page
- Multi-language support
- Mobile app version

## References

- Technical Design: Section 9.1 (Main App Structure)
- Streamlit Documentation: https://docs.streamlit.io/
- Related Stories: 6.2 (Map), 6.3 (Dashboard), 6.4 (Export)

