# Story 6.4: Export Functionality

**Priority**: P1 (Nice to Have)  
**Dependencies**: Story 6.1 (Streamlit Main App Structure)  
**Estimated Effort**: Small (2-4 hours)  
**Layer**: 6 (Visualization)

---

## Description

Implement data export functionality allowing users to download filtered facility and city statistics data in CSV format. This enables users to perform custom analysis in Excel or other tools, share data with stakeholders, and archive research results.

---

## Input Contract

**Accepts**:
- `facilities_df: pd.DataFrame` - Filtered facilities dataframe
- `cities_df: pd.DataFrame` - Filtered city statistics dataframe

**Format**:
```python
# Facilities DataFrame columns
['place_id', 'name', 'address', 'city', 'postal_code', 'latitude', 
 'longitude', 'rating', 'review_count', 'google_url', 'facility_type', 
 'num_courts', 'indoor_outdoor', 'phone', 'website', 'collected_at', 
 'last_updated']

# Cities DataFrame columns
['city', 'total_facilities', 'avg_rating', 'median_rating', 
 'total_reviews', 'center_lat', 'center_lng', 'population', 
 'facilities_per_capita', 'avg_distance_to_nearest', 'opportunity_score', 
 'population_weight', 'saturation_weight', 'quality_gap_weight', 
 'geographic_gap_weight']
```

---

## Output Contract

**Produces**:
- CSV file(s) saved to `data/exports/` directory
- File download triggered in Streamlit interface

**File Naming Convention**:
```
facilities_export_YYYY-MM-DD_HH-MM-SS.csv
city_stats_export_YYYY-MM-DD_HH-MM-SS.csv
```

---

## API Surface

```python
# src/utils/exporters.py

from pathlib import Path
import pandas as pd
from datetime import datetime
from typing import Optional

class DataExporter:
    """Export dataframes to CSV files with timestamped filenames."""
    
    def __init__(self, export_dir: Path = Path("data/exports")):
        """
        Initialize exporter.
        
        Args:
            export_dir: Directory to save exports
        """
        pass
    
    def export_to_csv(
        self,
        df: pd.DataFrame,
        prefix: str,
        include_index: bool = False
    ) -> Path:
        """
        Export dataframe to CSV with timestamp.
        
        Args:
            df: DataFrame to export
            prefix: Filename prefix (e.g., 'facilities', 'city_stats')
            include_index: Whether to include index in CSV
            
        Returns:
            Path to created CSV file
            
        Raises:
            ValueError: If dataframe is empty
            IOError: If export directory cannot be created
        """
        pass
    
    @staticmethod
    def generate_filename(prefix: str, extension: str = "csv") -> str:
        """
        Generate timestamped filename.
        
        Args:
            prefix: Filename prefix
            extension: File extension (without dot)
            
        Returns:
            Filename string (e.g., 'facilities_export_2024-01-15_14-30-45.csv')
        """
        pass
    
    def get_export_path(self, filename: str) -> Path:
        """
        Get full path for export file.
        
        Args:
            filename: Name of export file
            
        Returns:
            Full Path object
        """
        pass
```

---

## Acceptance Criteria

### Functional Requirements

- [ ] **CSV Export Button**: Streamlit download button for facilities data
- [ ] **CSV Export Button**: Streamlit download button for city statistics data
- [ ] **Filtered Data Only**: Export respects current filter selections
- [ ] **Timestamp in Filename**: Automatic timestamp in format `YYYY-MM-DD_HH-MM-SS`
- [ ] **Save to Directory**: Files saved to `data/exports/` directory
- [ ] **Directory Creation**: Auto-create `data/exports/` if it doesn't exist
- [ ] **Empty Dataframe Handling**: Graceful error message if no data to export
- [ ] **File Size Validation**: Handle large exports (100+ facilities)

### User Experience

- [ ] **Clear Button Labels**: "📥 Download Facilities CSV" and "📥 Download City Stats CSV"
- [ ] **Download Feedback**: Success message after export
- [ ] **File Info Display**: Show number of rows exported
- [ ] **Sidebar Placement**: Export buttons in logical location (bottom of sidebar or in dedicated section)

### Data Quality

- [ ] **All Columns Included**: No data loss during export
- [ ] **Proper Encoding**: UTF-8 encoding for international characters
- [ ] **Date Formatting**: ISO format for datetime fields
- [ ] **Null Handling**: Empty strings for null values (not "NaN" text)

### Documentation

- [ ] **User Guide**: Document export folder cleanup in USAGE.md
- [ ] **UI Note**: Display message in app about manual cleanup requirement
- [ ] **Best Practice**: Suggest periodic cleanup of old exports

### Technical Requirements

- [ ] **No Index Column**: Don't export pandas index unless explicitly needed
- [ ] **Column Order Preserved**: Maintain logical column ordering
- [ ] **Memory Efficient**: Use pandas optimizations for large files
- [ ] **Thread Safe**: Safe for concurrent exports

---

## Implementation Details

### File Structure

```
src/utils/exporters.py         # Main exporter class
tests/test_utils/               # Test directory
  └── test_exporters.py         # Unit tests
data/exports/                   # Export destination (git-ignored)
  ├── .gitkeep                  # Keep directory in git
  └── *.csv                     # Exported files (ignored)
```

### Integration Points

**Streamlit App** (`app/app.py`):
```python
from src.utils.exporters import DataExporter

# In sidebar or dedicated "Export" section
st.sidebar.header("Export Data")

exporter = DataExporter()

# Facilities export
facilities_csv = exporter.export_to_csv(
    filtered_facilities, 
    prefix="facilities"
)

if facilities_csv:
    with open(facilities_csv, 'rb') as f:
        st.sidebar.download_button(
            label="📥 Download Facilities CSV",
            data=f,
            file_name=facilities_csv.name,
            mime="text/csv"
        )
```

### Error Handling

| Error Condition | Handling Strategy |
|----------------|-------------------|
| Empty dataframe | Display warning: "No data to export with current filters" |
| Export directory permission error | Show error message with directory path |
| Disk space full | Catch IOError and display appropriate message |
| Invalid characters in filename | Sanitize timestamp format |

---

## Testing Requirements

### Unit Tests (`tests/test_utils/test_exporters.py`)

```python
def test_export_to_csv_creates_file():
    """Test that CSV file is created with correct data."""
    pass

def test_generate_filename_format():
    """Test filename timestamp format."""
    pass

def test_export_empty_dataframe_raises_error():
    """Test that exporting empty dataframe raises ValueError."""
    pass

def test_export_respects_filtered_data():
    """Test that only filtered rows are exported."""
    pass

def test_export_preserves_all_columns():
    """Test that all dataframe columns are in CSV."""
    pass

def test_export_directory_creation():
    """Test that export directory is created if missing."""
    pass

def test_utf8_encoding():
    """Test that special characters are preserved."""
    pass

def test_null_value_handling():
    """Test that null values are exported as empty strings."""
    pass

def test_concurrent_exports_unique_filenames():
    """Test that simultaneous exports have unique filenames."""
    pass
```

### Integration Tests

- [ ] Test export from Streamlit app with filtered data
- [ ] Test download button triggers correctly
- [ ] Verify exported CSV can be re-imported into pandas
- [ ] Test with large dataset (1000+ rows)

### Manual Testing Checklist

- [ ] Export with all filters enabled
- [ ] Export with no filters (all data)
- [ ] Export with zero results
- [ ] Open exported CSV in Excel - verify formatting
- [ ] Verify filenames are unique for rapid consecutive exports
- [ ] Test on different operating systems (Windows/Mac/Linux)

---

## Files to Create

```
src/utils/exporters.py          # Main implementation
tests/test_utils/test_exporters.py   # Unit tests
data/exports/.gitkeep            # Ensure directory exists in git
```

---

## Files to Modify

```
app/app.py                       # Add export buttons
.gitignore                       # Add data/exports/*.csv
```

---

## Configuration

**Add to `.gitignore`**:
```gitignore
# Export files (keep directory structure but ignore CSVs)
data/exports/*.csv
data/exports/*.xlsx
```

**Add to `src/config.py`** (if needed):
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Export settings
    export_dir: Path = data_dir / "exports"
    export_include_index: bool = False
    export_encoding: str = "utf-8"
```

---

## Example Usage

### In Streamlit App

```python
import streamlit as st
from src.utils.exporters import DataExporter

# Initialize exporter
exporter = DataExporter()

# Create export section
st.sidebar.markdown("---")
st.sidebar.header("📥 Export Data")

# Show data summary
st.sidebar.write(f"Facilities: {len(filtered_facilities)} rows")
st.sidebar.write(f"Cities: {len(filtered_cities)} rows")

# Facilities export
if len(filtered_facilities) > 0:
    facilities_csv = exporter.export_to_csv(
        filtered_facilities,
        prefix="facilities"
    )
    
    with open(facilities_csv, 'rb') as f:
        st.sidebar.download_button(
            label="Download Facilities CSV",
            data=f,
            file_name=facilities_csv.name,
            mime="text/csv",
            help="Download filtered facilities data"
        )
else:
    st.sidebar.warning("No facilities data to export")

# City stats export
if len(filtered_cities) > 0:
    cities_csv = exporter.export_to_csv(
        filtered_cities,
        prefix="city_stats"
    )
    
    with open(cities_csv, 'rb') as f:
        st.sidebar.download_button(
            label="Download City Stats CSV",
            data=f,
            file_name=cities_csv.name,
            mime="text/csv",
            help="Download city statistics"
        )
else:
    st.sidebar.warning("No city data to export")
```

---

## Success Criteria

- [ ] User can export filtered data with one click
- [ ] Exported CSV opens correctly in Excel/Google Sheets
- [ ] Filenames are unique and sortable by timestamp
- [ ] All data columns are preserved
- [ ] Special characters display correctly
- [ ] Export works with 0 rows (shows appropriate message)
- [ ] Export works with 1000+ rows efficiently
- [ ] Unit test coverage ≥90%

---

## Future Enhancements (Out of Scope)

- Excel (.xlsx) export with formatting
- PDF report generation
- JSON export format
- Scheduled/automated exports
- Export templates (custom column selection)
- Export presets (save filter configurations)
- Email export functionality
- Compression for large exports (.zip)

---

## Notes

- Keep export logic simple and focused on CSV format
- Streamlit's `download_button` handles browser download automatically
- Consider adding export timestamp metadata within CSV (comment row)
- **File Cleanup**: Files in `data/exports/` should be manually cleaned by user periodically
  - No automatic cleanup implemented (to prevent accidental data loss)
  - Consider adding a note in the UI: "Old exports are not automatically deleted. Clean up data/exports/ folder periodically."
  - Future enhancement: Optional auto-cleanup of exports older than N days
- No authentication/authorization needed (local use only)

---

## Related Stories

- **Story 6.1**: Streamlit Main App Structure (provides dataframes to export)
- **Story 0.1**: Data Models (defines data structure being exported)
- **Story 5.2**: Data Processing CLI (generates initial processed data)

