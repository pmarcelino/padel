"""
Tests for the Facility model.

This module contains comprehensive tests for the Facility Pydantic model,
including validation, field constraints, and serialization methods.
"""

from datetime import datetime
from typing import Optional

import pytest
from pydantic import ValidationError

from src.models.facility import Facility


class TestFacilityValidCreation:
    """Test valid facility creation scenarios."""

    def test_valid_facility_with_required_fields_only(self) -> None:
        """Test creating a facility with only required fields."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        )

        assert facility.place_id == "ChIJ123abc"
        assert facility.name == "Padel Club"
        assert facility.address == "Rua Example, 123"
        assert facility.city == "Albufeira"  # Should be normalized
        assert facility.latitude == 37.0885
        assert facility.longitude == -8.2475
        assert facility.review_count == 0  # Default value

    def test_valid_facility_with_all_fields(self) -> None:
        """Test creating a facility with all fields populated."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club Algarve",
            address="Rua Example, 123",
            city="albufeira",
            postal_code="8200-001",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=150,
            google_url="https://maps.google.com/?cid=123",
            facility_type="club",
            num_courts=6,
            indoor_outdoor="both",
            phone="+351 282 123 456",
            website="https://padel-club.com",
        )

        assert facility.place_id == "ChIJ123abc"
        assert facility.name == "Padel Club Algarve"
        assert facility.postal_code == "8200-001"
        assert facility.rating == 4.5
        assert facility.review_count == 150
        assert facility.num_courts == 6
        assert facility.indoor_outdoor == "both"
        assert facility.phone == "+351 282 123 456"
        assert facility.website == "https://padel-club.com"

    def test_optional_fields_can_be_none(self) -> None:
        """Test that optional fields can be None."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=None,
            postal_code=None,
            google_url=None,
            facility_type=None,
            num_courts=None,
            indoor_outdoor=None,
            phone=None,
            website=None,
        )

        assert facility.rating is None
        assert facility.postal_code is None
        assert facility.google_url is None
        assert facility.facility_type is None
        assert facility.num_courts is None
        assert facility.indoor_outdoor is None
        assert facility.phone is None
        assert facility.website is None

    def test_datetime_auto_generation(self) -> None:
        """Test that collected_at and last_updated are auto-generated."""
        before = datetime.now()
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        )
        after = datetime.now()

        assert facility.collected_at is not None
        assert facility.last_updated is not None
        assert before <= facility.collected_at <= after
        assert before <= facility.last_updated <= after


class TestFacilityRequiredFieldsValidation:
    """Test validation of required fields."""

    def test_missing_place_id_raises_error(self) -> None:
        """Test that missing place_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
            )
        assert "place_id" in str(exc_info.value)

    def test_missing_name_raises_error(self) -> None:
        """Test that missing name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
            )
        assert "name" in str(exc_info.value)

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
            )
        assert "name" in str(exc_info.value)

    def test_missing_latitude_raises_error(self) -> None:
        """Test that missing latitude raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                longitude=-8.2475,
            )
        assert "latitude" in str(exc_info.value)

    def test_missing_longitude_raises_error(self) -> None:
        """Test that missing longitude raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
            )
        assert "longitude" in str(exc_info.value)


class TestFacilityCoordinateValidation:
    """Test coordinate field validation."""

    def test_valid_latitude_boundaries(self) -> None:
        """Test that valid latitude boundaries are accepted."""
        # Minimum valid latitude
        facility_min = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=-90.0,
            longitude=0.0,
        )
        assert facility_min.latitude == -90.0

        # Maximum valid latitude
        facility_max = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=90.0,
            longitude=0.0,
        )
        assert facility_max.latitude == 90.0

    def test_invalid_latitude_below_range_raises_error(self) -> None:
        """Test that latitude below -90 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=-90.1,
                longitude=0.0,
            )
        assert "latitude" in str(exc_info.value)

    def test_invalid_latitude_above_range_raises_error(self) -> None:
        """Test that latitude above 90 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=90.1,
                longitude=0.0,
            )
        assert "latitude" in str(exc_info.value)

    def test_valid_longitude_boundaries(self) -> None:
        """Test that valid longitude boundaries are accepted."""
        # Minimum valid longitude
        facility_min = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=0.0,
            longitude=-180.0,
        )
        assert facility_min.longitude == -180.0

        # Maximum valid longitude
        facility_max = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=0.0,
            longitude=180.0,
        )
        assert facility_max.longitude == 180.0

    def test_invalid_longitude_below_range_raises_error(self) -> None:
        """Test that longitude below -180 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=0.0,
                longitude=-180.1,
            )
        assert "longitude" in str(exc_info.value)

    def test_invalid_longitude_above_range_raises_error(self) -> None:
        """Test that longitude above 180 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=0.0,
                longitude=180.1,
            )
        assert "longitude" in str(exc_info.value)


class TestFacilityRatingValidation:
    """Test rating field validation."""

    def test_valid_rating_range(self) -> None:
        """Test that valid rating range (0-5) is accepted."""
        # Minimum valid rating
        facility_min = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=0.0,
        )
        assert facility_min.rating == 0.0

        # Maximum valid rating
        facility_max = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=5.0,
        )
        assert facility_max.rating == 5.0

    def test_rating_none_is_allowed(self) -> None:
        """Test that rating can be None."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=None,
        )
        assert facility.rating is None

    def test_invalid_rating_below_range_raises_error(self) -> None:
        """Test that rating below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
                rating=-0.1,
            )
        assert "rating" in str(exc_info.value)

    def test_invalid_rating_above_range_raises_error(self) -> None:
        """Test that rating above 5 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
                rating=5.1,
            )
        assert "rating" in str(exc_info.value)


class TestFacilityReviewCountValidation:
    """Test review_count field validation."""

    def test_review_count_default_value(self) -> None:
        """Test that review_count defaults to 0."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        )
        assert facility.review_count == 0

    def test_valid_review_count(self) -> None:
        """Test that valid review_count is accepted."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            review_count=150,
        )
        assert facility.review_count == 150

    def test_review_count_zero_is_valid(self) -> None:
        """Test that review_count of 0 is valid."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            review_count=0,
        )
        assert facility.review_count == 0

    def test_negative_review_count_raises_error(self) -> None:
        """Test that negative review_count raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
                review_count=-1,
            )
        assert "review_count" in str(exc_info.value)


class TestFacilityIndoorOutdoorValidation:
    """Test indoor_outdoor field validation."""

    def test_indoor_outdoor_valid_indoor(self) -> None:
        """Test that 'indoor' is a valid value."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            indoor_outdoor="indoor",
        )
        assert facility.indoor_outdoor == "indoor"

    def test_indoor_outdoor_valid_outdoor(self) -> None:
        """Test that 'outdoor' is a valid value."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            indoor_outdoor="outdoor",
        )
        assert facility.indoor_outdoor == "outdoor"

    def test_indoor_outdoor_valid_both(self) -> None:
        """Test that 'both' is a valid value."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            indoor_outdoor="both",
        )
        assert facility.indoor_outdoor == "both"

    def test_indoor_outdoor_none_is_valid(self) -> None:
        """Test that None is a valid value."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            indoor_outdoor=None,
        )
        assert facility.indoor_outdoor is None

    def test_invalid_indoor_outdoor_raises_error(self) -> None:
        """Test that invalid indoor_outdoor value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
                indoor_outdoor="mixed",
            )
        assert "indoor_outdoor" in str(exc_info.value)

    def test_invalid_indoor_outdoor_case_sensitive(self) -> None:
        """Test that indoor_outdoor is case-sensitive."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
                indoor_outdoor="Indoor",
            )
        assert "indoor_outdoor" in str(exc_info.value)


class TestFacilityCityNormalization:
    """Test city name normalization."""

    def test_city_normalization_lowercase(self) -> None:
        """Test that lowercase city name is normalized to Title Case."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        )
        assert facility.city == "Albufeira"

    def test_city_normalization_uppercase(self) -> None:
        """Test that uppercase city name is normalized to Title Case."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="ALBUFEIRA",
            latitude=37.0885,
            longitude=-8.2475,
        )
        assert facility.city == "Albufeira"

    def test_city_normalization_strips_whitespace(self) -> None:
        """Test that city name whitespace is stripped."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="  albufeira  ",
            latitude=37.0885,
            longitude=-8.2475,
        )
        assert facility.city == "Albufeira"

    def test_city_normalization_multiple_words(self) -> None:
        """Test that multi-word city names are normalized correctly."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="portimão da costa",
            latitude=37.0885,
            longitude=-8.2475,
        )
        assert facility.city == "Portimão Da Costa"


class TestFacilityNumCourtsValidation:
    """Test num_courts field validation."""

    def test_valid_num_courts(self) -> None:
        """Test that valid num_courts is accepted."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            num_courts=6,
        )
        assert facility.num_courts == 6

    def test_num_courts_minimum_valid(self) -> None:
        """Test that num_courts of 1 is valid."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            num_courts=1,
        )
        assert facility.num_courts == 1

    def test_num_courts_zero_raises_error(self) -> None:
        """Test that num_courts of 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
                num_courts=0,
            )
        assert "num_courts" in str(exc_info.value)

    def test_num_courts_negative_raises_error(self) -> None:
        """Test that negative num_courts raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Facility(
                place_id="ChIJ123abc",
                name="Padel Club",
                address="Rua Example, 123",
                city="Albufeira",
                latitude=37.0885,
                longitude=-8.2475,
                num_courts=-1,
            )
        assert "num_courts" in str(exc_info.value)


class TestFacilityToDictMethod:
    """Test to_dict() serialization method."""

    def test_to_dict_includes_all_fields(self) -> None:
        """Test that to_dict() includes all fields."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club Algarve",
            address="Rua Example, 123",
            city="Albufeira",
            postal_code="8200-001",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=150,
            google_url="https://maps.google.com/?cid=123",
            facility_type="club",
            num_courts=6,
            indoor_outdoor="both",
            phone="+351 282 123 456",
            website="https://padel-club.com",
        )

        result = facility.to_dict()

        assert isinstance(result, dict)
        assert result["place_id"] == "ChIJ123abc"
        assert result["name"] == "Padel Club Algarve"
        assert result["address"] == "Rua Example, 123"
        assert result["city"] == "Albufeira"
        assert result["postal_code"] == "8200-001"
        assert result["latitude"] == 37.0885
        assert result["longitude"] == -8.2475
        assert result["rating"] == 4.5
        assert result["review_count"] == 150
        assert result["google_url"] == "https://maps.google.com/?cid=123"
        assert result["facility_type"] == "club"
        assert result["num_courts"] == 6
        assert result["indoor_outdoor"] == "both"
        assert result["phone"] == "+351 282 123 456"
        assert result["website"] == "https://padel-club.com"
        assert "collected_at" in result
        assert "last_updated" in result

    def test_to_dict_converts_datetime_to_iso_format(self) -> None:
        """Test that to_dict() converts datetime fields to ISO format strings."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        )

        result = facility.to_dict()

        # Check that datetime fields are strings in ISO format
        assert isinstance(result["collected_at"], str)
        assert isinstance(result["last_updated"], str)

        # Verify they can be parsed back to datetime
        datetime.fromisoformat(result["collected_at"])
        datetime.fromisoformat(result["last_updated"])

    def test_to_dict_handles_none_values(self) -> None:
        """Test that to_dict() handles None values gracefully."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=None,
            postal_code=None,
            indoor_outdoor=None,
        )

        result = facility.to_dict()

        assert result["rating"] is None
        assert result["postal_code"] is None
        assert result["indoor_outdoor"] is None

    def test_to_dict_numeric_types_remain_numeric(self) -> None:
        """Test that numeric types in to_dict() remain as numbers."""
        facility = Facility(
            place_id="ChIJ123abc",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=150,
            num_courts=6,
        )

        result = facility.to_dict()

        assert isinstance(result["latitude"], float)
        assert isinstance(result["longitude"], float)
        assert isinstance(result["rating"], float)
        assert isinstance(result["review_count"], int)
        assert isinstance(result["num_courts"], int)
