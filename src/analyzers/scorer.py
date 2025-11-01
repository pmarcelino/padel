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
    - Geographic Gap: 30% (larger distance to competitors = geographic opportunity)
    """
    
    # Formula weights (must sum to 1.0)
    POPULATION_WEIGHT_FACTOR = 0.2
    SATURATION_WEIGHT_FACTOR = 0.3
    QUALITY_GAP_WEIGHT_FACTOR = 0.2
    GEOGRAPHIC_GAP_WEIGHT_FACTOR = 0.3
    
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
        Normalize geographic gap (larger distance = higher opportunity).
        
        Uses simple ratio normalization where larger distances to the nearest
        facility receive higher weights. Distance is capped at 20km maximum.
        Cities more than 20km from competitors receive the maximum geographic
        gap weight.
        
        Args:
            value: Average distance to nearest facility (km)
            
        Returns:
            Normalized value between 0-1 (larger distance = higher score, capped at 20km)
        """
        if value is None:
            return 0.5
        
        # Cap at 20km and normalize to 0-1 range
        capped_value = min(value, 20.0)
        return capped_value / 20.0
    
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

