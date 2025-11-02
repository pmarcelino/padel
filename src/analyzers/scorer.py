"""
OpportunityScorer for calculating city opportunity scores.

This module provides the OpportunityScorer class which calculates weighted
opportunity scores for cities based on population, saturation, quality gaps,
and geographic gaps. Scores are normalized to 0-100 range to identify the most
promising locations for new padel facilities.
"""

from typing import List, Optional

from src.models.city import CityStats


class OpportunityScorer:
    """
    Calculate opportunity scores for cities based on multiple weighted factors.
    
    The scorer normalizes various city metrics (population, saturation, quality gaps,
    and geographic gaps) into a unified 0-100 score that helps identify the most
    promising locations for new padel facilities.
    
    Formula weights (must sum to 1.0):
    - Population: 20% (higher population = more potential customers)
    - Saturation: 30% (lower facilities per capita = less competition)
    - Quality Gap: 20% (lower ratings = room for quality differentiation)
    - Geographic Gap: 30% (step-based: 0-5km=0.25, 5-10km=0.50, 10-20km=0.75, >20km=1.0)
    """
    
    # Formula weights (must sum to 1.0)
    POPULATION_WEIGHT_FACTOR = 0.2
    SATURATION_WEIGHT_FACTOR = 0.3
    QUALITY_GAP_WEIGHT_FACTOR = 0.2
    GEOGRAPHIC_GAP_WEIGHT_FACTOR = 0.3
    
    # Geographic gap distance buckets (km) - (min_km, max_km, weight)
    GEOGRAPHIC_GAP_BUCKETS = {
        "close": (0, 5, 0.25),
        "medium": (5, 10, 0.50),
        "far": (10, 20, 0.75),
        "very_far": (20, float('inf'), 1.0),
    }
    
    def __init__(self):
        """
        Initialize scorer and validate formula weights.
        
        Raises:
            ValueError: If formula weights don't sum to 1.0
        """
        total = (
            self.POPULATION_WEIGHT_FACTOR +
            self.SATURATION_WEIGHT_FACTOR +
            self.QUALITY_GAP_WEIGHT_FACTOR +
            self.GEOGRAPHIC_GAP_WEIGHT_FACTOR
        )
        if not (0.9999 <= total <= 1.0001):  # Allow tiny floating point errors
            raise ValueError(f"Formula weights must sum to 1.0, got {total}")
    
    def calculate_scores(self, city_stats: List[CityStats]) -> List[CityStats]:
        """
        Calculate opportunity scores using normalized weights.
        
        This method normalizes all four weight components and calculates the final
        opportunity score for each city. The input list is modified in place.
        
        Formula:
        Opportunity Score = (Population Weight × 0.2) 
                          + (Low Saturation Weight × 0.3)
                          + (Quality Gap Weight × 0.2)
                          + (Geographic Gap Weight × 0.3)
        
        Args:
            city_stats: List of CityStats with metrics populated
            
        Returns:
            Same list with scores calculated (modified in place)
        """
        if not city_stats:
            return city_stats
        
        # Extract all values for normalization
        populations = [stats.population for stats in city_stats]
        saturations = [stats.facilities_per_capita for stats in city_stats]
        ratings = [stats.avg_rating for stats in city_stats]
        
        # Calculate weights for each city
        for stats in city_stats:
            # Normalize each component
            stats.population_weight = self._normalize_population(
                stats.population, populations
            )
            stats.saturation_weight = self._normalize_saturation(
                stats.facilities_per_capita, saturations
            )
            stats.quality_gap_weight = self._normalize_quality_gap(
                stats.avg_rating, ratings
            )
            stats.geographic_gap_weight = self._normalize_geographic_gap(
                stats.avg_distance_to_nearest
            )
            
            # Calculate final opportunity score using CityStats method
            stats.calculate_opportunity_score()
        
        return city_stats
    
    def _normalize_population(self, value: Optional[float], all_values: List[Optional[float]]) -> float:
        """
        Normalize population (higher is better).
        
        Uses min-max normalization where higher populations receive higher weights.
        This reflects that larger populations represent more potential customers.
        
        Args:
            value: Population for a specific city
            all_values: All population values for normalization
            
        Returns:
            Normalized value between 0-1 (higher population = higher score)
        """
        return self._normalize(value, all_values, invert=False)
    
    def _normalize_saturation(self, value: Optional[float], all_values: List[Optional[float]]) -> float:
        """
        Normalize saturation (lower is better - inverted).
        
        Uses inverted min-max normalization where lower facilities per capita
        receives higher weights. This reflects that less saturated markets have
        less competition.
        
        Args:
            value: Facilities per capita for a specific city
            all_values: All saturation values for normalization
            
        Returns:
            Normalized value between 0-1 (lower saturation = higher score)
        """
        return self._normalize(value, all_values, invert=True)
    
    def _normalize_quality_gap(self, value: Optional[float], all_values: List[Optional[float]]) -> float:
        """
        Normalize quality gap (lower rating = higher opportunity - inverted).
        
        Uses inverted min-max normalization where lower average ratings receive
        higher weights. This reflects that markets with lower-quality facilities
        present opportunities for quality differentiation.
        
        Args:
            value: Average rating for a specific city
            all_values: All rating values for normalization
            
        Returns:
            Normalized value between 0-1 (lower rating = higher opportunity)
        """
        return self._normalize(value, all_values, invert=True)
    
    def _normalize_geographic_gap(self, value: Optional[float]) -> float:
        """
        Normalize geographic gap using step-based buckets.
        
        Distance buckets:
        - 0-5 km: 0.25 (close - low geographic opportunity)
        - 5-10 km: 0.50 (medium distance - medium opportunity)
        - 10-20 km: 0.75 (far - high opportunity)
        - >20 km: 1.0 (very far - very high opportunity)
        
        Args:
            value: Average distance to nearest facility (km)
            
        Returns:
            Normalized value: 0.25, 0.50, 0.75, or 1.0
        """
        if value is None or value < 0:
            return 0.5  # Default for invalid values
        
        if value < 5:
            return 0.25
        elif value < 10:
            return 0.50
        elif value < 20:
            return 0.75
        else:
            return 1.0
    
    def _normalize(self, value: Optional[float], all_values: List[Optional[float]], invert: bool = False) -> float:
        """
        Perform min-max normalization with edge case handling.
        
        This is a DRY helper method that implements min-max normalization with
        proper handling of None values, single values, and zero variance.
        
        Formula: (value - min) / (max - min + epsilon)
        
        Edge cases:
        - None value: returns 0.5 (neutral)
        - Empty list: returns 0.5 (neutral)
        - Single value: returns 0.5 (neutral)
        - Zero variance: returns 0.5 (neutral)
        
        Args:
            value: The value to normalize
            all_values: All values for computing min/max
            invert: If True, returns 1 - normalized_value
            
        Returns:
            Normalized value between 0-1, or 0.5 for edge cases
        """
        if value is None or not all_values:
            return 0.5
        
        # Filter out None values
        valid_values = [v for v in all_values if v is not None]
        
        if not valid_values or len(valid_values) == 1:
            return 0.5
        
        min_val = min(valid_values)
        max_val = max(valid_values)
        
        # Check for zero variance
        if max_val - min_val < 1e-6:
            return 0.5
        
        # Min-max normalization with epsilon for numerical stability
        normalized = (value - min_val) / (max_val - min_val + 1e-6)
        
        return 1.0 - normalized if invert else normalized

