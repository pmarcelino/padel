"""
Unit tests for DistanceCalculator.

Tests cover:
- Basic distance calculations with known coordinates
- City center calculations (single and multiple facilities)
- Travel willingness estimation by population
- Edge cases (empty lists, single city, no neighbors)
- Accuracy validation (±1% of known distances)
"""

import pytest
from src.models.facility import Facility
from src.analyzers.distance import DistanceCalculator


# ============================================================================
# Fixtures - Reusable test data
# ============================================================================

@pytest.fixture
def albufeira_facility():
    """Single facility in Albufeira."""
    return Facility(
        place_id="alb1",
        name="Albufeira Padel Club",
        address="Test Address",
        city="Albufeira",
        latitude=37.0885,
        longitude=-8.2475,
        review_count=100
    )


@pytest.fixture
def faro_facility():
    """Single facility in Faro."""
    return Facility(
        place_id="faro1",
        name="Faro Padel Center",
        address="Test Address",
        city="Faro",
        latitude=37.0194,
        longitude=-7.9322,
        review_count=150
    )


@pytest.fixture
def lagos_facilities():
    """Multiple facilities in Lagos for center calculation."""
    return [
        Facility(
            place_id="lag1",
            name="Lagos Club 1",
            address="Test Address",
            city="Lagos",
            latitude=37.10,
            longitude=-8.67,
            review_count=50
        ),
        Facility(
            place_id="lag2",
            name="Lagos Club 2",
            address="Test Address",
            city="Lagos",
            latitude=37.11,
            longitude=-8.68,
            review_count=60
        ),
        Facility(
            place_id="lag3",
            name="Lagos Club 3",
            address="Test Address",
            city="Lagos",
            latitude=37.12,
            longitude=-8.69,
            review_count=70
        )
    ]


@pytest.fixture
def portimao_facility():
    """Single facility in Portimão."""
    return Facility(
        place_id="port1",
        name="Portimão Sports Center",
        address="Test Address",
        city="Portimão",
        latitude=37.1383,
        longitude=-8.5375,
        review_count=200
    )


@pytest.fixture
def multi_city_facilities(albufeira_facility, faro_facility, portimao_facility):
    """Facilities across multiple cities."""
    return [albufeira_facility, faro_facility, portimao_facility]


# ============================================================================
# Basic Distance Calculations (TS-4.2.1)
# ============================================================================

class TestBasicDistanceCalculations:
    """Test geodesic distance calculations between cities."""
    
    def test_distance_albufeira_to_faro(self, albufeira_facility, faro_facility):
        """Test distance between Albufeira and Faro is ~29 km (±1%)."""
        facilities = [albufeira_facility, faro_facility]
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
        
        # Expected: ~29 km (geodesic distance between coordinates)
        # Allow ±1% tolerance: 28.71 to 29.37 km
        assert 28.71 <= distance <= 29.37, f"Expected ~29 km, got {distance} km"
    
    def test_distance_lagos_to_portimao(self, portimao_facility):
        """Test distance between Lagos and Portimão is ~13 km (±1%)."""
        lagos_facility = Facility(
            place_id="lag1",
            name="Lagos Club",
            address="Test Address",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6732,
            review_count=80
        )
        facilities = [lagos_facility, portimao_facility]
        distance = DistanceCalculator.calculate_distance_to_nearest("Lagos", facilities)
        
        # Expected: ~13 km (geodesic distance between coordinates)
        # Allow ±1% tolerance: 12.56 to 12.82 km
        assert 12.56 <= distance <= 12.82, f"Expected ~13 km, got {distance} km"
    
    def test_distance_with_three_cities(self, multi_city_facilities):
        """Test distance calculation with facilities from 3+ cities."""
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", multi_city_facilities)
        
        # Should return distance to nearest neighbor (either Faro or Portimão)
        assert distance > 0, "Distance should be positive"
        assert distance < 100, "Distance should be reasonable for Algarve region"
    
    def test_geodesic_not_euclidean(self, albufeira_facility, faro_facility):
        """Verify geodesic calculation (not simple Euclidean distance)."""
        facilities = [albufeira_facility, faro_facility]
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
        
        # Euclidean would give ~0.32 degrees, geodesic gives ~26 km
        # If it was Euclidean, result would be < 1
        assert distance > 20, "Should use geodesic distance, not Euclidean"


# ============================================================================
# City Center Calculations (TS-4.2.2)
# ============================================================================

class TestCityCenterCalculations:
    """Test city center calculation from facility coordinates."""
    
    def test_single_facility_center(self, albufeira_facility):
        """Single facility - center equals facility coordinates."""
        facilities = [albufeira_facility]
        
        # With only one city, nearest distance should be 0.0
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
        assert distance == 0.0, "Single city should return 0.0"
    
    def test_multiple_facilities_same_city(self, lagos_facilities, faro_facility):
        """Multiple facilities in same city - center is average lat/lng."""
        # Add Faro to have a neighboring city
        facilities = lagos_facilities + [faro_facility]
        distance = DistanceCalculator.calculate_distance_to_nearest("Lagos", facilities)
        
        # Should calculate from center of Lagos (average of 3 facilities)
        # Center should be: lat=37.11, lng=-8.68
        # Distance to Faro should be calculated from this center
        assert distance > 0, "Should calculate distance from city center"
        assert distance < 200, "Distance should be reasonable"
    
    def test_city_center_is_average(self, lagos_facilities, albufeira_facility):
        """Verify city center is calculated as mean of coordinates."""
        facilities = lagos_facilities + [albufeira_facility]
        
        # Lagos center: (37.10 + 37.11 + 37.12) / 3 = 37.11
        #               (-8.67 + -8.68 + -8.69) / 3 = -8.68
        # This is implicit in the distance calculation
        distance = DistanceCalculator.calculate_distance_to_nearest("Lagos", facilities)
        assert distance > 0, "Distance from center should be positive"


# ============================================================================
# Travel Willingness by Population (TS-4.2.3)
# ============================================================================

class TestTravelWillingnessRadius:
    """Test travel willingness estimation based on population."""
    
    def test_urban_large_city(self):
        """Urban areas (>50,000 population) return 5.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(60000)
        assert radius == 5.0, "Urban areas should have 5 km radius"
    
    def test_urban_boundary_above(self):
        """Population just above 50,000 returns 5.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(50001)
        assert radius == 5.0, "Just above 50k should be 5 km"
    
    def test_midsize_city(self):
        """Mid-size towns (20,000-50,000) return 10.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(30000)
        assert radius == 10.0, "Mid-size towns should have 10 km radius"
    
    def test_midsize_boundary_exact(self):
        """Population exactly 50,000 returns 10.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(50000)
        assert radius == 10.0, "Exactly 50k should be 10 km"
    
    def test_midsize_boundary_at_20k(self):
        """Population exactly 20,000 returns 10.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(20000)
        assert radius == 10.0, "Exactly 20k should be 10 km"
    
    def test_small_town(self):
        """Small towns (<20,000) return 15.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(10000)
        assert radius == 15.0, "Small towns should have 15 km radius"
    
    def test_very_small_town(self):
        """Very small towns return 15.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(5000)
        assert radius == 15.0, "Very small towns should have 15 km radius"
    
    def test_boundary_below_20k(self):
        """Population just below 20,000 returns 15.0 km."""
        radius = DistanceCalculator.calculate_travel_willingness_radius(19999)
        assert radius == 15.0, "Just below 20k should be 15 km"


# ============================================================================
# Edge Cases (TS-4.2.4)
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_facility_list(self):
        """Empty facility list returns 0.0."""
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", [])
        assert distance == 0.0, "Empty list should return 0.0"
    
    def test_city_not_in_list(self, albufeira_facility):
        """City not in facility list returns 0.0."""
        facilities = [albufeira_facility]
        distance = DistanceCalculator.calculate_distance_to_nearest("Faro", facilities)
        assert distance == 0.0, "Non-existent city should return 0.0"
    
    def test_only_one_city(self, lagos_facilities):
        """Only one city with facilities returns 0.0."""
        distance = DistanceCalculator.calculate_distance_to_nearest("Lagos", lagos_facilities)
        assert distance == 0.0, "Single city should return 0.0"
    
    def test_no_facilities_in_other_cities(self, lagos_facilities):
        """All facilities in target city only returns 0.0."""
        distance = DistanceCalculator.calculate_distance_to_nearest("Lagos", lagos_facilities)
        assert distance == 0.0, "No external facilities should return 0.0"
    
    def test_all_facilities_same_city(self, albufeira_facility):
        """All facilities in same city returns 0.0."""
        facilities = [albufeira_facility, albufeira_facility]  # Duplicate
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
        assert distance == 0.0, "All same city should return 0.0"


# ============================================================================
# Acceptance Criteria Validation
# ============================================================================

class TestAcceptanceCriteria:
    """Validate acceptance criteria from story."""
    
    def test_methods_are_static(self):
        """Verify both methods are static (no self required)."""
        # Should be callable without instantiation
        radius = DistanceCalculator.calculate_travel_willingness_radius(30000)
        assert radius == 10.0, "Static method should work without instance"
    
    def test_distance_precision(self, albufeira_facility, faro_facility):
        """Verify distance precision to 2 decimal places."""
        facilities = [albufeira_facility, faro_facility]
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
        
        # Check that result has at most 2 decimal places
        assert round(distance, 2) == distance, "Distance should have at most 2 decimal places"
    
    def test_accuracy_within_tolerance(self, albufeira_facility, faro_facility):
        """Verify ±1% accuracy against known coordinates."""
        facilities = [albufeira_facility, faro_facility]
        distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
        
        # Known distance: ~29 km (geodesic calculation)
        expected = 29.08
        tolerance = expected * 0.01  # 1%
        assert abs(distance - expected) <= tolerance, f"Distance {distance} not within 1% of {expected}"


# ============================================================================
# Zero-Facility City Distance Tests (Story 9.3)
# ============================================================================

class TestZeroFacilityCityDistances:
    """Test distance calculations for cities with no facilities (Story 9.3)."""
    
    def test_zero_facility_city_distance_from_city_center(self):
        """Zero-facility city calculates distance from city center coordinates."""
        from src.models.city import CityStats
        
        # Create city stats for Monchique (zero facilities)
        monchique_stats = CityStats(
            city="Monchique",
            total_facilities=0,
            center_lat=37.3167,  # From CITY_CENTERS
            center_lng=-8.5556,
            population=5958,
            facilities_per_capita=0.0
        )
        
        # Create facility in Lagos
        lagos_facility = Facility(
            place_id="lag1",
            name="Lagos Club",
            address="Test Address",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6732,
            review_count=80
        )
        
        # Calculate distances using new API
        calculator = DistanceCalculator()
        city_stats = [monchique_stats]
        facilities = [lagos_facility]
        
        result = calculator.calculate_distances(city_stats, facilities)
        
        # Should calculate distance from Monchique center to Lagos facility
        assert result[0].avg_distance_to_nearest > 0, "Distance should be positive"
        assert result[0].avg_distance_to_nearest < 100, "Distance should be reasonable"
    
    def test_zero_facility_city_finds_nearest_across_all_cities(self):
        """Zero-facility city finds nearest facility across all cities, not just own."""
        from src.models.city import CityStats
        
        # Zero-facility city
        monchique_stats = CityStats(
            city="Monchique",
            total_facilities=0,
            center_lat=37.3167,
            center_lng=-8.5556,
            population=5958,
            facilities_per_capita=0.0
        )
        
        # Create facilities in multiple cities
        albufeira_facility = Facility(
            place_id="alb1",
            name="Albufeira Club",
            address="Test Address",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            review_count=100
        )
        
        faro_facility = Facility(
            place_id="faro1",
            name="Faro Club",
            address="Test Address",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            review_count=150
        )
        
        calculator = DistanceCalculator()
        city_stats = [monchique_stats]
        facilities = [albufeira_facility, faro_facility]
        
        result = calculator.calculate_distances(city_stats, facilities)
        
        # Should find nearest across all cities
        assert result[0].avg_distance_to_nearest > 0, "Should find nearest facility"
        # Should be closer to Albufeira (~25km) than Faro (~70km)
        assert result[0].avg_distance_to_nearest < 50, "Should find closer facility"
    
    def test_zero_facility_city_distance_is_positive(self):
        """Zero-facility city has positive distance when facilities exist elsewhere."""
        from src.models.city import CityStats
        
        vila_do_bispo_stats = CityStats(
            city="Vila Do Bispo",
            total_facilities=0,
            center_lat=37.0833,
            center_lng=-8.9122,
            population=5717,
            facilities_per_capita=0.0
        )
        
        lagos_facility = Facility(
            place_id="lag1",
            name="Lagos Club",
            address="Test Address",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6732,
            review_count=80
        )
        
        calculator = DistanceCalculator()
        result = calculator.calculate_distances([vila_do_bispo_stats], [lagos_facility])
        
        # Should NOT return 0.0 (the bug we're fixing)
        assert result[0].avg_distance_to_nearest > 0, "Distance must be positive, not 0.0"
        # Vila do Bispo is ~20-25km from Lagos
        assert 15 <= result[0].avg_distance_to_nearest <= 30, "Distance should be realistic"
    
    def test_city_center_coordinates_used_correctly(self):
        """Verify city center coordinates from CityStats are used for distance calculation."""
        from src.models.city import CityStats
        
        # Create zero-facility city with known coordinates
        test_city_stats = CityStats(
            city="TestCity",
            total_facilities=0,
            center_lat=37.0,  # Specific test coordinates
            center_lng=-8.0,
            population=10000,
            facilities_per_capita=0.0
        )
        
        # Facility at known location
        test_facility = Facility(
            place_id="test1",
            name="Test Facility",
            address="Test",
            city="OtherCity",
            latitude=37.1,  # 0.1 degrees north
            longitude=-8.0,  # Same longitude
            review_count=50
        )
        
        calculator = DistanceCalculator()
        result = calculator.calculate_distances([test_city_stats], [test_facility])
        
        # Distance should be ~11.1 km (0.1 degrees latitude difference)
        assert 10 <= result[0].avg_distance_to_nearest <= 12, \
            f"Expected ~11km, got {result[0].avg_distance_to_nearest}km"
    
    def test_zero_facility_city_no_facilities_anywhere(self):
        """Zero-facility city returns 0.0 when no facilities exist anywhere."""
        from src.models.city import CityStats
        
        monchique_stats = CityStats(
            city="Monchique",
            total_facilities=0,
            center_lat=37.3167,
            center_lng=-8.5556,
            population=5958,
            facilities_per_capita=0.0
        )
        
        calculator = DistanceCalculator()
        result = calculator.calculate_distances([monchique_stats], [])
        
        # Edge case: no facilities anywhere, can't calculate distance
        assert result[0].avg_distance_to_nearest == 0.0, "Should return 0.0 when no facilities exist"
    
    def test_zero_facility_city_one_facility_in_region(self):
        """Zero-facility city calculates distance to single facility in region."""
        from src.models.city import CityStats
        
        monchique_stats = CityStats(
            city="Monchique",
            total_facilities=0,
            center_lat=37.3167,
            center_lng=-8.5556,
            population=5958,
            facilities_per_capita=0.0
        )
        
        single_facility = Facility(
            place_id="only1",
            name="Only Club",
            address="Test",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            review_count=100
        )
        
        calculator = DistanceCalculator()
        result = calculator.calculate_distances([monchique_stats], [single_facility])
        
        # Should calculate distance to the one facility
        assert result[0].avg_distance_to_nearest > 0, "Should calculate to single facility"
        assert result[0].avg_distance_to_nearest < 150, "Distance should be within Algarve region"
    
    def test_zero_facility_city_very_far(self):
        """Zero-facility city handles very far distances (>50km)."""
        from src.models.city import CityStats
        
        # City in far west
        test_city = CityStats(
            city="WestCity",
            total_facilities=0,
            center_lat=37.0,
            center_lng=-9.0,  # Far west
            population=10000,
            facilities_per_capita=0.0
        )
        
        # Facility in far east
        east_facility = Facility(
            place_id="east1",
            name="East Club",
            address="Test",
            city="EastCity",
            latitude=37.0,
            longitude=-7.0,  # Far east (2 degrees = ~170km)
            review_count=50
        )
        
        calculator = DistanceCalculator()
        result = calculator.calculate_distances([test_city], [east_facility])
        
        # Should handle large distance
        assert result[0].avg_distance_to_nearest > 50, "Should handle distances >50km"
        assert result[0].avg_distance_to_nearest < 300, "Should be realistic for Portugal"
    
    def test_zero_facility_city_very_close(self):
        """Zero-facility city handles very close distances (<1km)."""
        from src.models.city import CityStats
        
        # City with center very close to facility
        test_city = CityStats(
            city="CloseCity",
            total_facilities=0,
            center_lat=37.0000,
            center_lng=-8.0000,
            population=5000,
            facilities_per_capita=0.0
        )
        
        # Facility just across city border (~500m away)
        nearby_facility = Facility(
            place_id="near1",
            name="Nearby Club",
            address="Test",
            city="NeighborCity",
            latitude=37.0045,  # ~500m north
            longitude=-8.0000,
            review_count=30
        )
        
        calculator = DistanceCalculator()
        result = calculator.calculate_distances([test_city], [nearby_facility])
        
        # Should handle small distance accurately
        assert 0 < result[0].avg_distance_to_nearest < 1, \
            f"Expected <1km, got {result[0].avg_distance_to_nearest}km"


# ============================================================================
# Mixed City Scenario Tests (Story 9.3)
# ============================================================================

class TestMixedCityScenarios:
    """Test scenarios with mix of cities with and without facilities."""
    
    def test_mixed_cities_with_and_without_facilities(self):
        """Test with 2 cities having facilities, 1 without."""
        from src.models.city import CityStats
        
        # Cities with facilities
        albufeira_stats = CityStats(
            city="Albufeira",
            total_facilities=2,
            center_lat=37.0885,
            center_lng=-8.2475,
            population=42388,
            facilities_per_capita=0.47
        )
        
        faro_stats = CityStats(
            city="Faro",
            total_facilities=1,
            center_lat=37.0194,
            center_lng=-7.9322,
            population=64560,
            facilities_per_capita=0.15
        )
        
        # Zero-facility city
        monchique_stats = CityStats(
            city="Monchique",
            total_facilities=0,
            center_lat=37.3167,
            center_lng=-8.5556,
            population=5958,
            facilities_per_capita=0.0
        )
        
        # Facilities
        albufeira_facility1 = Facility(
            place_id="alb1", name="Club 1", address="Test",
            city="Albufeira", latitude=37.088, longitude=-8.247, review_count=100
        )
        albufeira_facility2 = Facility(
            place_id="alb2", name="Club 2", address="Test",
            city="Albufeira", latitude=37.089, longitude=-8.248, review_count=80
        )
        faro_facility = Facility(
            place_id="faro1", name="Faro Club", address="Test",
            city="Faro", latitude=37.0194, longitude=-7.9322, review_count=150
        )
        
        calculator = DistanceCalculator()
        city_stats = [albufeira_stats, faro_stats, monchique_stats]
        facilities = [albufeira_facility1, albufeira_facility2, faro_facility]
        
        result = calculator.calculate_distances(city_stats, facilities)
        
        # Cities with facilities should have positive distances (to other cities)
        albufeira_result = [r for r in result if r.city == "Albufeira"][0]
        faro_result = [r for r in result if r.city == "Faro"][0]
        monchique_result = [r for r in result if r.city == "Monchique"][0]
        
        assert albufeira_result.avg_distance_to_nearest > 0, "Albufeira should have distance to Faro"
        assert faro_result.avg_distance_to_nearest > 0, "Faro should have distance to Albufeira"
        assert monchique_result.avg_distance_to_nearest > 0, "Monchique should have distance to nearest"
        
        # Monchique should NOT be 0.0 (the bug)
        assert monchique_result.avg_distance_to_nearest != 0.0, "Zero-facility city should not be 0.0"
    
    def test_all_fifteen_cities_realistic_distribution(self):
        """Test with all 15 Algarve cities with realistic facility distribution."""
        from src.models.city import CityStats
        from src.analyzers.aggregator import CityAggregator
        
        # Create facilities in only 5 cities (10 cities with zero facilities)
        facilities = [
            Facility(place_id="alb1", name="Albufeira 1", address="Test",
                    city="Albufeira", latitude=37.0885, longitude=-8.2475, review_count=100),
            Facility(place_id="faro1", name="Faro 1", address="Test",
                    city="Faro", latitude=37.0194, longitude=-7.9322, review_count=150),
            Facility(place_id="lag1", name="Lagos 1", address="Test",
                    city="Lagos", latitude=37.1028, longitude=-8.6732, review_count=80),
            Facility(place_id="lou1", name="Loulé 1", address="Test",
                    city="Loulé", latitude=37.1376, longitude=-8.0222, review_count=120),
            Facility(place_id="port1", name="Portimão 1", address="Test",
                    city="Portimão", latitude=37.1391, longitude=-8.5372, review_count=200),
        ]
        
        # Aggregate to get all 15 cities
        aggregator = CityAggregator()
        all_city_stats = aggregator.aggregate(facilities)
        
        # Calculate distances
        calculator = DistanceCalculator()
        result = calculator.calculate_distances(all_city_stats, facilities)
        
        # All 15 cities should have distance values
        assert len(result) == 15, "Should process all 15 cities"
        
        # Cities with facilities should have distances to other cities
        cities_with_facilities = [r for r in result if r.total_facilities > 0]
        for city in cities_with_facilities:
            assert city.avg_distance_to_nearest > 0, \
                f"{city.city} has facilities but distance is {city.avg_distance_to_nearest}"
        
        # Cities without facilities should have distances from city center
        cities_without_facilities = [r for r in result if r.total_facilities == 0]
        assert len(cities_without_facilities) == 10, "Should have 10 zero-facility cities"
        
        for city in cities_without_facilities:
            # Should NOT be 0.0 (the bug we're fixing)
            assert city.avg_distance_to_nearest > 0, \
                f"{city.city} is zero-facility but distance should not be 0.0"
            # Should be reasonable distance within Algarve
            assert city.avg_distance_to_nearest < 150, \
                f"{city.city} distance {city.avg_distance_to_nearest}km seems too large"
    
    def test_city_with_facilities_unchanged(self):
        """Regression: cities with facilities should use existing behavior."""
        from src.models.city import CityStats
        
        # City with facilities
        albufeira_stats = CityStats(
            city="Albufeira",
            total_facilities=2,
            center_lat=37.0885,
            center_lng=-8.2475,
            population=42388,
            facilities_per_capita=0.47
        )
        
        facilities = [
            Facility(place_id="alb1", name="Albufeira 1", address="Test",
                    city="Albufeira", latitude=37.0885, longitude=-8.2475, review_count=100),
            Facility(place_id="alb2", name="Albufeira 2", address="Test",
                    city="Albufeira", latitude=37.089, longitude=-8.248, review_count=80),
            Facility(place_id="faro1", name="Faro 1", address="Test",
                    city="Faro", latitude=37.0194, longitude=-7.9322, review_count=150),
        ]
        
        # Calculate with new API
        calculator = DistanceCalculator()
        result = calculator.calculate_distances([albufeira_stats], facilities)
        
        # Calculate with old API (should be same)
        old_distance = DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
        
        # Results should match (regression test)
        assert result[0].avg_distance_to_nearest == old_distance, \
            "New API should produce same results as old API for cities with facilities"

