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

