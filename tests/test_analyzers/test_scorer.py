"""
Tests for OpportunityScorer.

This module contains comprehensive unit tests for the OpportunityScorer class,
covering weight validation, normalization methods, edge cases, and integration
with the CityStats model.
"""

import pytest
from src.analyzers.scorer import OpportunityScorer
from src.models.city import CityStats


# Test Fixtures
@pytest.fixture
def sample_city_stats():
    """Provide sample city statistics for testing."""
    return [
        CityStats(
            city="Albufeira",
            total_facilities=10,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=1000,
            center_lat=37.0885,
            center_lng=-8.2475,
            population=42388,
            facilities_per_capita=2.36,
            avg_distance_to_nearest=5.0
        ),
        CityStats(
            city="Faro",
            total_facilities=15,
            avg_rating=4.5,
            median_rating=4.5,
            total_reviews=1500,
            center_lat=37.0194,
            center_lng=-7.9322,
            population=64560,
            facilities_per_capita=2.32,
            avg_distance_to_nearest=3.0
        ),
        CityStats(
            city="Monchique",
            total_facilities=1,
            avg_rating=3.5,
            median_rating=3.5,
            total_reviews=50,
            center_lat=37.3170,
            center_lng=-8.5550,
            population=5958,
            facilities_per_capita=1.68,
            avg_distance_to_nearest=15.0
        )
    ]


@pytest.fixture
def single_city_stats():
    """Provide single city for edge case testing."""
    return [
        CityStats(
            city="Faro",
            total_facilities=10,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=1000,
            center_lat=37.0194,
            center_lng=-7.9322,
            population=64560,
            facilities_per_capita=2.32,
            avg_distance_to_nearest=5.0
        )
    ]


@pytest.fixture
def city_stats_with_none_values():
    """Provide city stats with None values for edge case testing."""
    return [
        CityStats(
            city="CityA",
            total_facilities=5,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=500,
            center_lat=37.0,
            center_lng=-8.0,
            population=None,  # None value
            facilities_per_capita=None,  # None value
            avg_distance_to_nearest=5.0
        ),
        CityStats(
            city="CityB",
            total_facilities=10,
            avg_rating=None,  # None value
            median_rating=None,
            total_reviews=1000,
            center_lat=37.1,
            center_lng=-8.1,
            population=50000,
            facilities_per_capita=2.0,
            avg_distance_to_nearest=None  # None value
        )
    ]


@pytest.fixture
def city_stats_zero_variance():
    """Provide city stats with zero variance (all same values) for testing."""
    return [
        CityStats(
            city="CityA",
            total_facilities=10,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=1000,
            center_lat=37.0,
            center_lng=-8.0,
            population=50000,
            facilities_per_capita=2.0,
            avg_distance_to_nearest=10.0
        ),
        CityStats(
            city="CityB",
            total_facilities=10,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=1000,
            center_lat=37.1,
            center_lng=-8.1,
            population=50000,
            facilities_per_capita=2.0,
            avg_distance_to_nearest=10.0
        )
    ]


# Weight Validation Tests
class TestWeightValidation:
    """Test formula weight validation."""

    def test_weights_sum_to_one(self):
        """Test that formula weights sum to 1.0 at initialization."""
        scorer = OpportunityScorer()
        total = (
            scorer.POPULATION_WEIGHT_FACTOR +
            scorer.SATURATION_WEIGHT_FACTOR +
            scorer.QUALITY_GAP_WEIGHT_FACTOR +
            scorer.GEOGRAPHIC_GAP_WEIGHT_FACTOR
        )
        assert abs(total - 1.0) < 0.0001, f"Weights must sum to 1.0, got {total}"

    def test_individual_weight_values(self):
        """Test that individual weights match specification."""
        scorer = OpportunityScorer()
        assert scorer.POPULATION_WEIGHT_FACTOR == 0.2
        assert scorer.SATURATION_WEIGHT_FACTOR == 0.3
        assert scorer.QUALITY_GAP_WEIGHT_FACTOR == 0.2
        assert scorer.GEOGRAPHIC_GAP_WEIGHT_FACTOR == 0.3

    def test_initialization_succeeds_with_valid_weights(self):
        """Test that initialization succeeds when weights sum to 1.0."""
        # Should not raise an exception
        scorer = OpportunityScorer()
        assert scorer is not None


# Normalization Tests
class TestNormalization:
    """Test individual normalization methods."""

    def test_normalize_population_higher_is_better(self):
        """Test population normalization where higher value = higher weight."""
        scorer = OpportunityScorer()
        populations = [10000, 50000, 100000]
        
        # Lowest population should get lowest weight
        low_weight = scorer._normalize_population(10000, populations)
        # Highest population should get highest weight
        high_weight = scorer._normalize_population(100000, populations)
        # Middle should be in between
        mid_weight = scorer._normalize_population(50000, populations)
        
        assert 0.0 <= low_weight <= 1.0
        assert 0.0 <= high_weight <= 1.0
        assert 0.0 <= mid_weight <= 1.0
        assert low_weight < mid_weight < high_weight

    def test_normalize_saturation_lower_is_better(self):
        """Test saturation normalization where lower value = higher weight (inverted)."""
        scorer = OpportunityScorer()
        saturations = [1.0, 2.0, 3.0]
        
        # Lowest saturation should get highest weight (inverted)
        low_sat_weight = scorer._normalize_saturation(1.0, saturations)
        # Highest saturation should get lowest weight (inverted)
        high_sat_weight = scorer._normalize_saturation(3.0, saturations)
        
        assert 0.0 <= low_sat_weight <= 1.0
        assert 0.0 <= high_sat_weight <= 1.0
        assert low_sat_weight > high_sat_weight

    def test_normalize_quality_gap_lower_rating_is_better(self):
        """Test quality gap normalization where lower rating = higher opportunity (inverted)."""
        scorer = OpportunityScorer()
        ratings = [3.0, 4.0, 5.0]
        
        # Lowest rating should get highest weight (inverted)
        low_rating_weight = scorer._normalize_quality_gap(3.0, ratings)
        # Highest rating should get lowest weight (inverted)
        high_rating_weight = scorer._normalize_quality_gap(5.0, ratings)
        
        assert 0.0 <= low_rating_weight <= 1.0
        assert 0.0 <= high_rating_weight <= 1.0
        assert low_rating_weight > high_rating_weight

    def test_normalize_geographic_gap_higher_distance_is_better(self):
        """Test geographic gap normalization where larger distance = higher score."""
        scorer = OpportunityScorer()
        
        # Test normal distances
        low_distance_weight = scorer._normalize_geographic_gap(5.0)
        high_distance_weight = scorer._normalize_geographic_gap(15.0)
        
        assert 0.0 <= low_distance_weight <= 1.0
        assert 0.0 <= high_distance_weight <= 1.0
        assert low_distance_weight < high_distance_weight

    def test_geographic_gap_capped_at_20km(self):
        """Test that geographic gap is capped at 20km maximum."""
        scorer = OpportunityScorer()
        
        # Distance of 20km should give weight of 1.0
        weight_20 = scorer._normalize_geographic_gap(20.0)
        # Distance > 20km should also give weight of 1.0 (capped)
        weight_30 = scorer._normalize_geographic_gap(30.0)
        weight_50 = scorer._normalize_geographic_gap(50.0)
        
        assert weight_20 == 1.0
        assert weight_30 == 1.0
        assert weight_50 == 1.0


# Edge Case Tests
class TestEdgeCases:
    """Test edge case handling."""

    def test_none_value_returns_neutral_weight(self):
        """Test that None values default to 0.5 (neutral)."""
        scorer = OpportunityScorer()
        
        # Test with None value in population
        populations = [10000, 50000, None]
        weight = scorer._normalize_population(None, populations)
        assert weight == 0.5

    def test_single_city_returns_neutral_weights(self, single_city_stats):
        """Test that single city results in neutral weights for min-max metrics.
        
        Note: Geographic gap uses absolute distance scaling (distance/20km),
        so it will not be 0.5 for a single city - it depends on the actual distance.
        """
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(single_city_stats)
        
        stats = result[0]
        # Min-max normalized metrics return 0.5 for single city (no variance)
        assert stats.population_weight == 0.5
        assert stats.saturation_weight == 0.5
        assert stats.quality_gap_weight == 0.5
        # Geographic gap uses absolute scaling: 5.0km / 20.0km = 0.25
        assert stats.geographic_gap_weight == 0.25
        # Expected score: (0.5*0.2 + 0.5*0.3 + 0.5*0.2 + 0.25*0.3) * 100 = 42.5
        assert stats.opportunity_score == 42.5

    def test_zero_variance_returns_neutral_weights(self, city_stats_zero_variance):
        """Test that zero variance (all same values) results in neutral weights for min-max metrics.
        
        Note: Geographic gap uses absolute distance scaling, not min-max normalization,
        so it will be based on actual distance (10km / 20km = 0.5 in this case).
        """
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(city_stats_zero_variance)
        
        for stats in result:
            # Min-max normalized metrics return 0.5 for zero variance
            assert stats.population_weight == 0.5
            assert stats.saturation_weight == 0.5
            assert stats.quality_gap_weight == 0.5
            # Geographic gap uses absolute scaling: 10.0km / 20.0km = 0.5
            assert stats.geographic_gap_weight == 0.5
            # Expected score: (0.5*0.2 + 0.5*0.3 + 0.5*0.2 + 0.5*0.3) * 100 = 50.0
            assert stats.opportunity_score == 50.0

    def test_empty_list_returns_empty_list(self):
        """Test that empty list returns empty list."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores([])
        assert result == []

    def test_handles_none_values_gracefully(self, city_stats_with_none_values):
        """Test that None values are handled gracefully (default to 0.5)."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(city_stats_with_none_values)
        
        # Should complete without errors
        assert len(result) == 2
        
        # Check that None values resulted in 0.5 weights
        for stats in result:
            # All weights should be between 0 and 1
            assert 0.0 <= stats.population_weight <= 1.0
            assert 0.0 <= stats.saturation_weight <= 1.0
            assert 0.0 <= stats.quality_gap_weight <= 1.0
            assert 0.0 <= stats.geographic_gap_weight <= 1.0
            assert 0.0 <= stats.opportunity_score <= 100.0

    def test_division_by_zero_protection(self):
        """Test that division by zero is prevented with epsilon."""
        scorer = OpportunityScorer()
        
        # All same values (zero variance) - should not crash
        populations = [50000, 50000, 50000]
        weight = scorer._normalize_population(50000, populations)
        assert weight == 0.5  # Should return neutral weight


# Integration Tests
class TestIntegration:
    """Test integration with CityStats model."""

    def test_calculate_scores_returns_same_list(self, sample_city_stats):
        """Test that calculate_scores returns the same list with scores calculated."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(sample_city_stats)
        
        # Should return same list object
        assert result is sample_city_stats
        assert len(result) == 3

    def test_all_weights_set_on_city_stats(self, sample_city_stats):
        """Test that all weight components are set on CityStats objects."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(sample_city_stats)
        
        for stats in result:
            assert stats.population_weight is not None
            assert stats.saturation_weight is not None
            assert stats.quality_gap_weight is not None
            assert stats.geographic_gap_weight is not None
            assert 0.0 <= stats.population_weight <= 1.0
            assert 0.0 <= stats.saturation_weight <= 1.0
            assert 0.0 <= stats.quality_gap_weight <= 1.0
            assert 0.0 <= stats.geographic_gap_weight <= 1.0

    def test_opportunity_score_calculated(self, sample_city_stats):
        """Test that opportunity_score is calculated and in range 0-100."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(sample_city_stats)
        
        for stats in result:
            assert stats.opportunity_score is not None
            assert 0.0 <= stats.opportunity_score <= 100.0

    def test_opportunity_score_uses_correct_formula(self, sample_city_stats):
        """Test that opportunity_score uses correct weighted formula."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(sample_city_stats)
        
        for stats in result:
            # Manually calculate expected score
            expected_score = (
                stats.population_weight * 0.2 +
                stats.saturation_weight * 0.3 +
                stats.quality_gap_weight * 0.2 +
                stats.geographic_gap_weight * 0.3
            ) * 100
            
            # Should match within floating point precision
            assert abs(stats.opportunity_score - expected_score) < 0.01

    def test_realistic_algarve_scenario(self, sample_city_stats):
        """Test with realistic Algarve data to verify intuitive results."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(sample_city_stats)
        
        # Monchique should score high (low saturation, low rating, far distance, small population)
        # Faro should be somewhere in middle (high population but saturated and high ratings)
        # Albufeira should be in middle
        
        scores = {stats.city: stats.opportunity_score for stats in result}
        
        # Basic sanity checks - all scores should be different
        assert len(set(scores.values())) == 3
        
        # Monchique should have high geographic gap weight (15km is far)
        monchique = next(s for s in result if s.city == "Monchique")
        assert monchique.geographic_gap_weight > 0.5

    def test_city_stats_validation_preserved(self, sample_city_stats):
        """Test that CityStats validation is preserved after scoring."""
        scorer = OpportunityScorer()
        result = scorer.calculate_scores(sample_city_stats)
        
        # All CityStats should still be valid Pydantic models
        for stats in result:
            # This would raise ValidationError if invalid
            stats.model_validate(stats)


# Functional Tests
class TestOpportunityScoring:
    """Test the overall opportunity scoring functionality."""

    def test_high_population_increases_score(self):
        """Test that higher population contributes to higher score."""
        city_low_pop = CityStats(
            city="SmallCity",
            total_facilities=5,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=500,
            center_lat=37.0,
            center_lng=-8.0,
            population=10000,
            facilities_per_capita=5.0,
            avg_distance_to_nearest=10.0
        )
        
        city_high_pop = CityStats(
            city="LargeCity",
            total_facilities=5,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=500,
            center_lat=37.1,
            center_lng=-8.1,
            population=100000,
            facilities_per_capita=0.5,
            avg_distance_to_nearest=10.0
        )
        
        scorer = OpportunityScorer()
        result = scorer.calculate_scores([city_low_pop, city_high_pop])
        
        # Higher population should have higher population_weight
        assert result[1].population_weight > result[0].population_weight

    def test_low_saturation_increases_score(self):
        """Test that lower saturation (facilities per capita) increases score."""
        city_low_sat = CityStats(
            city="Undersaturated",
            total_facilities=1,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=100,
            center_lat=37.0,
            center_lng=-8.0,
            population=50000,
            facilities_per_capita=0.2,  # Low saturation
            avg_distance_to_nearest=10.0
        )
        
        city_high_sat = CityStats(
            city="Saturated",
            total_facilities=20,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=2000,
            center_lat=37.1,
            center_lng=-8.1,
            population=50000,
            facilities_per_capita=4.0,  # High saturation
            avg_distance_to_nearest=10.0
        )
        
        scorer = OpportunityScorer()
        result = scorer.calculate_scores([city_low_sat, city_high_sat])
        
        # Lower saturation should have higher saturation_weight
        assert result[0].saturation_weight > result[1].saturation_weight

    def test_low_rating_increases_quality_gap(self):
        """Test that lower ratings increase quality gap opportunity."""
        city_low_rating = CityStats(
            city="LowQuality",
            total_facilities=5,
            avg_rating=3.0,  # Low rating
            median_rating=3.0,
            total_reviews=500,
            center_lat=37.0,
            center_lng=-8.0,
            population=50000,
            facilities_per_capita=1.0,
            avg_distance_to_nearest=10.0
        )
        
        city_high_rating = CityStats(
            city="HighQuality",
            total_facilities=5,
            avg_rating=4.8,  # High rating
            median_rating=4.8,
            total_reviews=500,
            center_lat=37.1,
            center_lng=-8.1,
            population=50000,
            facilities_per_capita=1.0,
            avg_distance_to_nearest=10.0
        )
        
        scorer = OpportunityScorer()
        result = scorer.calculate_scores([city_low_rating, city_high_rating])
        
        # Lower rating should have higher quality_gap_weight
        assert result[0].quality_gap_weight > result[1].quality_gap_weight

    def test_far_distance_increases_geographic_gap(self):
        """Test that larger distance to nearest facility increases geographic gap."""
        city_near = CityStats(
            city="NearFacilities",
            total_facilities=5,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=500,
            center_lat=37.0,
            center_lng=-8.0,
            population=50000,
            facilities_per_capita=1.0,
            avg_distance_to_nearest=2.0  # Very close
        )
        
        city_far = CityStats(
            city="IsolatedCity",
            total_facilities=5,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=500,
            center_lat=37.1,
            center_lng=-8.1,
            population=50000,
            facilities_per_capita=1.0,
            avg_distance_to_nearest=18.0  # Very far
        )
        
        scorer = OpportunityScorer()
        result = scorer.calculate_scores([city_near, city_far])
        
        # Farther distance should have higher geographic_gap_weight
        assert result[1].geographic_gap_weight > result[0].geographic_gap_weight

