"""
Tests for the CityStats model.

This module contains comprehensive tests for the CityStats Pydantic model,
including validation, field constraints, and calculation methods.
"""

import pytest
from pydantic import ValidationError

from src.models.city import CityStats


class TestCityStatsValidCreation:
    """Test valid CityStats creation scenarios."""

    def test_valid_city_stats_with_required_fields(self) -> None:
        """Test creating city stats with required fields only."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
        )

        assert stats.city == "Albufeira"
        assert stats.total_facilities == 10
        assert stats.center_lat == 37.0885
        assert stats.center_lng == -8.2475
        assert stats.total_reviews == 0  # Default value
        assert stats.opportunity_score == 0.0  # Default value

    def test_valid_city_stats_with_all_fields(self) -> None:
        """Test creating city stats with all fields populated."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            avg_rating=4.2,
            median_rating=4.3,
            total_reviews=1500,
            center_lat=37.0885,
            center_lng=-8.2475,
            population=42388,
            facilities_per_capita=2.36,
            avg_distance_to_nearest=1.5,
            opportunity_score=45.5,
            population_weight=0.65,
            saturation_weight=0.45,
            quality_gap_weight=0.30,
            geographic_gap_weight=0.55,
        )

        assert stats.city == "Albufeira"
        assert stats.total_facilities == 10
        assert stats.avg_rating == 4.2
        assert stats.median_rating == 4.3
        assert stats.total_reviews == 1500
        assert stats.center_lat == 37.0885
        assert stats.center_lng == -8.2475
        assert stats.population == 42388
        assert stats.facilities_per_capita == 2.36
        assert stats.avg_distance_to_nearest == 1.5
        assert stats.opportunity_score == 45.5
        assert stats.population_weight == 0.65
        assert stats.saturation_weight == 0.45
        assert stats.quality_gap_weight == 0.30
        assert stats.geographic_gap_weight == 0.55

    def test_default_values_for_scores_and_weights(self) -> None:
        """Test that scores and weights have correct default values."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
        )

        assert stats.opportunity_score == 0.0
        assert stats.population_weight == 0.0
        assert stats.saturation_weight == 0.0
        assert stats.quality_gap_weight == 0.0
        assert stats.geographic_gap_weight == 0.0


class TestCityStatsRequiredFieldsValidation:
    """Test validation of required fields."""

    def test_missing_city_raises_error(self) -> None:
        """Test that missing city raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
            )
        assert "city" in str(exc_info.value)

    def test_missing_total_facilities_raises_error(self) -> None:
        """Test that missing total_facilities raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                center_lat=37.0885,
                center_lng=-8.2475,
            )
        assert "total_facilities" in str(exc_info.value)

    def test_missing_center_lat_raises_error(self) -> None:
        """Test that missing center_lat raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lng=-8.2475,
            )
        assert "center_lat" in str(exc_info.value)

    def test_missing_center_lng_raises_error(self) -> None:
        """Test that missing center_lng raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
            )
        assert "center_lng" in str(exc_info.value)


class TestCityStatsNumericFieldValidation:
    """Test validation of numeric fields."""

    def test_total_facilities_zero_is_valid(self) -> None:
        """Test that total_facilities of 0 is valid."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=0,
            center_lat=37.0885,
            center_lng=-8.2475,
        )
        assert stats.total_facilities == 0

    def test_negative_total_facilities_raises_error(self) -> None:
        """Test that negative total_facilities raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=-1,
                center_lat=37.0885,
                center_lng=-8.2475,
            )
        assert "total_facilities" in str(exc_info.value)

    def test_total_reviews_zero_is_valid(self) -> None:
        """Test that total_reviews of 0 is valid."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            total_reviews=0,
        )
        assert stats.total_reviews == 0

    def test_negative_total_reviews_raises_error(self) -> None:
        """Test that negative total_reviews raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                total_reviews=-1,
            )
        assert "total_reviews" in str(exc_info.value)

    def test_population_zero_is_valid(self) -> None:
        """Test that population of 0 is valid."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            population=0,
        )
        assert stats.population == 0

    def test_negative_population_raises_error(self) -> None:
        """Test that negative population raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                population=-1,
            )
        assert "population" in str(exc_info.value)


class TestCityStatsRatingValidation:
    """Test rating field validation."""

    def test_valid_avg_rating_range(self) -> None:
        """Test that valid avg_rating range (0-5) is accepted."""
        # Minimum valid rating
        stats_min = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            avg_rating=0.0,
        )
        assert stats_min.avg_rating == 0.0

        # Maximum valid rating
        stats_max = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            avg_rating=5.0,
        )
        assert stats_max.avg_rating == 5.0

    def test_avg_rating_none_is_allowed(self) -> None:
        """Test that avg_rating can be None."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            avg_rating=None,
        )
        assert stats.avg_rating is None

    def test_invalid_avg_rating_below_range_raises_error(self) -> None:
        """Test that avg_rating below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                avg_rating=-0.1,
            )
        assert "avg_rating" in str(exc_info.value)

    def test_invalid_avg_rating_above_range_raises_error(self) -> None:
        """Test that avg_rating above 5 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                avg_rating=5.1,
            )
        assert "avg_rating" in str(exc_info.value)

    def test_valid_median_rating_range(self) -> None:
        """Test that valid median_rating range (0-5) is accepted."""
        # Minimum valid rating
        stats_min = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            median_rating=0.0,
        )
        assert stats_min.median_rating == 0.0

        # Maximum valid rating
        stats_max = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            median_rating=5.0,
        )
        assert stats_max.median_rating == 5.0

    def test_median_rating_none_is_allowed(self) -> None:
        """Test that median_rating can be None."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            median_rating=None,
        )
        assert stats.median_rating is None

    def test_invalid_median_rating_below_range_raises_error(self) -> None:
        """Test that median_rating below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                median_rating=-0.1,
            )
        assert "median_rating" in str(exc_info.value)

    def test_invalid_median_rating_above_range_raises_error(self) -> None:
        """Test that median_rating above 5 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                median_rating=5.1,
            )
        assert "median_rating" in str(exc_info.value)


class TestCityStatsOpportunityScoreValidation:
    """Test opportunity score field validation."""

    def test_opportunity_score_minimum_valid(self) -> None:
        """Test that opportunity_score of 0 is valid."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            opportunity_score=0.0,
        )
        assert stats.opportunity_score == 0.0

    def test_opportunity_score_maximum_valid(self) -> None:
        """Test that opportunity_score of 100 is valid."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            opportunity_score=100.0,
        )
        assert stats.opportunity_score == 100.0

    def test_opportunity_score_below_range_raises_error(self) -> None:
        """Test that opportunity_score below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                opportunity_score=-0.1,
            )
        assert "opportunity_score" in str(exc_info.value)

    def test_opportunity_score_above_range_raises_error(self) -> None:
        """Test that opportunity_score above 100 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                opportunity_score=100.1,
            )
        assert "opportunity_score" in str(exc_info.value)


class TestCityStatsWeightValidation:
    """Test weight field validation (all should be 0-1)."""

    def test_population_weight_valid_range(self) -> None:
        """Test that population_weight range (0-1) is accepted."""
        stats_min = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            population_weight=0.0,
        )
        assert stats_min.population_weight == 0.0

        stats_max = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            population_weight=1.0,
        )
        assert stats_max.population_weight == 1.0

    def test_population_weight_below_range_raises_error(self) -> None:
        """Test that population_weight below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                population_weight=-0.1,
            )
        assert "population_weight" in str(exc_info.value)

    def test_population_weight_above_range_raises_error(self) -> None:
        """Test that population_weight above 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                population_weight=1.1,
            )
        assert "population_weight" in str(exc_info.value)

    def test_saturation_weight_valid_range(self) -> None:
        """Test that saturation_weight range (0-1) is accepted."""
        stats_min = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            saturation_weight=0.0,
        )
        assert stats_min.saturation_weight == 0.0

        stats_max = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            saturation_weight=1.0,
        )
        assert stats_max.saturation_weight == 1.0

    def test_saturation_weight_below_range_raises_error(self) -> None:
        """Test that saturation_weight below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                saturation_weight=-0.1,
            )
        assert "saturation_weight" in str(exc_info.value)

    def test_saturation_weight_above_range_raises_error(self) -> None:
        """Test that saturation_weight above 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                saturation_weight=1.1,
            )
        assert "saturation_weight" in str(exc_info.value)

    def test_quality_gap_weight_valid_range(self) -> None:
        """Test that quality_gap_weight range (0-1) is accepted."""
        stats_min = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            quality_gap_weight=0.0,
        )
        assert stats_min.quality_gap_weight == 0.0

        stats_max = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            quality_gap_weight=1.0,
        )
        assert stats_max.quality_gap_weight == 1.0

    def test_quality_gap_weight_below_range_raises_error(self) -> None:
        """Test that quality_gap_weight below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                quality_gap_weight=-0.1,
            )
        assert "quality_gap_weight" in str(exc_info.value)

    def test_quality_gap_weight_above_range_raises_error(self) -> None:
        """Test that quality_gap_weight above 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                quality_gap_weight=1.1,
            )
        assert "quality_gap_weight" in str(exc_info.value)

    def test_geographic_gap_weight_valid_range(self) -> None:
        """Test that geographic_gap_weight range (0-1) is accepted."""
        stats_min = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            geographic_gap_weight=0.0,
        )
        assert stats_min.geographic_gap_weight == 0.0

        stats_max = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            geographic_gap_weight=1.0,
        )
        assert stats_max.geographic_gap_weight == 1.0

    def test_geographic_gap_weight_below_range_raises_error(self) -> None:
        """Test that geographic_gap_weight below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                geographic_gap_weight=-0.1,
            )
        assert "geographic_gap_weight" in str(exc_info.value)

    def test_geographic_gap_weight_above_range_raises_error(self) -> None:
        """Test that geographic_gap_weight above 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CityStats(
                city="Albufeira",
                total_facilities=10,
                center_lat=37.0885,
                center_lng=-8.2475,
                geographic_gap_weight=1.1,
            )
        assert "geographic_gap_weight" in str(exc_info.value)


class TestCityStatsCalculateOpportunityScore:
    """Test calculate_opportunity_score() method."""

    def test_calculate_opportunity_score_formula(self) -> None:
        """Test that opportunity score is calculated with correct formula."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            population_weight=0.5,
            saturation_weight=0.6,
            quality_gap_weight=0.7,
            geographic_gap_weight=0.8,
        )

        stats.calculate_opportunity_score()

        # Formula: (0.5*0.2 + 0.6*0.3 + 0.7*0.2 + 0.8*0.3) * 100
        # = (0.1 + 0.18 + 0.14 + 0.24) * 100
        # = 0.66 * 100 = 66.0
        expected_score = (0.5 * 0.2 + 0.6 * 0.3 + 0.7 * 0.2 + 0.8 * 0.3) * 100
        assert stats.opportunity_score == pytest.approx(expected_score, rel=1e-9)

    def test_calculate_opportunity_score_with_zero_weights(self) -> None:
        """Test that opportunity score with all zero weights is 0."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            population_weight=0.0,
            saturation_weight=0.0,
            quality_gap_weight=0.0,
            geographic_gap_weight=0.0,
        )

        stats.calculate_opportunity_score()
        assert stats.opportunity_score == 0.0

    def test_calculate_opportunity_score_with_max_weights(self) -> None:
        """Test that opportunity score with all max weights is 100."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            population_weight=1.0,
            saturation_weight=1.0,
            quality_gap_weight=1.0,
            geographic_gap_weight=1.0,
        )

        stats.calculate_opportunity_score()
        # (1.0*0.2 + 1.0*0.3 + 1.0*0.2 + 1.0*0.3) * 100 = 1.0 * 100 = 100.0
        assert stats.opportunity_score == 100.0

    def test_calculate_opportunity_score_updates_existing_score(self) -> None:
        """Test that calculate_opportunity_score updates existing score."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            opportunity_score=50.0,  # Initial value
            population_weight=0.8,
            saturation_weight=0.6,
            quality_gap_weight=0.4,
            geographic_gap_weight=0.2,
        )

        stats.calculate_opportunity_score()

        # Should be recalculated based on weights
        expected_score = (0.8 * 0.2 + 0.6 * 0.3 + 0.4 * 0.2 + 0.2 * 0.3) * 100
        assert stats.opportunity_score == pytest.approx(expected_score, rel=1e-9)
        assert stats.opportunity_score != 50.0  # Should be different from initial

    def test_calculate_opportunity_score_within_bounds(self) -> None:
        """Test that calculated opportunity score stays within 0-100 bounds."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            center_lat=37.0885,
            center_lng=-8.2475,
            population_weight=0.65,
            saturation_weight=0.45,
            quality_gap_weight=0.30,
            geographic_gap_weight=0.55,
        )

        stats.calculate_opportunity_score()

        assert 0.0 <= stats.opportunity_score <= 100.0

    def test_calculate_opportunity_score_example_from_story(self) -> None:
        """Test the example from the story documentation."""
        stats = CityStats(
            city="Albufeira",
            total_facilities=10,
            avg_rating=4.2,
            center_lat=37.0885,
            center_lng=-8.2475,
            population=42388,
            population_weight=0.65,
            saturation_weight=0.45,
            quality_gap_weight=0.30,
            geographic_gap_weight=0.55,
        )

        stats.calculate_opportunity_score()

        # Calculate expected: (0.65*0.2 + 0.45*0.3 + 0.30*0.2 + 0.55*0.3) * 100
        expected_score = (0.65 * 0.2 + 0.45 * 0.3 + 0.30 * 0.2 + 0.55 * 0.3) * 100
        assert stats.opportunity_score == pytest.approx(expected_score, rel=1e-9)
