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
    """Test that empty facility list returns all 15 cities with zero stats."""
    result = aggregator.aggregate([])
    
    # Should return all 15 Algarve cities with zero stats
    assert len(result) == 15
    
    # All cities should have zero facilities
    for stats in result:
        assert stats.total_facilities == 0
        assert stats.avg_rating is None
        assert stats.median_rating is None
        assert stats.total_reviews == 0
        assert stats.facilities_per_capita == 0.0


def test_aggregate_single_city(aggregator, facilities_single_city):
    """Test aggregation with facilities from a single city."""
    result = aggregator.aggregate(facilities_single_city)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro (has facilities)
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Faro"].total_facilities == 2
    
    # Other cities should have zero facilities
    assert city_stats_map["Albufeira"].total_facilities == 0
    assert city_stats_map["Monchique"].total_facilities == 0


def test_aggregate_multiple_cities(aggregator, facilities_multiple_cities):
    """Test aggregation with facilities from multiple cities."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # All cities should be present
    cities = {stats.city for stats in result}
    assert cities == set(aggregator.CITY_POPULATIONS.keys())
    
    # Cities with facilities
    cities_with_facilities = {stats.city for stats in result if stats.total_facilities > 0}
    assert cities_with_facilities == {"Albufeira", "Faro", "Lagos"}


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
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its rating
    city_stats_map = {stats.city: stats for stats in result}
    # Expected: (4.5 + 4.0) / 2 = 4.25
    assert city_stats_map["Faro"].avg_rating == 4.25


def test_median_rating_calculation(aggregator, facilities_multiple_cities):
    """Test median rating calculation."""
    result = aggregator.aggregate(facilities_multiple_cities)
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Albufeira has ratings [4.5, 4.2], median = 4.35
    assert city_stats_map["Albufeira"].median_rating == 4.35


def test_rating_ignores_none(aggregator, facilities_with_null_ratings):
    """Test that null ratings are excluded from calculations."""
    result = aggregator.aggregate(facilities_with_null_ratings)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Albufeira and check its rating
    city_stats_map = {stats.city: stats for stats in result}
    # Should only consider the 4.5 rating, ignoring None
    assert city_stats_map["Albufeira"].avg_rating == 4.5
    assert city_stats_map["Albufeira"].median_rating == 4.5


def test_no_ratings_returns_none(aggregator, facilities_all_null_ratings):
    """Test that None is returned when all ratings are null."""
    result = aggregator.aggregate(facilities_all_null_ratings)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its rating
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Faro"].avg_rating is None
    assert city_stats_map["Faro"].median_rating is None


def test_mixed_ratings(aggregator, facilities_with_null_ratings):
    """Test calculation with mix of null and valid ratings."""
    result = aggregator.aggregate(facilities_with_null_ratings)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Albufeira and check its stats
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Albufeira"].avg_rating == 4.5
    assert city_stats_map["Albufeira"].total_facilities == 2


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
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its total reviews
    city_stats_map = {stats.city: stats for stats in result}
    # Expected: 100 + 50 = 150
    assert city_stats_map["Faro"].total_reviews == 150


def test_zero_reviews(aggregator, facilities_zero_reviews):
    """Test handling of zero review counts."""
    result = aggregator.aggregate(facilities_zero_reviews)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Lagos and check its total reviews
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Lagos"].total_reviews == 0


# ============================================================================
# GEOGRAPHIC CALCULATION TESTS
# ============================================================================


def test_center_latitude(aggregator, facilities_single_city):
    """Test mean latitude calculation."""
    result = aggregator.aggregate(facilities_single_city)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its center latitude
    city_stats_map = {stats.city: stats for stats in result}
    # Expected: (37.0194 + 37.0200) / 2 = 37.0197
    assert abs(city_stats_map["Faro"].center_lat - 37.0197) < 0.0001


def test_center_longitude(aggregator, facilities_single_city):
    """Test mean longitude calculation."""
    result = aggregator.aggregate(facilities_single_city)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its center longitude
    city_stats_map = {stats.city: stats for stats in result}
    # Expected: (-7.9322 + -7.9300) / 2 = -7.9311
    assert abs(city_stats_map["Faro"].center_lng - (-7.9311)) < 0.0001


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
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its center
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Faro"].center_lat == 37.0194
    assert city_stats_map["Faro"].center_lng == -7.9322


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
    
    # Should return 15 Algarve cities + 1 unknown city = 16
    assert len(result) == 16
    
    # Find Unknown City and check its population
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Unknown City"].population is None


def test_facilities_per_capita_calculation(aggregator, facilities_single_city):
    """Test facilities per capita calculation with correct formula."""
    result = aggregator.aggregate(facilities_single_city)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its facilities per capita
    city_stats_map = {stats.city: stats for stats in result}
    # Faro population: 64,560
    # 2 facilities
    # Expected: (2 / 64560) * 10000 = 0.30979...
    expected = (2 / 64560) * 10000
    assert abs(city_stats_map["Faro"].facilities_per_capita - expected) < 0.001


def test_facilities_per_capita_none_population(aggregator, facilities_unknown_city):
    """Test facilities per capita when population is None."""
    result = aggregator.aggregate(facilities_unknown_city)
    
    # Should return 15 Algarve cities + 1 unknown city = 16
    assert len(result) == 16
    
    # Find Unknown City and check its facilities per capita
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Unknown City"].facilities_per_capita is None


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
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Lagos and check its stats
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Lagos"].total_reviews == 0
    assert city_stats_map["Lagos"].total_facilities == 1


def test_all_null_ratings(aggregator, facilities_all_null_ratings):
    """Test all facilities with null ratings."""
    result = aggregator.aggregate(facilities_all_null_ratings)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # Find Faro and check its stats
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Faro"].avg_rating is None
    assert city_stats_map["Faro"].median_rating is None
    assert city_stats_map["Faro"].total_facilities == 2


def test_city_not_in_populations(aggregator, facilities_unknown_city):
    """Test city not in CITY_POPULATIONS dict."""
    result = aggregator.aggregate(facilities_unknown_city)
    
    # Should return 15 Algarve cities + 1 unknown city = 16
    assert len(result) == 16
    
    # Find Unknown City and check its stats
    city_stats_map = {stats.city: stats for stats in result}
    assert city_stats_map["Unknown City"].city == "Unknown City"
    assert city_stats_map["Unknown City"].population is None
    assert city_stats_map["Unknown City"].facilities_per_capita is None


def test_citystats_model_validation(aggregator, facilities_single_city):
    """Test output CityStats objects are valid Pydantic models."""
    result = aggregator.aggregate(facilities_single_city)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    # All should be valid CityStats
    for stats in result:
        assert isinstance(stats, CityStats)
        
        # Verify all required fields are present
        assert stats.city is not None
        assert stats.total_facilities is not None
        assert stats.center_lat is not None
        assert stats.center_lng is not None
        assert stats.total_reviews is not None


def test_realistic_sample(aggregator, facilities_realistic_sample):
    """Test with realistic sample data (12 facilities, 3 cities)."""
    result = aggregator.aggregate(facilities_realistic_sample)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Verify counts for cities with facilities
    assert city_stats_map["Albufeira"].total_facilities == 5
    assert city_stats_map["Faro"].total_facilities == 4
    assert city_stats_map["Lagos"].total_facilities == 3
    
    # Verify cities without facilities have zero counts
    assert city_stats_map["Monchique"].total_facilities == 0
    assert city_stats_map["Vila Do Bispo"].total_facilities == 0
    
    # Verify all have valid CityStats
    for stats in result:
        assert isinstance(stats, CityStats)
        assert stats.center_lat is not None
        assert stats.center_lng is not None
        assert stats.population is not None


# ============================================================================
# ZERO-FACILITY CITIES TESTS (Story 9.1)
# ============================================================================


def test_unknown_city_with_facilities_included(aggregator):
    """Test that cities not in CITY_POPULATIONS are still included in results."""
    facilities = [
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
        Facility(
            place_id="faro_1",
            name="Faro Club",
            address="Address",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.5,
            review_count=100,
        ),
    ]
    
    result = aggregator.aggregate(facilities)
    
    # Should return 15 Algarve cities + 1 unknown city = 16
    assert len(result) == 16
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Verify unknown city is included with facility stats
    assert "Unknown City" in city_stats_map
    assert city_stats_map["Unknown City"].total_facilities == 1
    assert city_stats_map["Unknown City"].avg_rating == 4.0
    assert city_stats_map["Unknown City"].population is None
    assert city_stats_map["Unknown City"].facilities_per_capita is None
    
    # Verify Faro is included
    assert city_stats_map["Faro"].total_facilities == 1
    assert city_stats_map["Faro"].avg_rating == 4.5


def test_all_15_cities_have_facilities(aggregator):
    """Test regression when all 15 Algarve cities have facilities."""
    facilities = []
    for i, city_name in enumerate(aggregator.CITY_POPULATIONS.keys()):
        facilities.append(
            Facility(
                place_id=f"{city_name}_{i}",
                name=f"{city_name} Club",
                address="Address",
                city=city_name,
                latitude=37.0 + i * 0.01,
                longitude=-8.0 + i * 0.01,
                rating=4.0 + (i % 10) * 0.1,
                review_count=100 + i * 10,
            )
        )
    
    result = aggregator.aggregate(facilities)
    
    # Should return exactly 15 cities
    assert len(result) == 15
    
    # All cities should have 1 facility
    for stats in result:
        assert stats.total_facilities == 1
        assert stats.avg_rating is not None
        assert stats.population is not None
        assert stats.facilities_per_capita > 0


def test_single_city_has_facilities_rest_zero(aggregator):
    """Test boundary case: only one city has facilities, rest have zero."""
    facilities = [
        Facility(
            place_id="alb_1",
            name="Albufeira Club",
            address="Address",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=150,
        )
    ]
    
    result = aggregator.aggregate(facilities)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Albufeira should have 1 facility
    assert city_stats_map["Albufeira"].total_facilities == 1
    assert city_stats_map["Albufeira"].avg_rating == 4.5
    assert city_stats_map["Albufeira"].total_reviews == 150
    
    # All other 14 cities should have zero facilities
    zero_facility_cities = [
        city for city in aggregator.CITY_POPULATIONS.keys() if city != "Albufeira"
    ]
    assert len(zero_facility_cities) == 14
    
    for city_name in zero_facility_cities:
        stats = city_stats_map[city_name]
        assert stats.total_facilities == 0
        assert stats.avg_rating is None
        assert stats.median_rating is None
        assert stats.total_reviews == 0
        assert stats.facilities_per_capita == 0.0


def test_aggregate_empty_returns_all_cities(aggregator):
    """Test that empty facility list returns all 15 Algarve cities with zero stats."""
    result = aggregator.aggregate([])
    
    # Should return all 15 Algarve cities
    assert len(result) == 15
    
    # Verify all cities from CITY_POPULATIONS are present
    result_cities = {stats.city for stats in result}
    expected_cities = set(aggregator.CITY_POPULATIONS.keys())
    assert result_cities == expected_cities
    
    # All cities should have zero facilities
    for stats in result:
        assert stats.total_facilities == 0
        assert stats.avg_rating is None
        assert stats.median_rating is None
        assert stats.total_reviews == 0
        assert stats.facilities_per_capita == 0.0
        assert stats.population is not None
        assert stats.center_lat is not None
        assert stats.center_lng is not None


def test_zero_facility_city_has_correct_stats(aggregator):
    """Test that a city with no facilities has correct zero/null stats and center from CITY_CENTERS."""
    # Create facilities for only Faro
    facilities = [
        Facility(
            place_id="faro_1",
            name="Faro Club",
            address="Address",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.5,
            review_count=100,
        )
    ]
    
    result = aggregator.aggregate(facilities)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Faro should have facility stats
    assert city_stats_map["Faro"].total_facilities == 1
    assert city_stats_map["Faro"].avg_rating == 4.5
    
    # Monchique should have zero stats
    monchique = city_stats_map["Monchique"]
    assert monchique.total_facilities == 0
    assert monchique.avg_rating is None
    assert monchique.median_rating is None
    assert monchique.total_reviews == 0
    assert monchique.facilities_per_capita == 0.0
    assert monchique.population == 5958
    
    # Verify Monchique center comes from CITY_CENTERS, not facility mean
    expected_center = aggregator.CITY_CENTERS["Monchique"]
    assert monchique.center_lat == expected_center["lat"]
    assert monchique.center_lng == expected_center["lng"]


def test_partial_coverage_returns_all_cities(aggregator):
    """Test partial coverage scenario: 3 cities have facilities, 12 don't."""
    # Create facilities for Faro, Lagos, and Albufeira only
    facilities = [
        # Faro - 2 facilities
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
        # Lagos - 1 facility
        Facility(
            place_id="lagos_1",
            name="Lagos Club",
            address="Address",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6732,
            rating=4.8,
            review_count=120,
        ),
        # Albufeira - 2 facilities
        Facility(
            place_id="alb_1",
            name="Albufeira Club 1",
            address="Address 1",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=150,
        ),
        Facility(
            place_id="alb_2",
            name="Albufeira Club 2",
            address="Address 2",
            city="Albufeira",
            latitude=37.0900,
            longitude=-8.2500,
            rating=4.2,
            review_count=80,
        ),
    ]
    
    result = aggregator.aggregate(facilities)
    
    # Should return all 15 cities
    assert len(result) == 15
    
    city_stats_map = {stats.city: stats for stats in result}
    
    # Verify all 15 cities are present
    assert set(city_stats_map.keys()) == set(aggregator.CITY_POPULATIONS.keys())
    
    # Cities with facilities should have correct aggregated stats
    assert city_stats_map["Faro"].total_facilities == 2
    assert city_stats_map["Faro"].avg_rating == 4.25
    assert city_stats_map["Faro"].total_reviews == 150
    
    assert city_stats_map["Lagos"].total_facilities == 1
    assert city_stats_map["Lagos"].avg_rating == 4.8
    assert city_stats_map["Lagos"].total_reviews == 120
    
    assert city_stats_map["Albufeira"].total_facilities == 2
    assert city_stats_map["Albufeira"].avg_rating == 4.35
    assert city_stats_map["Albufeira"].total_reviews == 230
    
    # Cities without facilities should have zero stats
    zero_facility_cities = [
        "Aljezur", "Castro Marim", "Lagoa", "Loulé", "Monchique",
        "Olhão", "Portimão", "São Brás De Alportel", "Silves", 
        "Tavira", "Vila Do Bispo", "Vila Real De Santo António"
    ]
    
    for city_name in zero_facility_cities:
        stats = city_stats_map[city_name]
        assert stats.total_facilities == 0
        assert stats.avg_rating is None
        assert stats.median_rating is None
        assert stats.total_reviews == 0
        assert stats.facilities_per_capita == 0.0
        assert stats.population is not None
        assert stats.center_lat is not None
        assert stats.center_lng is not None

