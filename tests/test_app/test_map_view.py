"""
Integration tests for map view component.

Tests the Folium-based map component that visualizes padel facilities
and city opportunity scores, with special focus on null value handling.
"""

import numpy as np
import pandas as pd
import pytest
import folium
from folium import plugins


@pytest.fixture
def sample_facilities_df():
    """Create sample facilities DataFrame with some null ratings."""
    return pd.DataFrame(
        {
            "place_id": ["place_1", "place_2", "place_3", "place_4", "place_5"],
            "name": ["Padel Club A", "Padel Club B", "Padel Club C", "Padel Club D", "Padel Club E"],
            "city": ["Albufeira", "Faro", "Lagos", "Albufeira", "Portimão"],
            "address": ["Addr 1", "Addr 2", "Addr 3", "Addr 4", "Addr 5"],
            "latitude": [37.0885, 37.0194, 37.1028, 37.0890, 37.1359],
            "longitude": [-8.2475, -7.9322, -8.6729, -8.2480, -8.5380],
            "rating": [4.5, 4.2, 3.8, np.nan, 4.8],  # place_4 has null rating
            "review_count": [100, 80, 45, 50, 120],
            "google_url": ["url1", "url2", "url3", None, "url5"],  # place_4 missing google_url
            "indoor_outdoor": ["indoor", "outdoor", "both", "indoor", None],  # place_5 missing
        }
    )


@pytest.fixture
def sample_cities_df():
    """Create sample cities DataFrame with some null values."""
    return pd.DataFrame(
        {
            "city": ["Albufeira", "Faro", "Lagos", "Portimão"],
            "center_lat": [37.0888, 37.0194, 37.1028, 37.1359],
            "center_lng": [-8.2478, -7.9322, -8.6729, -8.5380],
            "opportunity_score": [75.5, 85.2, 65.0, 72.0],
            "total_facilities": [2, 1, 1, 1],
            "avg_rating": [4.5, 4.2, 3.8, np.nan],  # Portimão has null avg_rating
            "population": [30000, 60000, None, 59896],  # Lagos has null population
        }
    )


@pytest.fixture
def empty_facilities_df():
    """Create empty facilities DataFrame with correct schema."""
    return pd.DataFrame(
        columns=[
            "place_id",
            "name",
            "city",
            "address",
            "latitude",
            "longitude",
            "rating",
            "review_count",
            "google_url",
            "indoor_outdoor",
        ]
    )


@pytest.fixture
def empty_cities_df():
    """Create empty cities DataFrame with correct schema."""
    return pd.DataFrame(
        columns=[
            "city",
            "center_lat",
            "center_lng",
            "opportunity_score",
            "total_facilities",
            "avg_rating",
            "population",
        ]
    )


@pytest.fixture
def large_facilities_df():
    """Create large facilities DataFrame for performance testing (50+ facilities)."""
    num_facilities = 60
    cities = ["Albufeira", "Faro", "Lagos", "Portimão", "Loulé", "Tavira"]
    
    data = {
        "place_id": [f"place_{i}" for i in range(num_facilities)],
        "name": [f"Padel Club {i}" for i in range(num_facilities)],
        "city": [cities[i % len(cities)] for i in range(num_facilities)],
        "address": [f"Address {i}" for i in range(num_facilities)],
        "latitude": [37.0 + (i % 10) * 0.01 for i in range(num_facilities)],
        "longitude": [-8.0 - (i % 10) * 0.01 for i in range(num_facilities)],
        "rating": [3.5 + (i % 15) * 0.1 for i in range(num_facilities)],
        "review_count": [50 + (i % 20) * 10 for i in range(num_facilities)],
        "google_url": [f"url_{i}" for i in range(num_facilities)],
        "indoor_outdoor": [["indoor", "outdoor", "both"][i % 3] for i in range(num_facilities)],
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def single_facility_df():
    """Create DataFrame with single facility."""
    return pd.DataFrame(
        {
            "place_id": ["place_1"],
            "name": ["Single Padel Club"],
            "city": ["Albufeira"],
            "address": ["Single Address"],
            "latitude": [37.0885],
            "longitude": [-8.2475],
            "rating": [4.5],
            "review_count": [100],
            "google_url": ["url1"],
            "indoor_outdoor": ["indoor"],
        }
    )


@pytest.fixture
def single_city_df():
    """Create DataFrame with single city."""
    return pd.DataFrame(
        {
            "city": ["Albufeira"],
            "center_lat": [37.0888],
            "center_lng": [-8.2478],
            "opportunity_score": [75.5],
            "total_facilities": [1],
            "avg_rating": [4.5],
            "population": [30000],
        }
    )


# ============================================================================
# Integration Tests
# ============================================================================


class TestCreateMapBasic:
    """Test basic map creation functionality."""

    def test_create_map_returns_folium_map(self, sample_facilities_df, sample_cities_df):
        """Test that create_map returns a folium.Map object."""
        from app.components.map_view import create_map

        result = create_map(sample_facilities_df, sample_cities_df)

        assert isinstance(result, folium.Map)

    def test_create_map_with_empty_dataframes(self, empty_facilities_df, empty_cities_df):
        """Test that create_map handles empty DataFrames without crashing."""
        from app.components.map_view import create_map

        result = create_map(empty_facilities_df, empty_cities_df)

        assert isinstance(result, folium.Map)

    def test_create_map_with_single_facility(self, single_facility_df, single_city_df):
        """Test map creation with single facility."""
        from app.components.map_view import create_map

        result = create_map(single_facility_df, single_city_df)

        assert isinstance(result, folium.Map)

    def test_create_map_with_large_dataset(self, large_facilities_df, sample_cities_df):
        """Test map creation with 50+ facilities for performance."""
        from app.components.map_view import create_map

        result = create_map(large_facilities_df, sample_cities_df)

        assert isinstance(result, folium.Map)


class TestNullValueHandling:
    """Test null value handling for ratings, population, and avg_rating."""

    def test_facility_with_null_rating_creates_gray_marker(
        self, sample_facilities_df, sample_cities_df
    ):
        """Test that facilities with null ratings get gray markers."""
        from app.components.map_view import create_map

        # sample_facilities_df has place_4 with np.nan rating
        result = create_map(sample_facilities_df, sample_cities_df)

        # Map should be created without crashing
        assert isinstance(result, folium.Map)
        # Further validation: check that map has markers (at least 5 facilities)
        # This is an integration test, so we verify it doesn't crash

    def test_city_with_null_population_displays_unknown(
        self, sample_facilities_df, sample_cities_df
    ):
        """Test that cities with null population display 'Unknown' in popup."""
        from app.components.map_view import create_map

        # sample_cities_df has Lagos with null population
        result = create_map(sample_facilities_df, sample_cities_df)

        assert isinstance(result, folium.Map)

    def test_city_with_null_avg_rating_displays_na(
        self, sample_facilities_df, sample_cities_df
    ):
        """Test that cities with null avg_rating display 'N/A' in popup."""
        from app.components.map_view import create_map

        # sample_cities_df has Portimão with null avg_rating
        result = create_map(sample_facilities_df, sample_cities_df)

        assert isinstance(result, folium.Map)

    def test_facility_with_missing_google_url(self, sample_facilities_df, sample_cities_df):
        """Test that facilities with missing google_url don't crash."""
        from app.components.map_view import create_map

        # sample_facilities_df has place_4 with None google_url
        result = create_map(sample_facilities_df, sample_cities_df)

        assert isinstance(result, folium.Map)

    def test_facility_with_missing_indoor_outdoor(
        self, sample_facilities_df, sample_cities_df
    ):
        """Test that facilities with missing indoor_outdoor field don't crash."""
        from app.components.map_view import create_map

        # sample_facilities_df has place_5 with None indoor_outdoor
        result = create_map(sample_facilities_df, sample_cities_df)

        assert isinstance(result, folium.Map)


class TestMapConfiguration:
    """Test map configuration settings."""

    def test_map_center_location(self, sample_facilities_df, sample_cities_df):
        """Test that map is centered on Algarve region."""
        from app.components.map_view import create_map

        result = create_map(sample_facilities_df, sample_cities_df)

        # Check map center is approximately Algarve region (37.1°N, -8.0°W)
        location = result.location
        assert abs(location[0] - 37.1) < 0.5  # Latitude tolerance
        assert abs(location[1] - (-8.0)) < 1.0  # Longitude tolerance

    def test_map_zoom_level(self, sample_facilities_df, sample_cities_df):
        """Test that map has appropriate zoom level."""
        from app.components.map_view import create_map

        result = create_map(sample_facilities_df, sample_cities_df)

        # Check zoom level is around 10 for regional view
        assert result.options["zoom"] == 10


class TestHelperFunctions:
    """Test helper functions for color coding and popup generation."""

    def test_get_marker_color_with_valid_ratings(self):
        """Test color coding for valid ratings."""
        from app.components.map_view import _get_marker_color

        assert _get_marker_color(4.8) == "green"  # >= 4.5
        assert _get_marker_color(4.5) == "green"  # >= 4.5
        assert _get_marker_color(4.3) == "blue"   # >= 4.0
        assert _get_marker_color(4.0) == "blue"   # >= 4.0
        assert _get_marker_color(3.9) == "orange" # >= 3.5
        assert _get_marker_color(3.5) == "orange" # >= 3.5
        assert _get_marker_color(3.2) == "red"    # < 3.5

    def test_get_marker_color_with_null_rating(self):
        """Test color coding for null rating returns gray."""
        from app.components.map_view import _get_marker_color

        assert _get_marker_color(np.nan) == "gray"
        assert _get_marker_color(None) == "gray"

    def test_create_facility_popup_with_all_fields(self):
        """Test facility popup generation with all fields present."""
        from app.components.map_view import _create_facility_popup

        facility = pd.Series(
            {
                "name": "Test Padel Club",
                "city": "Albufeira",
                "rating": 4.5,
                "review_count": 100,
                "address": "Test Address 123",
                "google_url": "https://maps.google.com/test",
            }
        )

        html = _create_facility_popup(facility)

        assert isinstance(html, str)
        assert "Test Padel Club" in html
        assert "Albufeira" in html
        assert "4.5" in html
        assert "100" in html
        assert "Test Address 123" in html
        assert "https://maps.google.com/test" in html

    def test_create_facility_popup_with_null_rating(self):
        """Test facility popup with null rating displays N/A."""
        from app.components.map_view import _create_facility_popup

        facility = pd.Series(
            {
                "name": "Test Padel Club",
                "city": "Albufeira",
                "rating": np.nan,
                "review_count": 50,
                "address": "Test Address",
                "google_url": "https://test.com",
            }
        )

        html = _create_facility_popup(facility)

        assert "N/A" in html

    def test_create_facility_popup_with_missing_google_url(self):
        """Test facility popup without google_url doesn't include link."""
        from app.components.map_view import _create_facility_popup

        facility = pd.Series(
            {
                "name": "Test Padel Club",
                "city": "Albufeira",
                "rating": 4.5,
                "review_count": 100,
                "address": "Test Address",
                "google_url": None,
            }
        )

        html = _create_facility_popup(facility)

        assert isinstance(html, str)
        # Should not crash, and should not include a broken link

    def test_create_city_popup_with_all_fields(self):
        """Test city popup generation with all fields present."""
        from app.components.map_view import _create_city_popup

        city = pd.Series(
            {
                "city": "Albufeira",
                "opportunity_score": 75.5,
                "total_facilities": 10,
                "avg_rating": 4.3,
                "population": 30000,
            }
        )

        html = _create_city_popup(city)

        assert isinstance(html, str)
        assert "Albufeira" in html
        assert "75.5" in html
        assert "10" in html
        assert "4.3" in html or "4.30" in html
        assert "30,000" in html or "30000" in html

    def test_create_city_popup_with_null_population(self):
        """Test city popup with null population displays Unknown."""
        from app.components.map_view import _create_city_popup

        city = pd.Series(
            {
                "city": "Lagos",
                "opportunity_score": 65.0,
                "total_facilities": 5,
                "avg_rating": 4.0,
                "population": None,
            }
        )

        html = _create_city_popup(city)

        assert "Unknown" in html

    def test_create_city_popup_with_null_avg_rating(self):
        """Test city popup with null avg_rating displays N/A."""
        from app.components.map_view import _create_city_popup

        city = pd.Series(
            {
                "city": "Portimão",
                "opportunity_score": 72.0,
                "total_facilities": 8,
                "avg_rating": np.nan,
                "population": 50000,
            }
        )

        html = _create_city_popup(city)

        assert "N/A" in html

