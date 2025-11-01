"""
Unit tests for data processing CLI script.

Tests validate the data processing pipeline including loading facilities from CSV,
aggregating by city, calculating distances and opportunity scores, and saving results.
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open
import io

import pandas as pd
import pytest

from src.models.facility import Facility
from src.models.city import CityStats


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_facilities():
    """Create sample facilities for testing."""
    return [
        Facility(
            place_id="alb_1",
            name="Club A",
            address="Address A",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=150,
            collected_at=datetime(2024, 1, 1, 12, 0, 0),
            last_updated=datetime(2024, 1, 1, 12, 0, 0),
        ),
        Facility(
            place_id="alb_2",
            name="Club B",
            address="Address B",
            city="Albufeira",
            latitude=37.0900,
            longitude=-8.2500,
            rating=4.2,
            review_count=80,
            collected_at=datetime(2024, 1, 1, 12, 0, 0),
            last_updated=datetime(2024, 1, 1, 12, 0, 0),
        ),
        Facility(
            place_id="faro_1",
            name="Club C",
            address="Address C",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.7,
            review_count=200,
            collected_at=datetime(2024, 1, 1, 12, 0, 0),
            last_updated=datetime(2024, 1, 1, 12, 0, 0),
        ),
    ]


@pytest.fixture
def sample_csv_data(sample_facilities):
    """Create sample CSV data as DataFrame."""
    return pd.DataFrame([f.to_dict() for f in sample_facilities])


@pytest.fixture
def sample_city_stats():
    """Create sample city stats for testing."""
    return [
        CityStats(
            city="Albufeira",
            total_facilities=2,
            avg_rating=4.35,
            median_rating=4.35,
            total_reviews=230,
            center_lat=37.08925,
            center_lng=-8.24875,
            population=42388,
            facilities_per_capita=0.47,
        ),
        CityStats(
            city="Faro",
            total_facilities=1,
            avg_rating=4.7,
            median_rating=4.7,
            total_reviews=200,
            center_lat=37.0194,
            center_lng=-7.9322,
            population=64560,
            facilities_per_capita=0.15,
        ),
    ]


# ============================================================================
# TEST LOAD FACILITIES FROM CSV
# ============================================================================


def test_load_facilities_from_csv(tmp_path, sample_csv_data):
    """Test loading facilities from CSV file."""
    # Import here to avoid issues before implementation
    from scripts.process_data import load_facilities_from_csv
    
    # Create temporary CSV file
    csv_file = tmp_path / "facilities.csv"
    sample_csv_data.to_csv(csv_file, index=False)
    
    # Load facilities
    facilities = load_facilities_from_csv(csv_file)
    
    # Verify results
    assert len(facilities) == 3
    assert all(isinstance(f, Facility) for f in facilities)
    assert facilities[0].name == "Club A"
    assert facilities[1].name == "Club B"
    assert facilities[2].name == "Club C"


def test_load_facilities_from_csv_missing_file():
    """Test loading from missing file returns empty list."""
    from scripts.process_data import load_facilities_from_csv
    
    non_existent_file = Path("/tmp/nonexistent.csv")
    facilities = load_facilities_from_csv(non_existent_file)
    
    assert facilities == []


def test_load_facilities_from_csv_empty_file(tmp_path):
    """Test loading from empty CSV file."""
    from scripts.process_data import load_facilities_from_csv
    
    csv_file = tmp_path / "empty.csv"
    # Create CSV with only headers
    df = pd.DataFrame(columns=["place_id", "name", "address", "city", "latitude", "longitude"])
    df.to_csv(csv_file, index=False)
    
    facilities = load_facilities_from_csv(csv_file)
    
    assert facilities == []


# ============================================================================
# TEST GEOGRAPHIC METRICS CALCULATION
# ============================================================================


def test_calculate_geographic_metrics(sample_city_stats, sample_facilities):
    """Test calculating geographic metrics for city stats."""
    from scripts.process_data import calculate_geographic_metrics
    
    # Calculate metrics
    result = calculate_geographic_metrics(sample_city_stats, sample_facilities)
    
    # Verify stats are updated
    assert result is sample_city_stats  # Should return same list
    assert sample_city_stats[0].avg_distance_to_nearest is not None
    assert sample_city_stats[1].avg_distance_to_nearest is not None
    
    # Distance between Albufeira and Faro should be approximately 26-30 km
    assert 25.0 <= sample_city_stats[0].avg_distance_to_nearest <= 30.0


def test_calculate_geographic_metrics_empty_list(sample_facilities):
    """Test calculating metrics with empty city stats list."""
    from scripts.process_data import calculate_geographic_metrics
    
    result = calculate_geographic_metrics([], sample_facilities)
    
    assert result == []


# ============================================================================
# TEST SAVE PROCESSED DATA
# ============================================================================


def test_save_processed_data(tmp_path, sample_facilities, sample_city_stats):
    """Test saving processed data to CSV files."""
    from scripts.process_data import save_processed_data
    
    # Mock settings to use tmp_path
    with patch("scripts.process_data.settings") as mock_settings:
        mock_settings.processed_data_dir = tmp_path
        
        # Save data
        save_processed_data(sample_facilities, sample_city_stats)
        
        # Verify files exist
        facilities_file = tmp_path / "facilities.csv"
        city_stats_file = tmp_path / "city_stats.csv"
        
        assert facilities_file.exists()
        assert city_stats_file.exists()
        
        # Verify content
        facilities_df = pd.read_csv(facilities_file)
        city_stats_df = pd.read_csv(city_stats_file)
        
        assert len(facilities_df) == 3
        assert len(city_stats_df) == 2
        
        # Check that required columns exist
        assert "place_id" in facilities_df.columns
        assert "name" in facilities_df.columns
        assert "city" in city_stats_df.columns
        assert "opportunity_score" in city_stats_df.columns


def test_save_processed_data_creates_directory(tmp_path, sample_facilities, sample_city_stats):
    """Test that save_processed_data creates output directory if it doesn't exist."""
    from scripts.process_data import save_processed_data
    
    output_dir = tmp_path / "new_output_dir"
    assert not output_dir.exists()
    
    with patch("scripts.process_data.settings") as mock_settings:
        mock_settings.processed_data_dir = output_dir
        
        save_processed_data(sample_facilities, sample_city_stats)
        
        assert output_dir.exists()


# ============================================================================
# TEST DISPLAY SUMMARY
# ============================================================================


def test_display_summary(sample_city_stats, capsys):
    """Test displaying summary of top cities."""
    from scripts.process_data import display_summary
    
    # Add opportunity scores to city stats
    sample_city_stats[0].opportunity_score = 75.5
    sample_city_stats[1].opportunity_score = 82.3
    
    display_summary(sample_city_stats)
    
    captured = capsys.readouterr()
    
    # Verify output contains expected elements
    assert "Top 5 Cities" in captured.out or "Cities by Opportunity Score" in captured.out
    assert "Faro" in captured.out  # Higher score
    assert "Albufeira" in captured.out
    assert "82.3" in captured.out or "82" in captured.out
    assert "75.5" in captured.out or "75" in captured.out


def test_display_summary_empty_list(capsys):
    """Test displaying summary with empty city stats."""
    from scripts.process_data import display_summary
    
    display_summary([])
    
    captured = capsys.readouterr()
    # Should handle gracefully, either by showing nothing or a message
    assert captured.out is not None


# ============================================================================
# TEST MAIN FUNCTION
# ============================================================================


def test_main_success(tmp_path, sample_csv_data):
    """Test full main function execution with valid data."""
    from scripts.process_data import main
    
    # Setup
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    
    csv_file = raw_dir / "facilities.csv"
    sample_csv_data.to_csv(csv_file, index=False)
    
    with patch("scripts.process_data.settings") as mock_settings:
        mock_settings.raw_data_dir = raw_dir
        mock_settings.processed_data_dir = processed_dir
        
        # Run main
        exit_code = main()
        
        # Verify success
        assert exit_code == 0
        assert processed_dir.exists()
        assert (processed_dir / "facilities.csv").exists()
        assert (processed_dir / "city_stats.csv").exists()


def test_main_missing_raw_data(tmp_path, capsys):
    """Test main function with missing raw data file."""
    from scripts.process_data import main
    
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    with patch("scripts.process_data.settings") as mock_settings:
        mock_settings.raw_data_dir = raw_dir
        
        exit_code = main()
        
        # Should return error code
        assert exit_code == 1
        
        # Check error message
        captured = capsys.readouterr()
        assert "Error" in captured.out or "error" in captured.out.lower()


def test_main_empty_dataset(tmp_path, capsys):
    """Test main function with empty dataset."""
    from scripts.process_data import main
    
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    # Create empty CSV
    csv_file = raw_dir / "facilities.csv"
    df = pd.DataFrame(columns=["place_id", "name", "address", "city", "latitude", "longitude"])
    df.to_csv(csv_file, index=False)
    
    with patch("scripts.process_data.settings") as mock_settings:
        mock_settings.raw_data_dir = raw_dir
        
        exit_code = main()
        
        # Should return error code
        assert exit_code == 1
        
        # Check warning message
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "warning" in captured.out.lower() or "No facilities" in captured.out


# ============================================================================
# TEST INTEGRATION - FULL PIPELINE
# ============================================================================


def test_full_pipeline_integration(tmp_path, sample_csv_data):
    """Integration test for complete data processing pipeline."""
    from scripts.process_data import (
        load_facilities_from_csv,
        calculate_geographic_metrics,
        save_processed_data,
    )
    from src.analyzers.aggregator import CityAggregator
    from src.analyzers.scorer import OpportunityScorer
    
    # Setup
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    
    csv_file = raw_dir / "facilities.csv"
    sample_csv_data.to_csv(csv_file, index=False)
    
    # Execute pipeline
    facilities = load_facilities_from_csv(csv_file)
    assert len(facilities) == 3
    
    # Aggregate
    aggregator = CityAggregator()
    city_stats = aggregator.aggregate(facilities)
    assert len(city_stats) == 2  # Two cities
    
    # Calculate distances
    city_stats = calculate_geographic_metrics(city_stats, facilities)
    assert all(s.avg_distance_to_nearest is not None for s in city_stats)
    
    # Calculate scores
    scorer = OpportunityScorer()
    city_stats = scorer.calculate_scores(city_stats)
    assert all(0 <= s.opportunity_score <= 100 for s in city_stats)
    
    # Sort
    city_stats.sort(key=lambda s: s.opportunity_score, reverse=True)
    assert city_stats[0].opportunity_score >= city_stats[1].opportunity_score
    
    # Save
    with patch("scripts.process_data.settings") as mock_settings:
        mock_settings.processed_data_dir = processed_dir
        save_processed_data(facilities, city_stats)
    
    # Verify
    assert (processed_dir / "facilities.csv").exists()
    assert (processed_dir / "city_stats.csv").exists()
    
    # Verify CSV content
    saved_facilities = pd.read_csv(processed_dir / "facilities.csv")
    saved_city_stats = pd.read_csv(processed_dir / "city_stats.csv")
    
    assert len(saved_facilities) == 3
    assert len(saved_city_stats) == 2
    assert "opportunity_score" in saved_city_stats.columns
    assert saved_city_stats["opportunity_score"].notna().all()

