"""
Unit tests for app business logic (app.core module).

Tests the core business logic functions that power the Streamlit UI:
- Data loading from CSV files
- Data filtering by city and rating
- Metrics calculation
- Error handling and edge cases
"""

import numpy as np
import pandas as pd
import pytest

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_facilities_df():
    """Create sample facilities DataFrame for testing."""
    return pd.DataFrame(
        {
            "place_id": ["place_1", "place_2", "place_3", "place_4"],
            "name": ["Padel Center Albufeira", "Faro Tennis Club", "Lagos Sports", "Albufeira Pro"],
            "address": ["Addr 1, Albufeira", "Addr 2, Faro", "Addr 3, Lagos", "Addr 4, Albufeira"],
            "city": ["Albufeira", "Faro", "Lagos", "Albufeira"],
            "postal_code": ["8200-001", "8000-001", "8600-001", "8200-002"],
            "latitude": [37.0885, 37.0194, 37.1028, 37.0890],
            "longitude": [-8.2475, -7.9322, -8.6729, -8.2480],
            "rating": [4.5, 4.2, 3.8, 4.8],
            "review_count": [100, 80, 45, 120],
            "google_url": ["url1", "url2", "url3", "url4"],
            "facility_type": ["club", "club", "center", "club"],
            "num_courts": [4, 3, 2, 6],
            "indoor_outdoor": ["indoor", "outdoor", "both", "indoor"],
            "phone": ["111", "222", "333", "444"],
            "website": ["web1", "web2", "web3", "web4"],
            "collected_at": ["2024-01-01"] * 4,
            "last_updated": ["2024-01-01"] * 4,
        }
    )


@pytest.fixture
def sample_city_stats_df():
    """Create sample city stats DataFrame for testing."""
    return pd.DataFrame(
        {
            "city": ["Albufeira", "Faro", "Lagos"],
            "total_facilities": [2, 1, 1],
            "avg_rating": [4.65, 4.2, 3.8],
            "median_rating": [4.65, 4.2, 3.8],
            "total_reviews": [220, 80, 45],
            "center_lat": [37.0888, 37.0194, 37.1028],
            "center_lng": [-8.2478, -7.9322, -8.6729],
            "population": [30000, 60000, 25000],
            "facilities_per_capita": [0.067, 0.017, 0.040],
            "avg_distance_to_nearest": [2.5, 5.0, 0.0],
            "opportunity_score": [75.5, 85.2, 65.0],
            "population_weight": [0.25, 0.30, 0.20],
            "saturation_weight": [0.20, 0.25, 0.15],
            "quality_gap_weight": [0.15, 0.18, 0.20],
            "geographic_gap_weight": [0.15, 0.12, 0.10],
        }
    )


@pytest.fixture
def temp_csv_files(tmp_path, sample_facilities_df, sample_city_stats_df):
    """Create temporary CSV files for testing data loading."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)

    facilities_path = processed_dir / "facilities.csv"
    city_stats_path = processed_dir / "city_stats.csv"

    sample_facilities_df.to_csv(facilities_path, index=False)
    sample_city_stats_df.to_csv(city_stats_path, index=False)

    return processed_dir


@pytest.fixture
def empty_facilities_df():
    """Create empty facilities DataFrame with correct schema."""
    return pd.DataFrame(
        columns=[
            "place_id",
            "name",
            "address",
            "city",
            "postal_code",
            "latitude",
            "longitude",
            "rating",
            "review_count",
            "google_url",
            "facility_type",
            "num_courts",
            "indoor_outdoor",
            "phone",
            "website",
            "collected_at",
            "last_updated",
        ]
    )


@pytest.fixture
def empty_city_stats_df():
    """Create empty city stats DataFrame with correct schema."""
    return pd.DataFrame(
        columns=[
            "city",
            "total_facilities",
            "avg_rating",
            "median_rating",
            "total_reviews",
            "center_lat",
            "center_lng",
            "population",
            "facilities_per_capita",
            "avg_distance_to_nearest",
            "opportunity_score",
            "population_weight",
            "saturation_weight",
            "quality_gap_weight",
            "geographic_gap_weight",
        ]
    )


# ============================================================================
# Test Data Loading
# ============================================================================


class TestLoadData:
    """Test data loading functionality."""

    def test_load_data_success(self, temp_csv_files):
        """Test successful loading of both CSV files."""
        from app.core import load_data

        # Pass the base path for testing
        facilities_df, city_stats_df = load_data(base_path=temp_csv_files.parent.parent)

        # Verify both DataFrames are loaded
        assert isinstance(facilities_df, pd.DataFrame)
        assert isinstance(city_stats_df, pd.DataFrame)
        assert len(facilities_df) == 4
        assert len(city_stats_df) == 3

    def test_load_data_missing_facilities_file(self, tmp_path):
        """Test handling of missing facilities.csv file."""
        from app.core import load_data

        # Create directory but no files
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        with pytest.raises(FileNotFoundError) as exc_info:
            load_data(base_path=tmp_path)

        assert "facilities.csv" in str(exc_info.value)

    def test_load_data_missing_city_stats_file(self, tmp_path, sample_facilities_df):
        """Test handling of missing city_stats.csv file."""
        from app.core import load_data

        # Create only facilities file
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        facilities_path = processed_dir / "facilities.csv"
        sample_facilities_df.to_csv(facilities_path, index=False)

        with pytest.raises(FileNotFoundError) as exc_info:
            load_data(base_path=tmp_path)

        assert "city_stats.csv" in str(exc_info.value)

    def test_load_data_malformed_csv(self, tmp_path):
        """Test handling of malformed CSV files."""
        from app.core import load_data

        # Create malformed CSV file
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        facilities_path = processed_dir / "facilities.csv"

        # Write invalid CSV content
        with open(facilities_path, "w") as f:
            f.write("invalid,csv,content\n")
            f.write("missing,columns\n")

        city_stats_path = processed_dir / "city_stats.csv"
        with open(city_stats_path, "w") as f:
            f.write("city\nFaro\n")

        # Should load but with unexpected schema (we won't validate schema in this test)
        # Just verify it doesn't crash completely
        facilities_df, city_stats_df = load_data(base_path=tmp_path)
        assert isinstance(facilities_df, pd.DataFrame)
        assert isinstance(city_stats_df, pd.DataFrame)

    def test_load_data_function_signature_for_caching(self):
        """Test that load_data has no required parameters for st.cache_data compatibility."""
        import inspect

        from app.core import load_data

        sig = inspect.signature(load_data)
        # Function should have no required parameters for caching (all should have defaults)
        required_params = [
            p for p in sig.parameters.values() if p.default == inspect.Parameter.empty
        ]
        assert len(required_params) == 0


# ============================================================================
# Test Data Filtering
# ============================================================================


class TestFilterFacilities:
    """Test facilities filtering functionality."""

    def test_filter_by_single_city(self, sample_facilities_df):
        """Test filtering facilities by a single city."""
        from app.core import filter_facilities

        filtered = filter_facilities(sample_facilities_df, ["Faro"], min_rating=0.0)

        assert len(filtered) == 1
        assert filtered.iloc[0]["city"] == "Faro"

    def test_filter_by_multiple_cities(self, sample_facilities_df):
        """Test filtering facilities by multiple cities."""
        from app.core import filter_facilities

        filtered = filter_facilities(sample_facilities_df, ["Albufeira", "Lagos"], min_rating=0.0)

        assert len(filtered) == 3
        assert set(filtered["city"].unique()) == {"Albufeira", "Lagos"}

    def test_filter_by_all_cities(self, sample_facilities_df):
        """Test filtering with all cities selected."""
        from app.core import filter_facilities

        all_cities = sample_facilities_df["city"].unique().tolist()
        filtered = filter_facilities(sample_facilities_df, all_cities, min_rating=0.0)

        assert len(filtered) == len(sample_facilities_df)

    def test_filter_by_minimum_rating(self, sample_facilities_df):
        """Test filtering by minimum rating threshold."""
        from app.core import filter_facilities

        all_cities = sample_facilities_df["city"].unique().tolist()
        filtered = filter_facilities(sample_facilities_df, all_cities, min_rating=4.0)

        # Should include only facilities with rating >= 4.0
        assert len(filtered) == 3
        assert all(filtered["rating"] >= 4.0)

    def test_filter_by_high_rating_threshold(self, sample_facilities_df):
        """Test filtering with high rating threshold."""
        from app.core import filter_facilities

        all_cities = sample_facilities_df["city"].unique().tolist()
        filtered = filter_facilities(sample_facilities_df, all_cities, min_rating=4.5)

        # Should include only facilities with rating >= 4.5
        assert len(filtered) == 2
        assert all(filtered["rating"] >= 4.5)

    def test_filter_combined_city_and_rating(self, sample_facilities_df):
        """Test combined filtering by city and rating."""
        from app.core import filter_facilities

        filtered = filter_facilities(sample_facilities_df, ["Albufeira"], min_rating=4.5)

        # Should include only Albufeira facilities with rating >= 4.5
        assert len(filtered) == 2
        assert all(filtered["city"] == "Albufeira")
        assert all(filtered["rating"] >= 4.5)

    def test_filter_empty_city_list(self, sample_facilities_df):
        """Test filtering with empty city list returns empty DataFrame."""
        from app.core import filter_facilities

        filtered = filter_facilities(sample_facilities_df, [], min_rating=0.0)

        assert len(filtered) == 0
        assert isinstance(filtered, pd.DataFrame)

    def test_filter_no_results(self, sample_facilities_df):
        """Test filtering that results in zero facilities."""
        from app.core import filter_facilities

        filtered = filter_facilities(sample_facilities_df, ["Faro"], min_rating=5.0)

        # No facility in Faro has rating >= 5.0
        assert len(filtered) == 0
        assert isinstance(filtered, pd.DataFrame)

    def test_filter_empty_dataframe(self, empty_facilities_df):
        """Test filtering an empty DataFrame."""
        from app.core import filter_facilities

        filtered = filter_facilities(empty_facilities_df, ["Albufeira"], min_rating=0.0)

        assert len(filtered) == 0
        assert isinstance(filtered, pd.DataFrame)


class TestFilterCities:
    """Test city stats filtering functionality."""

    def test_filter_cities_single_city(self, sample_city_stats_df):
        """Test filtering city stats by single city."""
        from app.core import filter_cities

        filtered = filter_cities(sample_city_stats_df, ["Faro"])

        assert len(filtered) == 1
        assert filtered.iloc[0]["city"] == "Faro"

    def test_filter_cities_multiple_cities(self, sample_city_stats_df):
        """Test filtering city stats by multiple cities."""
        from app.core import filter_cities

        filtered = filter_cities(sample_city_stats_df, ["Albufeira", "Lagos"])

        assert len(filtered) == 2
        assert set(filtered["city"].unique()) == {"Albufeira", "Lagos"}

    def test_filter_cities_all_cities(self, sample_city_stats_df):
        """Test filtering with all cities selected."""
        from app.core import filter_cities

        all_cities = sample_city_stats_df["city"].unique().tolist()
        filtered = filter_cities(sample_city_stats_df, all_cities)

        assert len(filtered) == len(sample_city_stats_df)

    def test_filter_cities_empty_list(self, sample_city_stats_df):
        """Test filtering with empty city list."""
        from app.core import filter_cities

        filtered = filter_cities(sample_city_stats_df, [])

        assert len(filtered) == 0
        assert isinstance(filtered, pd.DataFrame)

    def test_filter_cities_empty_dataframe(self, empty_city_stats_df):
        """Test filtering empty city stats DataFrame."""
        from app.core import filter_cities

        filtered = filter_cities(empty_city_stats_df, ["Albufeira"])

        assert len(filtered) == 0
        assert isinstance(filtered, pd.DataFrame)


# ============================================================================
# Test Metrics Calculation
# ============================================================================


class TestCalculateMetrics:
    """Test metrics calculation functionality."""

    def test_calculate_metrics_with_data(self, sample_facilities_df, sample_city_stats_df):
        """Test metrics calculation with valid data."""
        from app.core import calculate_metrics

        metrics = calculate_metrics(sample_facilities_df, sample_city_stats_df)

        assert isinstance(metrics, dict)
        assert "total_facilities" in metrics
        assert "avg_rating" in metrics
        assert "total_reviews" in metrics
        assert "top_opportunity_city" in metrics

        # Verify calculated values
        assert metrics["total_facilities"] == 4
        assert metrics["avg_rating"] == pytest.approx(4.325, rel=0.01)  # (4.5+4.2+3.8+4.8)/4
        assert metrics["total_reviews"] == 345  # 100+80+45+120
        assert metrics["top_opportunity_city"] == "Faro"  # highest opportunity_score

    def test_calculate_metrics_empty_facilities(self, empty_facilities_df, sample_city_stats_df):
        """Test metrics calculation with empty facilities DataFrame."""
        from app.core import calculate_metrics

        metrics = calculate_metrics(empty_facilities_df, sample_city_stats_df)

        assert metrics["total_facilities"] == 0
        assert metrics["avg_rating"] == 0.0  # or np.nan, depending on implementation
        assert metrics["total_reviews"] == 0
        # top_opportunity_city should still work based on city_stats_df
        assert metrics["top_opportunity_city"] == "Faro"

    def test_calculate_metrics_empty_cities(self, sample_facilities_df, empty_city_stats_df):
        """Test metrics calculation with empty city stats DataFrame."""
        from app.core import calculate_metrics

        metrics = calculate_metrics(sample_facilities_df, empty_city_stats_df)

        assert metrics["total_facilities"] == 4
        assert metrics["avg_rating"] > 0
        assert metrics["total_reviews"] == 345
        assert metrics["top_opportunity_city"] in ["N/A", None, ""]  # No cities available

    def test_calculate_metrics_both_empty(self, empty_facilities_df, empty_city_stats_df):
        """Test metrics calculation with both DataFrames empty."""
        from app.core import calculate_metrics

        metrics = calculate_metrics(empty_facilities_df, empty_city_stats_df)

        assert metrics["total_facilities"] == 0
        assert metrics["avg_rating"] in [0.0, np.nan] or pd.isna(metrics["avg_rating"])
        assert metrics["total_reviews"] == 0
        assert metrics["top_opportunity_city"] in ["N/A", None, ""]

    def test_calculate_metrics_single_facility(self, sample_city_stats_df):
        """Test metrics calculation with single facility."""
        from app.core import calculate_metrics

        single_facility_df = pd.DataFrame(
            {
                "place_id": ["place_1"],
                "name": ["Test Facility"],
                "city": ["Faro"],
                "rating": [4.5],
                "review_count": [100],
                "address": ["Test Address"],
                "postal_code": ["8000-001"],
                "latitude": [37.0],
                "longitude": [-8.0],
                "google_url": ["url"],
                "facility_type": ["club"],
                "num_courts": [4],
                "indoor_outdoor": ["indoor"],
                "phone": ["123"],
                "website": ["web"],
                "collected_at": ["2024-01-01"],
                "last_updated": ["2024-01-01"],
            }
        )

        metrics = calculate_metrics(single_facility_df, sample_city_stats_df)

        assert metrics["total_facilities"] == 1
        assert metrics["avg_rating"] == 4.5
        assert metrics["total_reviews"] == 100

    def test_calculate_metrics_return_type(self, sample_facilities_df, sample_city_stats_df):
        """Test that calculate_metrics returns correct types."""
        from app.core import calculate_metrics

        metrics = calculate_metrics(sample_facilities_df, sample_city_stats_df)

        assert isinstance(metrics["total_facilities"], (int, np.integer))
        assert isinstance(metrics["avg_rating"], (float, np.floating)) or pd.isna(
            metrics["avg_rating"]
        )
        assert isinstance(metrics["total_reviews"], (int, np.integer))
        assert isinstance(metrics["top_opportunity_city"], str)
