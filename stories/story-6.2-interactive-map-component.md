# Story 6.2: Interactive Map Component

## Overview

**Priority**: P0 (Critical Path)  
**Dependencies**: Story 6.1 (Streamlit Main App Structure)  
**Estimated Effort**: Medium  
**Layer**: 6 (Visualization)

## Description

Create an interactive Folium-based map component that visualizes padel facilities and city opportunity scores in the Algarve region. The map should provide a geographic view of facility distribution, ratings, and market opportunities.

## Input Contract

The component receives two pandas DataFrames:

### `facilities_df: pd.DataFrame`
Required columns:
- `place_id`: str
- `name`: str
- `city`: str
- `address`: str
- `latitude`: float
- `longitude`: float
- `rating`: float (nullable)
- `review_count`: int
- `google_url`: str (optional)
- `indoor_outdoor`: str (optional)

### `cities_df: pd.DataFrame`
Required columns:
- `city`: str
- `center_lat`: float
- `center_lng`: float
- `opportunity_score`: float (0-100)
- `total_facilities`: int
- `avg_rating`: float (nullable)
- `population`: int (nullable)

## Output Contract

### API Surface

```python
def create_map(facilities_df: pd.DataFrame, cities_df: pd.DataFrame) -> folium.Map
```

**Returns**: A fully configured `folium.Map` object ready to be rendered in Streamlit via `streamlit_folium.st_folium()`

## Functional Requirements

### 1. Map Configuration
- **Center**: Algarve region center (approximately 37.1°N, -8.0°W)
- **Zoom Level**: 10 (regional view)
- **Base Tiles**: OpenStreetMap
- **Responsive**: Should adapt to different screen sizes

### 2. Facility Markers
Each facility should be displayed as a `CircleMarker` with:

#### Color Coding by Rating
- **Green**: Rating ≥ 4.5
- **Blue**: Rating ≥ 4.0
- **Orange**: Rating ≥ 3.5
- **Red**: Rating < 3.5
- **Gray**: No rating available

#### Marker Properties
- **Radius**: 8 pixels
- **Fill**: True
- **Fill Opacity**: 0.7
- **Tooltip**: Facility name (appears on hover)

#### Popup Content
Interactive popup containing:
- Facility name (heading)
- City
- Rating (with star emoji) and review count
- Full address
- Link to Google Maps (if `google_url` available)

Popup HTML structure:
```html
<div style="width: 200px">
    <h4>{name}</h4>
    <p><b>City:</b> {city}</p>
    <p><b>Rating:</b> {rating}⭐ ({review_count} reviews)</p>
    <p><b>Address:</b> {address}</p>
    <a href="{google_url}" target="_blank">View on Google Maps</a>
</div>
```

### 3. City Center Markers
Each city should have a marker at its center coordinates with:

#### Marker Properties
- **Icon**: Purple marker with info-sign icon
- **Tooltip**: City name with opportunity score (e.g., "Albufeira: 85 score")

#### Popup Content
```html
<div style="width: 200px">
    <h4>{city}</h4>
    <p><b>Opportunity Score:</b> {score:.1f}/100</p>
    <p><b>Facilities:</b> {total_facilities}</p>
    <p><b>Avg Rating:</b> {avg_rating:.2f if avg_rating else 'N/A'}⭐</p>
    <p><b>Population:</b> {population:,if population else 'Unknown'}</p>
</div>
```

**Note**: Template must handle null/NaN values for `avg_rating` and `population` fields, which may be None in the CityStats model.

### 4. Heatmap Layer
- Add a `folium.plugins.HeatMap` layer showing facility density
- **Data**: List of [latitude, longitude] coordinates for each facility
- **Radius**: 15
- **Blur**: 25
- **Name**: "Density Heatmap"
- **Toggleable**: User can show/hide via layer control

### 5. Layer Control
- Add `folium.LayerControl()` to allow users to toggle layers
- Should support toggling the heatmap layer on/off

## Non-Functional Requirements

### Performance
- Map should render smoothly with 50+ facility markers
- Initial load time < 2 seconds
- Smooth pan and zoom interactions

### User Experience
- Intuitive color coding (green = good, red = poor)
- Informative popups without overwhelming information
- Clear visual distinction between facilities and city markers
- Responsive tooltips on hover

### Data Handling
- **Handle missing/null values gracefully**:
  - Facility ratings may be None/NaN (show as "gray" color, "N/A" in popup)
  - City population may be None (show as "Unknown" in popup)
  - City avg_rating may be None (show as "N/A" in popup)
- Handle empty DataFrames without crashing
- Format numbers appropriately (commas for thousands, decimals for ratings)
- Use `pd.isna()` or `pd.notna()` to check for null values before formatting

## Acceptance Criteria

- [x] Map centers on Algarve region with appropriate zoom
- [x] All facilities displayed as CircleMarkers with correct color coding
- [x] Facility popups contain all required information
- [x] City markers display opportunity scores
- [x] Heatmap layer shows facility density
- [x] Layer control allows toggling heatmap
- [x] Tooltips work on hover for both facility and city markers
- [x] Map renders correctly in Streamlit via `st_folium()`
- [x] **No crashes when rating is null/NaN (displays "gray" color and "N/A" in popup)**
- [x] **No crashes when city population is None (displays "Unknown" in popup)**
- [x] **No crashes when city avg_rating is None (displays "N/A" in popup)**
- [x] External links open in new tab
- [x] Responsive and performant with 50+ markers

## Files to Create

```
app/
└── components/
    └── map_view.py
```

## Implementation Notes

### Dependencies
```python
import folium
from folium import plugins
import pandas as pd
```

### Integration with Streamlit
In `app/app.py`, the map should be displayed using:
```python
from streamlit_folium import st_folium
from components.map_view import create_map

# In the Map tab:
map_obj = create_map(filtered_facilities, filtered_cities)
st_folium(map_obj, width=1200, height=600)
```

### Handling Null Ratings
Use `pd.isna()` or `pd.notna()` to check for null values before applying color coding:
```python
if pd.isna(facility['rating']):
    color = 'gray'
elif facility['rating'] >= 4.5:
    color = 'green'
# ... etc
```

### Map Bounds
For Algarve region:
- Latitude range: approximately 36.96° to 37.42°
- Longitude range: approximately -9.0° to -7.4°

## Testing Requirements

### Unit Tests
Not applicable for this component (visualization component, better tested manually or with integration tests)

### Integration Tests
- [x] Test with empty DataFrames (both facilities and cities)
- [x] **Test with facilities having null ratings (should display gray markers)**
- [x] **Test with cities having null population (should display "Unknown" in popup)**
- [x] **Test with cities having null avg_rating (should display "N/A" in popup)**
- [x] Test with missing optional fields (google_url, indoor_outdoor, etc.)
- [x] Test with single facility
- [x] Test with large dataset (100+ facilities)

### Manual Testing Checklist
- [ ] Verify map loads and centers correctly
- [ ] Click on multiple facility markers and verify popup content
- [ ] Click on city markers and verify opportunity score display
- [ ] Toggle heatmap layer on/off
- [ ] Hover over markers and verify tooltips
- [ ] Click Google Maps links and verify they open in new tab
- [ ] Test with filtered data (subset of cities)
- [ ] Zoom in/out and verify performance
- [ ] Pan around the map and verify markers stay in correct positions

## Example Usage

```python
import pandas as pd
from components.map_view import create_map

# Load data
facilities_df = pd.read_csv("data/processed/facilities.csv")
cities_df = pd.read_csv("data/processed/city_stats.csv")

# Create map
map_object = create_map(facilities_df, cities_df)

# Display in Streamlit
st_folium(map_object, width=1200, height=600)
```

## Success Metrics

- Users can quickly identify high-opportunity cities (purple markers)
- Geographic gaps in facility coverage are visually apparent
- Facility quality distribution is clear from color coding
- Map provides actionable insights without requiring data tables

## Future Enhancements (Out of Scope)

- Search functionality to find specific facilities
- Clustering for high-density areas
- Custom tile layers (satellite view)
- Distance measurement tool
- Drawing tools for custom regions
- Route planning between facilities
- Integration with indoor/outdoor filter

