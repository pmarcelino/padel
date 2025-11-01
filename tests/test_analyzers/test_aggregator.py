"""
Unit tests for CityAggregator.

Tests validate city-level aggregation of facility data including rating calculations,
geographic centers, population lookups, and facilities per capita following TDD principles.
"""

from datetime import datetime

import pytest

from src.analyzers.aggregator import CityAggregator
from src.models.city import CityStats
from src.models.facility import Facility


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def facilities_multiple_cities():
    """Create facilities from multiple cities (Albufeira, Faro, Lagos)."""
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
        ),
        Facility(
            place_id="lagos_1",
            name="Club D",
            address="Address D",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6732,
            rating=4.8,
            review_count=120,
        ),
    ]


@pytest.fixture
def facilities_single_city():
    """Create facilities from a single city."""
    return [
        Facility(
            place_id="faro_1",
            name="Faro Club 1",
            address="Address 1",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.5,
            review_count=100,
        ),
        Facility(
            place_id="faro_2",
            name="Faro Club 2",
            address="Address 2",
            city="Faro",
            latitude=37.0200,
            longitude=-7.9300,
            rating=4.0,
            review_count=50,
        ),
    ]


@pytest.fixture
def facilities_with_null_ratings():
    """Create facilities with some null ratings."""
    return [
        Facility(
            place_id="test_1",
            name="Club With Rating",
            address="Address 1",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=100,
        ),
        Facility(
            place_id="test_2",
            name="Club Without Rating",
            address="Address 2",
            city="Albufeira",
            latitude=37.0900,
            longitude=-8.2500,
            rating=None,
            review_count=0,
        ),
    ]


@pytest.fixture
def facilities_all_null_ratings():
    """Create facilities where all have null ratings."""
    return [
        Facility(
            place_id="null_1",
            name="No Rating Club 1",
            address="Address 1",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=None,
            review_count=0,
        ),
        Facility(
            place_id="null_2",
            name="No Rating Club 2",
            address="Address 2",
            city="Faro",
            latitude=37.0200,
            longitude=-7.9300,
            rating=None,
            review_count=0,
        ),
    ]


@pytest.fixture
def facilities_zero_reviews():
    """Create facilities with zero reviews."""
    return [
        Facility(
            place_id="zero_1",
            name="New Club",
            address="Address",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6732,
            rating=None,
            review_count=0,
        ),
    ]


@pytest.fixture
def facilities_unknown_city():
    """Create facilities from a city not in CITY_POPULATIONS."""
    return [
        Facility(
            place_id="unknown_1",
            name="Unknown City Club",
            address="Address",
            city="Unknown City",
            latitude=37.0000,
            longitude=-8.0000,
            rating=4.0,
            review_count=50,
        ),
    ]


@pytest.fixture
def facilities_realistic_sample():
    """Create a realistic sample with 12 facilities across 3 cities."""
    facilities = []
    
    # Albufeira - 5 facilities
    for i in range(5):
        facilities.append(
            Facility(
                place_id=f"alb_{i}",
                name=f"Albufeira Club {i}",
                address=f"Address {i}",
                city="Albufeira",
                latitude=37.088 + i * 0.001,
                longitude=-8.247 + i * 0.001,
                rating=4.0 + i * 0.2 if i < 4 else None,
                review_count=100 + i * 20,
            )
        )
    
    # Faro - 4 facilities
    for i in range(4):
        facilities.append(
            Facility(
                place_id=f"faro_{i}",
                name=f"Faro Club {i}",
                address=f"Address {i}",
                city="Faro",
                latitude=37.019 + i * 0.001,
                longitude=-7.932 + i * 0.001,
                rating=4.5 + i * 0.1,
                review_count=150 + i * 30,
            )
        )
    
    # Lagos - 3 facilities
    for i in range(3):
        facilities.append(
            Facility(
                place_id=f"lagos_{i}",
                name=f"Lagos Club {i}",
                address=f"Address {i}",
                city="Lagos",
                latitude=37.102 + i * 0.001,
                longitude=-8.673 + i * 0.001,
                rating=3.8 + i * 0.3,
                review_count=80 + i * 25,
            )
        )
    
    return facilities


@pytest.fixture
def aggregator():
    """Create a CityAggregator instance."""
    return CityAggregator()


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================


def test_aggregate_empty_list(aggregator):
    """Test that empty facility list returns empty result."""
    result = aggregator.aggregate([])
    assert result == []


def test_aggregate_single_city(aggregator, facilities_single_city):
    """Test aggregation with facilities from a single city."""
    result = aggregator.aggregate(facilities_single_city)
    
    assert len(result) == 1
    assert result[0].city == "Faro"
    assert result[0].total_facilities == 2


def test_aggregate_multiple_cities(aggregator, facilities_multiple_cities):
    """Test aggregation with facilities from multiple cities."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    assert len(result) == 3
    cities = {stats.city for stats in result}
    assert cities == {"Albufeira", "Faro", "Lagos"}


def test_city_grouping(aggregator, facilities_multiple_cities):
    """Test that facilities are correctly grouped by city."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    city_stats_map = {stats.city: stats for stats in result}
    
    assert city_stats_map["Albufeira"].total_facilities == 2
    assert city_stats_map["Faro"].total_facilities == 1
    assert city_stats_map["Lagos"].total_facilities == 1


# ============================================================================
# RATING CALCULATION TESTS
# ============================================================================


def test_avg_rating_calculation(aggregator, facilities_single_city):
    """Test average rating calculation with valid ratings."""
    result = aggregator.aggregate(facilities_single_city)
    
    assert len(result) == 1
    # Expected: (4.5 + 4.0) / 2 = 4.25
    assert result[0].avg_rating == 4.25


def test_median_rating_calculation(aggregator, facilities_multiple_cities):
    """Test median rating calculation."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Albufeira has ratings [4.5, 4.2], median = 4.35
    assert city_stats_map["Albufeira"].median_rating == 4.35


def test_rating_ignores_none(aggregator, facilities_with_null_ratings):
    """Test that null ratings are excluded from calculations."""
    result = aggregator.aggregate(facilities_with_null_ratings)
    
    assert len(result) == 1
    # Should only consider the 4.5 rating, ignoring None
    assert result[0].avg_rating == 4.5
    assert result[0].median_rating == 4.5


def test_no_ratings_returns_none(aggregator, facilities_all_null_ratings):
    """Test that None is returned when all ratings are null."""
    result = aggregator.aggregate(facilities_all_null_ratings)
    
    assert len(result) == 1
    assert result[0].avg_rating is None
    assert result[0].median_rating is None


def test_mixed_ratings(aggregator, facilities_with_null_ratings):
    """Test calculation with mix of null and valid ratings."""
    result = aggregator.aggregate(facilities_with_null_ratings)
    
    assert len(result) == 1
    assert result[0].avg_rating == 4.5
    assert result[0].total_facilities == 2


# ============================================================================
# COUNT CALCULATION TESTS
# ============================================================================


def test_total_facilities_count(aggregator, facilities_multiple_cities):
    """Test correct facility count per city."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    city_stats_map = {stats.city: stats for stats in result}
    
    assert city_stats_map["Albufeira"].total_facilities == 2
    assert city_stats_map["Faro"].total_facilities == 1
    assert city_stats_map["Lagos"].total_facilities == 1


def test_total_reviews_sum(aggregator, facilities_single_city):
    """Test sum of review counts."""
    result = aggregator.aggregate(facilities_single_city)
    
    assert len(result) == 1
    # Expected: 100 + 50 = 150
    assert result[0].total_reviews == 150


def test_zero_reviews(aggregator, facilities_zero_reviews):
    """Test handling of zero review counts."""
    result = aggregator.aggregate(facilities_zero_reviews)
    
    assert len(result) == 1
    assert result[0].total_reviews == 0


# ============================================================================
# GEOGRAPHIC CALCULATION TESTS
# ============================================================================


def test_center_latitude(aggregator, facilities_single_city):
    """Test mean latitude calculation."""
    result = aggregator.aggregate(facilities_single_city)
    
    assert len(result) == 1
    # Expected: (37.0194 + 37.0200) / 2 = 37.0197
    assert abs(result[0].center_lat - 37.0197) < 0.0001


def test_center_longitude(aggregator, facilities_single_city):
    """Test mean longitude calculation."""
    result = aggregator.aggregate(facilities_single_city)
    
    assert len(result) == 1
    # Expected: (-7.9322 + -7.9300) / 2 = -7.9311
    assert abs(result[0].center_lng - (-7.9311)) < 0.0001


def test_geographic_center_single_facility(aggregator):
    """Test geographic center with single facility."""
    facilities = [
        Facility(
            place_id="single",
            name="Single Club",
            address="Address",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.5,
            review_count=100,
        )
    ]
    
    result = aggregator.aggregate(facilities)
    
    assert len(result) == 1
    assert result[0].center_lat == 37.0194
    assert result[0].center_lng == -7.9322


def test_geographic_center_multiple_facilities(aggregator, facilities_multiple_cities):
    """Test geographic center with multiple facilities per city."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Albufeira has 2 facilities: (37.0885, -8.2475) and (37.0900, -8.2500)
    albufeira_stats = city_stats_map["Albufeira"]
    expected_lat = (37.0885 + 37.0900) / 2
    expected_lng = (-8.2475 + -8.2500) / 2
    
    assert abs(albufeira_stats.center_lat - expected_lat) < 0.0001
    assert abs(albufeira_stats.center_lng - expected_lng) < 0.0001


# ============================================================================
# POPULATION & PER CAPITA TESTS
# ============================================================================


def test_population_lookup_known_city(aggregator, facilities_multiple_cities):
    """Test population lookup for known cities."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Verify population from CITY_POPULATIONS
    assert city_stats_map["Albufeira"].population == 42388
    assert city_stats_map["Faro"].population == 64560
    assert city_stats_map["Lagos"].population == 31049


def test_population_lookup_unknown_city(aggregator, facilities_unknown_city):
    """Test population lookup for unknown cities returns None."""
    result = aggregator.aggregate(facilities_unknown_city)
    
    assert len(result) == 1
    assert result[0].population is None


def test_facilities_per_capita_calculation(aggregator, facilities_single_city):
    """Test facilities per capita calculation with correct formula."""
    result = aggregator.aggregate(facilities_single_city)
    
    assert len(result) == 1
    # Faro population: 64,560
    # 2 facilities
    # Expected: (2 / 64560) * 10000 = 0.30979...
    expected = (2 / 64560) * 10000
    assert abs(result[0].facilities_per_capita - expected) < 0.001


def test_facilities_per_capita_none_population(aggregator, facilities_unknown_city):
    """Test facilities per capita when population is None."""
    result = aggregator.aggregate(facilities_unknown_city)
    
    assert len(result) == 1
    assert result[0].facilities_per_capita is None


def test_facilities_per_capita_precision(aggregator, facilities_multiple_cities):
    """Test decimal precision of facilities per capita calculation."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Albufeira: 2 facilities, population 42,388
    # Expected: (2 / 42388) * 10000 = 0.471889...
    albufeira_per_capita = city_stats_map["Albufeira"].facilities_per_capita
    expected = (2 / 42388) * 10000
    assert abs(albufeira_per_capita - expected) < 0.0001


# ============================================================================
# EDGE CASES
# ============================================================================


def test_facility_no_reviews(aggregator, facilities_zero_reviews):
    """Test facility with review_count=0."""
    result = aggregator.aggregate(facilities_zero_reviews)
    
    assert len(result) == 1
    assert result[0].total_reviews == 0
    assert result[0].total_facilities == 1


def test_all_null_ratings(aggregator, facilities_all_null_ratings):
    """Test all facilities with null ratings."""
    result = aggregator.aggregate(facilities_all_null_ratings)
    
    assert len(result) == 1
    assert result[0].avg_rating is None
    assert result[0].median_rating is None
    assert result[0].total_facilities == 2


def test_city_not_in_populations(aggregator, facilities_unknown_city):
    """Test city not in CITY_POPULATIONS dict."""
    result = aggregator.aggregate(facilities_unknown_city)
    
    assert len(result) == 1
    assert result[0].city == "Unknown City"
    assert result[0].population is None
    assert result[0].facilities_per_capita is None


def test_citystats_model_validation(aggregator, facilities_single_city):
    """Test output CityStats objects are valid Pydantic models."""
    result = aggregator.aggregate(facilities_single_city)
    
    assert len(result) == 1
    assert isinstance(result[0], CityStats)
    
    # Verify all required fields are present
    stats = result[0]
    assert stats.city is not None
    assert stats.total_facilities is not None
    assert stats.center_lat is not None
    assert stats.center_lng is not None
    assert stats.total_reviews is not None


def test_realistic_sample(aggregator, facilities_realistic_sample):
    """Test with realistic sample data (12 facilities, 3 cities)."""
    result = aggregator.aggregate(facilities_realistic_sample)
    
    assert len(result) == 3
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Verify counts
    assert city_stats_map["Albufeira"].total_facilities == 5
    assert city_stats_map["Faro"].total_facilities == 4
    assert city_stats_map["Lagos"].total_facilities == 3
    
    # Verify all have valid CityStats
    for stats in result:
        assert isinstance(stats, CityStats)
        assert stats.total_facilities > 0
        assert stats.center_lat is not None
        assert stats.center_lng is not None
        assert stats.population is not None
        assert stats.facilities_per_capita is not None

