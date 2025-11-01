# Story 6.3: Dashboard & Charts

**Priority**: P1 (Nice to Have)  
**Dependencies**: Story 6.1 (Streamlit Main App Structure)  
**Estimated Effort**: Medium  
**Layer**: 6 (Visualization)

---

## Overview

Create an analytics dashboard with interactive Plotly charts to visualize padel facility data and city-level statistics. The dashboard should provide visual insights into market opportunities, facility distribution, and quality metrics across Algarve cities.

---

## User Story

**As a** market researcher or investor  
**I want** to visualize facility and city data through interactive charts  
**So that** I can quickly identify trends, patterns, and opportunities in the Algarve padel market

---

## Input Contract

```python
# Primary Input
city_stats_df: pd.DataFrame
# Columns: city, total_facilities, avg_rating, median_rating, total_reviews,
#          center_lat, center_lng, population, facilities_per_capita,
#          avg_distance_to_nearest, opportunity_score, population_weight,
#          saturation_weight, quality_gap_weight, geographic_gap_weight

# Secondary Input (for some charts)
facilities_df: pd.DataFrame
# Columns: place_id, name, address, city, rating, review_count, etc.
```

---

## Output Contract

Rendered Plotly charts within Streamlit interface, including:

1. **Bar Chart**: Facilities per city (sorted)
2. **Bar Chart**: Opportunity scores by city (color-coded)
3. **Scatter Plot**: Population vs. facilities per capita
4. **Pie Chart**: Rating distribution across all facilities
5. (Optional) **Box Plot**: Rating distribution by city
6. (Optional) **Histogram**: Review count distribution

---

## API Surface

```python
# app/components/dashboard.py

def render_overview(
    facilities_df: pd.DataFrame, 
    cities_df: pd.DataFrame
) -> None:
    """
    Render overview dashboard with key statistics and charts.
    
    Args:
        facilities_df: Filtered facilities dataframe
        cities_df: Filtered city statistics dataframe
    """
    pass

def create_facilities_bar_chart(cities_df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart of facilities per city.
    
    Args:
        cities_df: City statistics dataframe
        
    Returns:
        Plotly Figure object
    """
    pass

def create_opportunity_chart(cities_df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart of opportunity scores by city.
    Color-coded: green (high), yellow (medium), red (low)
    
    Args:
        cities_df: City statistics dataframe
        
    Returns:
        Plotly Figure object
    """
    pass

def create_population_saturation_scatter(cities_df: pd.DataFrame) -> go.Figure:
    """
    Create scatter plot: population vs facilities per capita.
    Shows saturation levels across different city sizes.
    
    Args:
        cities_df: City statistics dataframe
        
    Returns:
        Plotly Figure object
    """
    pass

def create_rating_distribution_pie(facilities_df: pd.DataFrame) -> go.Figure:
    """
    Create pie chart of rating distribution.
    Categories: 5 stars, 4-5 stars, 3-4 stars, <3 stars, No rating
    
    Args:
        facilities_df: Facilities dataframe
        
    Returns:
        Plotly Figure object
    """
    pass

def create_rating_boxplot_by_city(facilities_df: pd.DataFrame) -> go.Figure:
    """
    Optional: Create box plot of rating distributions by city.
    
    Args:
        facilities_df: Facilities dataframe
        
    Returns:
        Plotly Figure object
    """
    pass
```

---

## Acceptance Criteria

### Functional Requirements

- [ ] **Chart 1**: Bar chart showing total facilities per city
  - Sorted by facility count (descending)
  - Color-coded bars
  - Hover tooltips with exact counts
  
- [ ] **Chart 2**: Bar chart showing opportunity scores by city
  - Sorted by opportunity score (descending)
  - Color gradient: green (>70), yellow (40-70), red (<40)
  - Hover tooltips showing score breakdown

- [ ] **Chart 3**: Scatter plot of population vs saturation
  - X-axis: Population
  - Y-axis: Facilities per 10,000 people
  - Point size: total facilities
  - Hover tooltips with city name and metrics

- [ ] **Chart 4**: Pie chart of rating distribution
  - Segments: 5★, 4-5★, 3-4★, <3★, No rating
  - Percentage labels
  - Interactive legend

- [ ] All charts integrate with sidebar filters
  - Charts update when cities are selected/deselected
  - Charts update when min rating changes

- [ ] Responsive layout
  - Charts resize based on screen width
  - Mobile-friendly (readable on tablets)

- [ ] Interactive features
  - Hover tooltips with detailed information
  - Click to highlight/filter (if feasible)
  - Legend interactions

### Technical Requirements

- [ ] Use Plotly Express or Plotly Graph Objects
- [ ] Charts render within Streamlit using `st.plotly_chart()`
- [ ] Efficient rendering (< 2 seconds for all charts)
- [ ] Handle edge cases:
  - Empty dataframes (show "No data" message)
  - Single city selected
  - Missing values (NaN) in ratings

### UI/UX Requirements

- [ ] Consistent color scheme across all charts
- [ ] **Charts use accessible color palettes (colorblind-safe)**
- [ ] Clear axis labels and titles
- [ ] Readable font sizes
- [ ] Professional appearance
- [ ] Loading states for chart generation

### Optional Enhancements

- [ ] Export individual charts as PNG/HTML
- [ ] Download chart data as CSV
- [ ] Additional charts:
  - Review count histogram
  - Rating box plots by city
  - Indoor/outdoor distribution (if data available)
  - Trend analysis (if temporal data available)

---

## Chart Specifications

### 1. Facilities per City (Bar Chart)

**Purpose**: Show distribution of facilities across cities

**Visual Design**:
- Horizontal or vertical bars
- X-axis: City names
- Y-axis: Number of facilities
- Sort: Descending by count
- Color: Single color or gradient by count

**Hover Tooltip**:
```
City: Albufeira
Facilities: 10
% of Total: 15.2%
```

---

### 2. Opportunity Scores (Bar Chart)

**Purpose**: Highlight cities with highest market opportunity

**Visual Design**:
- Horizontal or vertical bars
- X-axis: City names
- Y-axis: Opportunity Score (0-100)
- Sort: Descending by score
- Color gradient:
  - Green: 70-100 (High opportunity)
  - Yellow: 40-69 (Medium opportunity)
  - Red: 0-39 (Low opportunity)

**Hover Tooltip**:
```
City: Lagos
Opportunity Score: 75.3/100

Breakdown:
• Population: 8.5/10
• Low Saturation: 9.2/10
• Quality Gap: 6.1/10
• Geographic Gap: 7.8/10
```

---

### 3. Population vs Saturation (Scatter Plot)

**Purpose**: Identify under-served cities by population size

**Visual Design**:
- X-axis: Population (log scale if needed)
- Y-axis: Facilities per 10,000 people
- Points: Circle markers
- Point size: Total facilities
- Point color: Opportunity score (gradient)

**Quadrants** (optional reference lines):
- Top-left: High pop, high saturation (mature market)
- Top-right: Low pop, high saturation (over-served)
- Bottom-left: High pop, low saturation (HIGH OPPORTUNITY)
- Bottom-right: Low pop, low saturation (niche market)

**Hover Tooltip**:
```
City: Faro
Population: 64,560
Facilities: 8
Per 10k people: 1.24
Opportunity Score: 68.5
```

---

### 4. Rating Distribution (Pie Chart)

**Purpose**: Show overall quality of facilities

**Visual Design**:
- Segments:
  - 5 stars (5.0)
  - 4-5 stars (4.0-4.9)
  - 3-4 stars (3.0-3.9)
  - <3 stars (<3.0)
  - No rating
- Colors: Green to red gradient
- Display: Percentages

**Hover Tooltip**:
```
Rating: 4-5 stars
Facilities: 25
Percentage: 42.3%
```

---

## Files to Create

```
app/components/dashboard.py       # Main dashboard component
```

**Optional**:
```
app/components/charts/            # Separate chart modules
├── __init__.py
├── facility_charts.py            # Facility-related charts
├── opportunity_charts.py         # Opportunity score charts
└── quality_charts.py             # Rating/quality charts
```

---

## Integration with Main App

The dashboard should be called from `app/app.py` in the Overview tab:

```python
# app/app.py (excerpt)

with tab1:  # Overview tab
    render_overview(filtered_facilities, filtered_cities)
```

---

## Testing Requirements

### Unit Tests

```python
# tests/test_components/test_dashboard.py

def test_facilities_bar_chart_creation(sample_cities_df):
    """Test bar chart creation with sample data."""
    fig = create_facilities_bar_chart(sample_cities_df)
    assert fig is not None
    assert len(fig.data) > 0

def test_opportunity_chart_colors(sample_cities_df):
    """Test color coding of opportunity scores."""
    fig = create_opportunity_chart(sample_cities_df)
    # Verify color assignments based on score ranges

def test_scatter_plot_with_missing_population(cities_df_missing_pop):
    """Test scatter plot handles missing population data."""
    fig = create_population_saturation_scatter(cities_df_missing_pop)
    # Should skip cities with missing population

def test_rating_pie_empty_data():
    """Test pie chart handles empty dataframe."""
    empty_df = pd.DataFrame()
    fig = create_rating_distribution_pie(empty_df)
    # Should return figure with "No data" message

def test_dashboard_renders_without_errors(sample_facilities_df, sample_cities_df):
    """Test main dashboard function executes."""
    # Mock streamlit functions
    render_overview(sample_facilities_df, sample_cities_df)
```

### Integration Tests

- [ ] Test chart rendering in Streamlit environment
- [ ] Test filter integration (sidebar filters update charts)
- [ ] Test performance with full dataset
- [ ] Visual regression testing (if applicable)

### Manual Testing Checklist

- [ ] All charts render correctly on page load
- [ ] Hover tooltips display accurate information
- [ ] Charts update when filters change
- [ ] Charts are responsive (resize browser window)
- [ ] Color scheme is consistent and accessible
- [ ] No console errors in browser
- [ ] Charts load in < 2 seconds
- [ ] Export functionality works (if implemented)

---

## Example Usage

```python
import streamlit as st
import pandas as pd
from app.components.dashboard import render_overview

# In main app
facilities_df = pd.read_csv("data/processed/facilities.csv")
cities_df = pd.read_csv("data/processed/city_stats.csv")

# Apply filters
filtered_facilities = facilities_df[facilities_df['city'].isin(selected_cities)]
filtered_cities = cities_df[cities_df['city'].isin(selected_cities)]

# Render dashboard
render_overview(filtered_facilities, filtered_cities)
```

---

## Design Decisions

### Why Plotly?
- Interactive hover tooltips
- Professional appearance
- Good Streamlit integration
- Export capabilities
- Responsive by default

### Why These Specific Charts?
- **Bar charts**: Easy comparison across cities
- **Scatter plot**: Reveals relationships between population and saturation
- **Pie chart**: Quick overview of quality distribution
- Each chart answers a specific business question

### Color Coding Strategy
- **Green**: Positive/high opportunity
- **Yellow**: Medium/neutral
- **Red**: Low opportunity/concern
- Consistent with common data visualization conventions
- **Accessibility**: Use colorblind-safe palettes (e.g., ColorBrewer schemes)
- **Alternative Indicators**: Consider adding patterns or icons in addition to colors for better accessibility

---

## Dependencies

### Python Packages
```
plotly>=5.16.0
pandas>=2.1.0
streamlit>=1.27.0
```

### Story Dependencies
- **Story 6.1**: Streamlit Main App Structure
  - Provides data loading functions
  - Provides filter logic
  - Provides tab structure

---

## Success Criteria

### Minimum Viable Product (MVP)
- [ ] 4 core charts render correctly
- [ ] Charts integrate with filters
- [ ] Hover tooltips work
- [ ] Responsive layout

### Stretch Goals
- [ ] Export chart functionality
- [ ] Additional chart types (box plots, histograms)
- [ ] Animated transitions
- [ ] Drill-down interactivity

---

## Non-Goals

This story does **NOT** include:
- ❌ Map visualization (covered in Story 6.2)
- ❌ Data export (covered in Story 6.4)
- ❌ Real-time data updates
- ❌ Advanced analytics (ML predictions, forecasting)
- ❌ Comparison with historical data

---

## Open Questions

1. Should we use Plotly Express (simpler) or Graph Objects (more control)?
   - **Recommendation**: Start with Plotly Express, refactor to Graph Objects if needed

2. Should charts be full-width or in columns?
   - **Recommendation**: 2-column layout for smaller charts, full-width for complex charts

3. Should we cache chart generation?
   - **Recommendation**: Yes, use `@st.cache_data` for chart functions

4. Should we show raw numbers or percentages?
   - **Recommendation**: Both (numbers primary, percentages in tooltips)

---

## Future Enhancements

- **Temporal Analysis**: Track facility growth over time
- **Comparative Analysis**: Compare cities side-by-side
- **Advanced Filtering**: Filter by indoor/outdoor, rating ranges
- **Custom Metrics**: User-defined opportunity weights
- **Report Generation**: PDF export with all charts

