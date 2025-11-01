# Story 5.1: Data Collection CLI

**Priority**: P0 (Critical Path)  
**Layer**: 5 (CLI & Orchestration)  
**Dependencies**: Story 1.1 (Google Places), Story 1.2 (Reviews), Story 2.1 (LLM Analyzer), Story 3.1 (Cleaner), Story 3.2 (Deduplicator)  
**Estimated Effort**: Small

---

## Description

Create a CLI script to orchestrate the entire data collection pipeline. This script will coordinate multiple collectors and processors to gather padel facility data from Google Places API, optionally enrich it with reviews and LLM analysis, clean and deduplicate the data, and save it to CSV format.

This is the primary entry point for data collection and should provide clear progress feedback and robust error handling.

---

## Input Contract

**Command Line Execution**:
```bash
python scripts/collect_data.py [OPTIONS]
```

**Optional Arguments**:
- `--region`: Geographic region to search (default: "Algarve, Portugal")
- `--with-reviews`: Fetch reviews for each facility (default: False)
- `--enrich-indoor-outdoor`: Use LLM to analyze indoor/outdoor status (default: False)
- `--llm-provider`: LLM provider to use - 'openai' or 'anthropic' (default: 'openai')
- `--llm-model`: LLM model to use (default: 'gpt-4o-mini')
- `--output`: Output file path (default: 'data/raw/facilities.csv')
- `--verbose`: Enable verbose logging (default: False)

**Environment Variables** (from `.env`):
- `GOOGLE_API_KEY`: Google Places API key (required)
- `OPENAI_API_KEY`: OpenAI API key (optional, for LLM enrichment)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional, for LLM enrichment)

---

## Output Contract

**Primary Output**: 
- CSV file at `data/raw/facilities.csv` containing all collected and cleaned facilities

**CSV Schema**:
```csv
place_id,name,address,city,postal_code,latitude,longitude,rating,review_count,google_url,facility_type,num_courts,indoor_outdoor,phone,website,collected_at,last_updated
```

**Console Output**:
- Progress indicators for each pipeline stage
- Summary statistics (total facilities, cities covered, etc.)
- Error/warning messages
- Execution time

**Exit Codes**:
- `0`: Success - All stages completed successfully
- `1`: Configuration Error - Missing API key or invalid configuration
- `2`: Data Collection Failed - Error during Google Places API calls
- `3`: Data Processing Failed - Error during cleaning or deduplication

Example usage in shell:
```bash
python scripts/collect_data.py
if [ $? -eq 0 ]; then
    echo "Success! Proceeding to next step..."
    python scripts/process_data.py
else
    echo "Data collection failed with exit code $?"
    exit 1
fi
```

---

## Script Behavior

The script should execute the following stages in order:

### Stage 1: Initialization
1. Load configuration from `.env` and command-line arguments
2. Validate Google API key is present
3. Create output directories if they don't exist (`data/raw/`, `data/cache/`)
4. Initialize collectors (GooglePlacesCollector, optionally ReviewCollector and LLM Analyzer)
5. Display configuration summary

### Stage 2: Data Collection
1. Search for padel facilities using GooglePlacesCollector
2. Display progress (e.g., "Found 45 facilities...")
3. Handle pagination and rate limiting automatically
4. Log any API errors but continue processing

### Stage 3: Review Collection (Optional)
If `--with-reviews` flag is set:
1. Iterate through collected facilities
2. Fetch reviews for each facility using ReviewCollector
3. Display progress (e.g., "Fetching reviews: 15/45...")
4. Store reviews temporarily for LLM enrichment

### Stage 4: LLM Enrichment (Optional)
If `--enrich-indoor-outdoor` flag is set:
1. Iterate through facilities with reviews
2. Use IndoorOutdoorAnalyzer to extract indoor/outdoor status
3. Display progress (e.g., "Analyzing: 10/45...")
4. Update facility objects with extracted information
5. Handle API errors gracefully (skip facility if LLM fails)

### Stage 5: Data Cleaning
1. Clean facilities using DataCleaner
2. Display count before/after cleaning
3. Log any facilities removed and reasons

### Stage 6: Deduplication
1. Remove duplicates using Deduplicator
2. Display count before/after deduplication
3. Log duplicate facility names

### Stage 7: Save Results
1. Convert facilities to DataFrame
2. Ensure output directory exists
3. Save to CSV with proper formatting
4. Display output file path
5. Print summary statistics

---

## Acceptance Criteria

- [x] Script is executable via `python scripts/collect_data.py`
- [x] Progress logging for each major stage
- [x] Progress indicators show current/total counts (e.g., "15/45")
- [x] Error handling with informative messages (doesn't crash on API errors)
- [x] Validates required API key before starting
- [x] Creates necessary directories automatically
- [x] Saves intermediate results if script fails mid-execution
- [x] Execution time < 30 minutes for full Algarve collection
- [x] Clean console output (not cluttered with debug info unless `--verbose`)
- [x] **Exit Codes Implemented:**
  - [x] Exit code 0 on successful completion
  - [x] Exit code 1 when API key is missing
  - [x] Exit code 1 when configuration is invalid
  - [x] Exit code 2 when data collection fails
  - [x] Exit code 3 when data processing fails
- [x] Command-line arguments work correctly
- [x] Works with and without optional enrichment steps
- [x] Displays summary statistics at the end
- [x] Proper timestamp formatting in output

---

## Files to Create

```
scripts/collect_data.py
```

---

## Technical Requirements

### Argument Parsing

Use `argparse` for command-line argument handling:
```python
import argparse

parser = argparse.ArgumentParser(description='Collect padel facility data')
parser.add_argument('--region', default='Algarve, Portugal')
parser.add_argument('--with-reviews', action='store_true')
parser.add_argument('--enrich-indoor-outdoor', action='store_true')
# ... etc
```

### Configuration Loading

1. Load settings from `src.config.settings`
2. Override with command-line arguments where provided
3. Validate all required configuration is present

### Progress Logging

Use clean, informative progress messages:
```
🎾 Starting Algarve Padel Field Data Collection
============================================================

1. Initializing Google Places collector...
   ✓ API key validated
   ✓ Cache enabled (30 day TTL)

2. Searching for padel facilities in Algarve, Portugal...
   Query: "padel Algarve, Portugal"
   Query: "padel court Algarve, Portugal"
   Query: "padel club Algarve, Portugal"
   Query: "centro de padel Algarve, Portugal"
   ✓ Found 52 facilities

3. Cleaning data...
   ✓ 52 facilities after cleaning (0 removed)

4. Removing duplicates...
   ✓ 48 unique facilities (4 duplicates removed)

5. Saving data...
   ✓ Saved to: data/raw/facilities.csv

✅ Data collection complete!
   Total facilities: 48
   Cities covered: 12
   Execution time: 8m 23s

Next step: python scripts/process_data.py
```

### Error Handling

Handle errors gracefully:
- **Missing API key**: Print clear error message with setup instructions
- **API errors**: Log warning but continue with other facilities
- **Network errors**: Suggest checking internet connection
- **Invalid region**: Suggest valid region format
- **Write errors**: Check permissions on output directory

### Performance Optimization

- Use caching to speed up subsequent runs
- Show estimated time remaining for long operations
- Don't refetch data that's already cached
- Consider adding `--force-refresh` flag to bypass cache

### Optional Verbose Mode

When `--verbose` flag is set:
- Show detailed API request/response info
- Display cache hit/miss information
- Log each facility as it's processed
- Show stack traces for errors

---

## Testing Requirements

### Unit Tests

Create `tests/test_scripts/test_collect_data.py` to test:

1. **Argument Parsing**
   - [x] Test default values
   - [x] Test custom arguments
   - [x] Test flag combinations

2. **Configuration Validation**
   - [x] Test missing API key handling
   - [x] Test invalid configuration

3. **Progress Logging**
   - [x] Test log messages are formatted correctly
   - [x] Test progress indicators

4. **Error Handling**
   - [x] Test API error recovery
   - [x] Test file write errors
   - [x] Test invalid region handling

5. **Exit Codes**
   - [x] Test success exit code (0) when all stages complete
   - [x] Test exit code 1 when GOOGLE_API_KEY is missing
   - [x] Test exit code 1 when configuration is invalid
   - [x] Test exit code 2 when Google Places API fails
   - [x] Test exit code 3 when data cleaning/deduplication fails
   - [x] Verify exit codes are returned to shell correctly

### Integration Tests

Test the full pipeline with mocked components:
- [x] Mock GooglePlacesCollector to return sample data
- [x] Mock ReviewCollector and LLM Analyzer
- [x] Verify data flows through all stages correctly
- [x] Verify CSV output is correctly formatted

### Manual Testing

Run the script with various configurations:
- [x] Default configuration (no flags)
- [x] With reviews (`--with-reviews`)
- [x] With LLM enrichment (`--enrich-indoor-outdoor`)
- [x] With both optional features
- [x] With invalid API key (verify error handling)
- [x] With `--verbose` flag
- [x] Run twice (verify caching speeds up second run)

---

## Example Usage

### Basic Collection (No Enrichment)
```bash
python scripts/collect_data.py
```

### With Reviews
```bash
python scripts/collect_data.py --with-reviews
```

### Full Enrichment (Reviews + LLM)
```bash
python scripts/collect_data.py \
  --with-reviews \
  --enrich-indoor-outdoor \
  --llm-provider openai \
  --llm-model gpt-4o-mini
```

### Custom Region and Output
```bash
python scripts/collect_data.py \
  --region "Lagos, Algarve, Portugal" \
  --output data/raw/lagos_facilities.csv
```

### Verbose Mode
```bash
python scripts/collect_data.py --verbose
```

---

## Implementation Notes

### Import Structure

The script should import from the project's `src/` modules:
```python
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.collectors.google_places import GooglePlacesCollector
from src.collectors.review_collector import ReviewCollector
from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
from src.processors.cleaner import DataCleaner
from src.processors.deduplicator import Deduplicator
import pandas as pd
```

### Timing and Statistics

Track and display:
- Start time
- End time
- Total execution time
- Number of facilities at each stage
- Number of cities covered
- Number of API calls (if verbose)
- Cache hit rate (if verbose)

### Intermediate Saves

Consider saving intermediate results:
- Save raw API responses to `data/cache/`
- If script crashes, user can resume from last stage
- Optional `--resume` flag to skip completed stages

### Idempotency

The script should be idempotent:
- Running twice should produce same results (unless data changed)
- Caching ensures subsequent runs are fast
- Existing output file should be overwritten (with warning)

---

## Dependencies

This story depends on the following being completed first:

- **Story 1.1**: GooglePlacesCollector must be implemented
- **Story 1.2**: ReviewCollector must be implemented (for optional features)
- **Story 2.1**: IndoorOutdoorAnalyzer must be implemented (for optional features)
- **Story 3.1**: DataCleaner must be implemented
- **Story 3.2**: Deduplicator must be implemented

All dependencies must have stable APIs matching their output contracts.

---

## Success Criteria

✅ Script runs successfully with default configuration  
✅ Clear progress output at each stage  
✅ Handles errors gracefully without crashing  
✅ Produces valid CSV output  
✅ Optional features work correctly  
✅ Execution completes in < 30 minutes  
✅ Second run is significantly faster (due to caching)  
✅ Command-line arguments work as expected  
✅ Exit codes are correct  
✅ Summary statistics are accurate  
✅ Code is well-documented and maintainable

---

## Future Enhancements (Not in Scope)

These could be added in future iterations:
- Resume functionality (`--resume` flag)
- Parallel processing for faster collection
- Real-time progress bars using `tqdm`
- Configurable output formats (JSON, Excel)
- Dry-run mode (`--dry-run`)
- Email notification on completion
- Integration with cloud storage (S3, GCS)

