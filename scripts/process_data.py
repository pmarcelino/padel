"""
Data processing CLI script.

This script orchestrates the complete data processing pipeline:
1. Load raw facility data from CSV
2. Aggregate facilities by city
3. Calculate geographic metrics (distance to nearest)
4. Calculate opportunity scores
5. Save processed data to CSV files
6. Display summary of top opportunities

Usage:
    python scripts/process_data.py
"""

import sys
from pathlib import Path
from typing import List

import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analyzers.aggregator import CityAggregator
from src.analyzers.distance import DistanceCalculator
from src.analyzers.scorer import OpportunityScorer
from src.config import settings
from src.models.city import CityStats
from src.models.facility import Facility


def load_facilities_from_csv(file_path: Path) -> List[Facility]:
    """
    Load facilities from CSV and convert to Facility objects.
    
    This function reads a CSV file containing facility data and converts each
    row into a Facility Pydantic model. Handles datetime parsing from ISO format
    strings and missing values appropriately.
    
    Args:
        file_path: Path to the CSV file containing facility data
        
    Returns:
        List of Facility objects. Returns empty list if file doesn't exist
        or if the CSV is empty.
        
    Example:
        >>> facilities = load_facilities_from_csv(Path("data/raw/facilities.csv"))
        >>> len(facilities)
        67
    """
    # Check if file exists
    if not file_path.exists():
        return []
    
    try:
        # Read CSV with proper data types
        df = pd.read_csv(file_path, dtype={'phone': str, 'postal_code': str})
        
        # Return empty list if no data
        if df.empty:
            return []
        
        # Parse datetime columns if they exist
        datetime_cols = ["collected_at", "last_updated"]
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # Convert each row to Facility object
        facilities = []
        for _, row in df.iterrows():
            # Convert row to dict and handle NaN values
            row_dict = row.to_dict()
            
            # Replace NaN with None for optional fields
            for key, value in row_dict.items():
                if pd.isna(value):
                    row_dict[key] = None
            
            # Create Facility object
            facility = Facility(**row_dict)
            facilities.append(facility)
        
        return facilities
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return []


def calculate_geographic_metrics(
    city_stats: List[CityStats], 
    facilities: List[Facility]
) -> List[CityStats]:
    """
    Calculate avg_distance_to_nearest for each city.
    
    This function updates each CityStats object with the minimum distance
    to the nearest facility in neighboring cities using the DistanceCalculator.
    The input list is modified in place.
    
    Args:
        city_stats: List of CityStats objects to update
        facilities: Complete list of facilities across all cities
        
    Returns:
        Same list of CityStats with avg_distance_to_nearest populated
        
    Example:
        >>> city_stats = [CityStats(city="Albufeira", ...)]
        >>> facilities = [Facility(city="Albufeira", ...), Facility(city="Faro", ...)]
        >>> updated_stats = calculate_geographic_metrics(city_stats, facilities)
        >>> updated_stats[0].avg_distance_to_nearest
        26.01
    """
    for stats in city_stats:
        # Calculate distance to nearest facility in other cities
        distance = DistanceCalculator.calculate_distance_to_nearest(
            stats.city, 
            facilities
        )
        stats.avg_distance_to_nearest = distance
    
    return city_stats


def save_processed_data(
    facilities: List[Facility], 
    city_stats: List[CityStats]
) -> None:
    """
    Save processed data to CSV files.
    
    Creates the output directory if it doesn't exist and saves both
    facilities and city_stats to CSV files in the processed data directory.
    
    Args:
        facilities: List of Facility objects to save
        city_stats: List of CityStats objects to save
        
    Raises:
        OSError: If unable to create directory or write files
        
    Example:
        >>> save_processed_data(facilities, city_stats)
        # Creates:
        #   data/processed/facilities.csv
        #   data/processed/city_stats.csv
    """
    # Create output directory if it doesn't exist
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert facilities to DataFrame
    facilities_dicts = [f.to_dict() for f in facilities]
    facilities_df = pd.DataFrame(facilities_dicts)
    
    # Convert city_stats to DataFrame
    city_stats_dicts = [s.model_dump() for s in city_stats]
    city_stats_df = pd.DataFrame(city_stats_dicts)
    
    # Save to CSV
    facilities_path = settings.processed_data_dir / "facilities.csv"
    city_stats_path = settings.processed_data_dir / "city_stats.csv"
    
    try:
        facilities_df.to_csv(facilities_path, index=False)
        city_stats_df.to_csv(city_stats_path, index=False)
        
        print(f"   ✓ Saved: {facilities_path}")
        print(f"   ✓ Saved: {city_stats_path}")
        
    except Exception as e:
        print(f"❌ Error: Cannot write to {settings.processed_data_dir}. Check permissions.")
        raise


def display_summary(city_stats: List[CityStats]) -> None:
    """
    Display formatted summary of top 5 cities.
    
    Prints a formatted table showing the top 5 cities ranked by opportunity
    score, including their key metrics: opportunity score, number of facilities,
    average rating, and population.
    
    Args:
        city_stats: List of CityStats objects (should be sorted by opportunity_score descending)
        
    Example:
        >>> display_summary(city_stats)
        Top 5 Cities by Opportunity Score:
        ------------------------------------------------------------
        1. Lagos: 78.3/100
           Facilities: 4, Avg Rating: 3.80⭐, Population: 31,049
    """
    if not city_stats:
        return
    
    print()
    print("Top 5 Cities by Opportunity Score:")
    print("-" * 60)
    
    # Take top 5 cities
    top_cities = city_stats[:5]
    
    for i, stats in enumerate(top_cities, 1):
        # Format rating with star emoji
        rating_str = f"{stats.avg_rating:.2f}⭐" if stats.avg_rating else "N/A"
        
        # Format population with comma separator
        pop_str = f"{stats.population:,}" if stats.population else "N/A"
        
        print(f"{i}. {stats.city}: {stats.opportunity_score:.1f}/100")
        print(f"   Facilities: {stats.total_facilities}, Avg Rating: {rating_str}, Population: {pop_str}")
        print()


def main() -> int:
    """
    Main orchestration function for data processing pipeline.
    
    Executes the complete data processing workflow:
    1. Loads raw facility data from CSV
    2. Aggregates facilities by city
    3. Calculates geographic metrics
    4. Calculates opportunity scores
    5. Sorts by opportunity score
    6. Saves processed data
    7. Displays summary
    
    Returns:
        Exit code: 0 on success, 1 on error
        
    Example:
        >>> exit_code = main()
        📊 Starting Data Processing
        ============================================================
        ...
        ✅ Processing complete!
        >>> exit_code
        0
    """
    print("📊 Starting Data Processing")
    print("=" * 60)
    print()
    
    # Step 1: Load raw data
    print("1. Loading raw data...")
    raw_data_path = settings.raw_data_dir / "facilities.csv"
    
    if not raw_data_path.exists():
        print(f"❌ Error: Raw data not found at {raw_data_path}")
        print("Please run the data collection script first:")
        print("  python scripts/collect_data.py")
        return 1
    
    facilities = load_facilities_from_csv(raw_data_path)
    
    if not facilities:
        print("⚠️  Warning: No facilities found in raw data")
        print("Processing cannot continue with empty dataset")
        return 1
    
    print(f"   Loaded {len(facilities)} facilities")
    print()
    
    # Step 2: Aggregate by city
    print("2. Aggregating by city...")
    aggregator = CityAggregator()
    city_stats = aggregator.aggregate(facilities)
    print(f"   {len(city_stats)} cities analyzed")
    print()
    
    # Step 3: Calculate geographic metrics
    print("3. Calculating geographic metrics...")
    city_stats = calculate_geographic_metrics(city_stats, facilities)
    print("   Distance calculations complete")
    print()
    
    # Step 4: Calculate opportunity scores
    print("4. Computing opportunity scores...")
    scorer = OpportunityScorer()
    city_stats = scorer.calculate_scores(city_stats)
    print("   Opportunity scores calculated")
    print()
    
    # Step 5: Sort by opportunity score (descending)
    city_stats.sort(key=lambda s: s.opportunity_score, reverse=True)
    
    # Step 6: Save processed data
    print("5. Saving processed data...")
    try:
        save_processed_data(facilities, city_stats)
    except Exception:
        return 1
    print()
    
    # Step 7: Display summary
    print("✅ Processing complete!")
    display_summary(city_stats)
    
    print("Next step: streamlit run app/app.py")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

