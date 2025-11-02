"""
Unit tests for data export functionality.

Tests cover CSV export with various edge cases including empty dataframes,
null values, UTF-8 encoding, and concurrent exports.
"""

import time
from pathlib import Path

import pandas as pd
import pytest

from src.utils.exporters import DataExporter


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_facilities_df():
    """
    Sample facilities DataFrame for testing.

    Returns:
        pd.DataFrame: Sample facilities with various data types and null values
    """
    return pd.DataFrame(
        {
            "place_id": ["place1", "place2", "place3"],
            "name": ["Padel Club A", "Padel Club B", "Padel Açúcar"],  # UTF-8 char
            "city": ["Faro", "Lagos", "Albufeira"],
            "rating": [4.5, None, 4.2],  # Include null rating
            "review_count": [100, 50, 75],
            "latitude": [37.0194, 37.1028, 37.0887],
            "longitude": [-7.9304, -8.6729, -8.2479],
        }
    )


@pytest.fixture
def sample_cities_df():
    """
    Sample city statistics DataFrame for testing.

    Returns:
        pd.DataFrame: Sample city statistics with null values
    """
    return pd.DataFrame(
        {
            "city": ["Faro", "Lagos", "Albufeira"],
            "total_facilities": [5, 3, 8],
            "avg_rating": [4.3, None, 4.5],  # Include null rating
            "opportunity_score": [75.5, 82.3, 68.9],
            "population": [64560, None, 40828],  # Include null population
        }
    )


@pytest.fixture
def exporter(tmp_path):
    """
    DataExporter instance with temporary export directory.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        DataExporter: Exporter configured with temp directory
    """
    export_dir = tmp_path / "exports"
    return DataExporter(export_dir=export_dir)


@pytest.fixture
def empty_df():
    """
    Empty DataFrame for testing edge cases.

    Returns:
        pd.DataFrame: Empty dataframe with columns but no rows
    """
    return pd.DataFrame(columns=["col1", "col2", "col3"])


# ============================================================================
# Core Functionality Tests
# ============================================================================


def test_generate_filename_format():
    """Test filename generation with correct timestamp format YYYY-MM-DD_HH-MM-SS-microseconds."""
    prefix = "test_export"
    extension = "csv"

    filename = DataExporter.generate_filename(prefix, extension)

    # Verify format: prefix_YYYY-MM-DD_HH-MM-SS-MICROSECONDS.extension
    assert filename.startswith(f"{prefix}_")
    assert filename.endswith(f".{extension}")

    # Extract timestamp part (between prefix and extension)
    timestamp_part = filename[len(prefix) + 1 : -len(extension) - 1]

    # Verify timestamp format YYYY-MM-DD_HH-MM-SS-MMMMMM (26 characters total)
    assert len(timestamp_part) == 26
    assert timestamp_part[4] == "-"  # Year separator
    assert timestamp_part[7] == "-"  # Month separator
    assert timestamp_part[10] == "_"  # Date-time separator
    assert timestamp_part[13] == "-"  # Hour separator
    assert timestamp_part[16] == "-"  # Minute separator
    assert timestamp_part[19] == "-"  # Second-microsecond separator
    
    # Verify microseconds are 6 digits
    microseconds_part = timestamp_part[20:]
    assert len(microseconds_part) == 6
    assert microseconds_part.isdigit()


def test_generate_filename_default_extension():
    """Test filename generation uses 'csv' as default extension."""
    prefix = "test"
    filename = DataExporter.generate_filename(prefix)

    assert filename.endswith(".csv")


def test_get_export_path(exporter):
    """Test export path construction."""
    filename = "test_file.csv"

    path = exporter.get_export_path(filename)

    # Verify path is Path object
    assert isinstance(path, Path)

    # Verify path contains export directory and filename
    assert path.name == filename
    assert path.parent == exporter.export_dir


def test_export_to_csv_creates_file(exporter, sample_facilities_df):
    """Test CSV file creation with correct data."""
    prefix = "facilities"

    # Export dataframe
    result_path = exporter.export_to_csv(sample_facilities_df, prefix)

    # Verify file was created
    assert result_path.exists()
    assert result_path.is_file()

    # Verify filename format
    assert result_path.name.startswith(f"{prefix}_")
    assert result_path.name.endswith(".csv")

    # Verify data integrity by reading back
    read_df = pd.read_csv(result_path)
    assert len(read_df) == len(sample_facilities_df)
    assert list(read_df.columns) == list(sample_facilities_df.columns)


def test_export_directory_creation(tmp_path, sample_facilities_df):
    """Test automatic creation of export directory if it doesn't exist."""
    # Create exporter with non-existent directory
    export_dir = tmp_path / "new_exports" / "nested" / "directory"
    exporter = DataExporter(export_dir=export_dir)

    # Verify directory doesn't exist yet
    assert not export_dir.exists()

    # Export should create directory
    result_path = exporter.export_to_csv(sample_facilities_df, "test")

    # Verify directory was created
    assert export_dir.exists()
    assert export_dir.is_dir()
    assert result_path.exists()


def test_export_preserves_all_columns(exporter, sample_facilities_df):
    """Test that all DataFrame columns are preserved in CSV export."""
    result_path = exporter.export_to_csv(sample_facilities_df, "test")

    # Read back and verify columns
    read_df = pd.read_csv(result_path)
    assert list(read_df.columns) == list(sample_facilities_df.columns)

    # Verify no extra columns
    assert len(read_df.columns) == len(sample_facilities_df.columns)


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_export_empty_dataframe_raises_error(exporter, empty_df):
    """Test that exporting empty DataFrame raises ValueError."""
    with pytest.raises(ValueError, match="empty|no data"):
        exporter.export_to_csv(empty_df, "empty")


def test_export_respects_filtered_data(exporter, sample_facilities_df):
    """Test that only filtered rows are exported."""
    # Filter dataframe
    filtered_df = sample_facilities_df[sample_facilities_df["city"] == "Faro"]

    # Export filtered data
    result_path = exporter.export_to_csv(filtered_df, "filtered")

    # Read back and verify only filtered rows
    read_df = pd.read_csv(result_path)
    assert len(read_df) == 1
    assert read_df["city"].iloc[0] == "Faro"


def test_null_value_handling(exporter, sample_facilities_df):
    """Test that NaN values are exported as empty strings, not 'NaN' text."""
    # Export dataframe with null values
    result_path = exporter.export_to_csv(sample_facilities_df, "with_nulls")

    # Read CSV as text to check actual content
    with open(result_path, "r", encoding="utf-8") as f:
        csv_content = f.read()

    # Verify 'NaN' text does not appear in CSV
    assert "NaN" not in csv_content

    # Read back as DataFrame and verify nulls are preserved
    read_df = pd.read_csv(result_path)
    # Row with null rating should have NaN in pandas
    assert pd.isna(read_df.loc[read_df["name"] == "Padel Club B", "rating"].iloc[0])


def test_utf8_encoding(exporter, sample_facilities_df):
    """Test that UTF-8 special characters are preserved correctly."""
    # Export dataframe with UTF-8 characters (Açúcar)
    result_path = exporter.export_to_csv(sample_facilities_df, "utf8")

    # Read back with UTF-8 encoding
    read_df = pd.read_csv(result_path, encoding="utf-8")

    # Verify special character is preserved
    assert "Padel Açúcar" in read_df["name"].values


# ============================================================================
# Advanced Tests
# ============================================================================


def test_concurrent_exports_unique_filenames(exporter, sample_facilities_df):
    """Test that rapid consecutive exports generate unique filenames."""
    filenames = []

    # Perform multiple rapid exports
    for i in range(3):
        result_path = exporter.export_to_csv(sample_facilities_df, "concurrent")
        filenames.append(result_path.name)
        # Small delay to ensure timestamp changes
        time.sleep(0.01)

    # Verify all filenames are unique
    assert len(filenames) == len(set(filenames))

    # Verify all files exist
    for filename in filenames:
        assert (exporter.export_dir / filename).exists()


def test_export_without_index(exporter, sample_facilities_df):
    """Test that pandas index is not included in exported CSV."""
    result_path = exporter.export_to_csv(sample_facilities_df, "no_index", include_index=False)

    # Read CSV as text to check for index column
    with open(result_path, "r", encoding="utf-8") as f:
        first_line = f.readline()

    # First column should be 'place_id', not 'Unnamed: 0' or index numbers
    assert first_line.startswith("place_id")


def test_export_with_index_when_requested(exporter, sample_facilities_df):
    """Test that pandas index IS included when explicitly requested."""
    result_path = exporter.export_to_csv(sample_facilities_df, "with_index", include_index=True)

    # Read back
    read_df = pd.read_csv(result_path)

    # Should have one extra column (the index)
    # Note: When reading back, the index becomes first column
    assert len(read_df.columns) == len(sample_facilities_df.columns) + 1


def test_export_returns_path_object(exporter, sample_facilities_df):
    """Test that export method returns a Path object."""
    result = exporter.export_to_csv(sample_facilities_df, "test")

    assert isinstance(result, Path)
    assert result.exists()


def test_export_with_large_dataframe(exporter):
    """Test export handles larger datasets efficiently."""
    # Create larger DataFrame (100 rows)
    large_df = pd.DataFrame(
        {
            "id": range(100),
            "name": [f"Facility {i}" for i in range(100)],
            "rating": [4.0 + (i % 10) / 10 for i in range(100)],
            "city": ["City" + str(i % 5) for i in range(100)],
        }
    )

    result_path = exporter.export_to_csv(large_df, "large")

    # Verify export completed
    assert result_path.exists()

    # Verify data integrity
    read_df = pd.read_csv(result_path)
    assert len(read_df) == 100

