"""
Unit tests for DataCleaner.

Tests validate facility data cleaning including coordinate validation,
city filtering, and DataFrame conversion following TDD principles.
"""

import logging
from datetime import datetime

import pandas as pd
import pytest

from src.models.facility import Facility
from src.processors.cleaner import DataCleaner


@pytest.fixture
def valid_facility():
    """Create a valid facility within Algarve bounds."""
    return Facility(
        place_id="valid_123",
        name="Padel Club Albufeira",
        address="Rua Test, Albufeira",
        city="Albufeira",
        latitude=37.0885,
        longitude=-8.2475,
        rating=4.5,
        review_count=100,
    )


@pytest.fixture
def invalid_coords_north():
    """Create a facility with latitude too high (above 37.42)."""
    return Facility(
        place_id="invalid_north",
        name="Padel Club North",
        address="Rua North, Faro",
        city="Faro",
        latitude=37.5,
        longitude=-8.0,
        rating=4.0,
        review_count=50,
    )


@pytest.fixture
def invalid_coords_south():
    """Create a facility with latitude too low (below 36.96)."""
    return Facility(
        place_id="invalid_south",
        name="Padel Club South",
        address="Rua South, Lagos",
        city="Lagos",
        latitude=36.9,
        longitude=-8.0,
        rating=4.0,
        review_count=50,
    )


@pytest.fixture
def invalid_coords_east():
    """Create a facility with longitude too high (above -7.4)."""
    return Facility(
        place_id="invalid_east",
        name="Padel Club East",
        address="Rua East, Tavira",
        city="Tavira",
        latitude=37.1,
        longitude=-7.3,
        rating=4.0,
        review_count=50,
    )


@pytest.fixture
def invalid_coords_west():
    """Create a facility with longitude too low (below -9.0)."""
    return Facility(
        place_id="invalid_west",
        name="Padel Club West",
        address="Rua West, Lagos",
        city="Lagos",
        latitude=37.1,
        longitude=-9.1,
        rating=4.0,
        review_count=50,
    )


@pytest.fixture
def no_city_facility():
    """Create a facility with empty city string."""
    return Facility(
        place_id="no_city",
        name="Padel Club No City",
        address="Rua Test",
        city="",
        latitude=37.1,
        longitude=-8.0,
        rating=4.0,
        review_count=50,
    )


@pytest.fixture
def unnormalized_city_facility():
    """Create a facility with unnormalized city name (Pydantic will normalize it)."""
    return Facility(
        place_id="unnormalized",
        name="Padel Club Faro",
        address="Rua Test, Faro",
        city=" faro ",
        latitude=37.0,
        longitude=-8.0,
        rating=4.0,
        review_count=50,
    )


@pytest.fixture
def none_rating_facility():
    """Create a facility with None rating (valid case)."""
    return Facility(
        place_id="none_rating",
        name="Padel Club No Rating",
        address="Rua Test, Portimao",
        city="Portimao",
        latitude=37.1,
        longitude=-8.5,
        rating=None,
        review_count=0,
    )


# ============================================================================
# Test Cases - Phase 2: Red Phase (Failing Tests)
# ============================================================================


def test_valid_facility_passes_through(valid_facility):
    """Test that a valid facility passes through cleaning unchanged."""
    result = DataCleaner.clean_facilities([valid_facility])

    assert len(result) == 1
    assert result[0].place_id == valid_facility.place_id
    assert result[0].city == "Albufeira"
    assert result[0].latitude == 37.0885
    assert result[0].longitude == -8.2475
    assert result[0].rating == 4.5


def test_multiple_valid_facilities(valid_facility, none_rating_facility):
    """Test that multiple valid facilities all pass through."""
    facilities = [valid_facility, none_rating_facility]
    result = DataCleaner.clean_facilities(facilities)

    assert len(result) == 2
    assert result[0].place_id == valid_facility.place_id
    assert result[1].place_id == none_rating_facility.place_id


def test_invalid_latitude_too_high(invalid_coords_north):
    """Test that facility with latitude > 37.42 is filtered out."""
    result = DataCleaner.clean_facilities([invalid_coords_north])

    assert len(result) == 0


def test_invalid_latitude_too_low(invalid_coords_south):
    """Test that facility with latitude < 36.96 is filtered out."""
    result = DataCleaner.clean_facilities([invalid_coords_south])

    assert len(result) == 0


def test_invalid_longitude_too_high(invalid_coords_east):
    """Test that facility with longitude > -7.4 is filtered out."""
    result = DataCleaner.clean_facilities([invalid_coords_east])

    assert len(result) == 0


def test_invalid_longitude_too_low(invalid_coords_west):
    """Test that facility with longitude < -9.0 is filtered out."""
    result = DataCleaner.clean_facilities([invalid_coords_west])

    assert len(result) == 0


def test_empty_city_removed(no_city_facility):
    """Test that facility with empty city string is filtered out."""
    result = DataCleaner.clean_facilities([no_city_facility])

    assert len(result) == 0


def test_city_normalization(unnormalized_city_facility):
    """Test that city name is normalized via Pydantic validator."""
    result = DataCleaner.clean_facilities([unnormalized_city_facility])

    assert len(result) == 1
    # Pydantic normalizes " faro " to "Faro" automatically
    assert result[0].city == "Faro"


def test_none_rating_preserved(none_rating_facility):
    """Test that None rating is preserved (valid case)."""
    result = DataCleaner.clean_facilities([none_rating_facility])

    assert len(result) == 1
    assert result[0].rating is None


def test_empty_input_list():
    """Test that empty input list returns empty list."""
    result = DataCleaner.clean_facilities([])

    assert result == []
    assert isinstance(result, list)


def test_mixed_valid_invalid(valid_facility, invalid_coords_north, invalid_coords_south):
    """Test that list with both valid and invalid returns only valid."""
    facilities = [invalid_coords_north, valid_facility, invalid_coords_south]
    result = DataCleaner.clean_facilities(facilities)

    assert len(result) == 1
    assert result[0].place_id == valid_facility.place_id


def test_to_dataframe_conversion(valid_facility, none_rating_facility):
    """Test that facilities convert to DataFrame with correct structure."""
    facilities = [valid_facility, none_rating_facility]
    df = DataCleaner.to_dataframe(facilities)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "place_id" in df.columns
    assert "city" in df.columns
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "rating" in df.columns
    assert df.iloc[0]["place_id"] == valid_facility.place_id
    # None values become NaN in pandas DataFrames
    assert pd.isna(df.iloc[1]["rating"])


def test_to_dataframe_empty_list():
    """Test that empty list returns empty DataFrame."""
    df = DataCleaner.to_dataframe([])

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_logging_counts(valid_facility, invalid_coords_north, caplog):
    """Test that logging captures count of removed facilities."""
    facilities = [valid_facility, invalid_coords_north]

    with caplog.at_level(logging.INFO):
        result = DataCleaner.clean_facilities(facilities)

    assert len(result) == 1
    # Check that logging contains information about cleaning
    assert any("Cleaned" in record.message for record in caplog.records)
