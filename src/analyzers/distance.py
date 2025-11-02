"""
Distance calculator for geographic analysis of padel facilities.

This module provides utilities for calculating distances between facilities
and estimating travel willingness based on city population size.
"""

from typing import List
from geopy.distance import geodesic
from src.models.facility import Facility
from src.models.city import CityStats


class DistanceCalculator:
    """
    Calculate geographic distances between facilities.
    
    This class provides both static methods (legacy API) and instance methods
    for calculating distances. The instance methods support zero-facility cities
    by using city center coordinates when no facilities exist in a city.
    
    Methods:
    - calculate_distances(): New API that handles zero-facility cities
    - calculate_distance_to_nearest(): Legacy static method (backwards compatible)
    - calculate_travel_willingness_radius(): Static method for travel radius estimation
    """
    
    def calculate_distances(
        self,
        city_stats: List[CityStats],
        all_facilities: List[Facility]
    ) -> List[CityStats]:
        """
        Calculate avg_distance_to_nearest for each city.
        
        This method handles both normal cities (with facilities) and zero-facility
        cities. For zero-facility cities, it calculates distance from the city center
        coordinates to the nearest facility anywhere in the region.
        
        For cities WITH facilities:
            - Calculate distance from each facility to its nearest neighbor in other cities
            - Uses existing calculate_distance_to_nearest() logic
        
        For cities WITHOUT facilities:
            - Calculate distance from city center to nearest facility anywhere
            - Uses city_stats.center_lat and city_stats.center_lng as the reference point
            - This represents: "How far do residents need to travel to play?"
        
        Args:
            city_stats: List of CityStats objects to update with distance calculations
            all_facilities: Complete list of facilities across all cities
            
        Returns:
            Same list of CityStats with avg_distance_to_nearest populated for each city
            
        Example:
            >>> calculator = DistanceCalculator()
            >>> monchique_stats = CityStats(city="Monchique", total_facilities=0, 
            ...                             center_lat=37.3167, center_lng=-8.5556, ...)
            >>> faro_facility = Facility(city="Faro", latitude=37.0194, longitude=-7.9322, ...)
            >>> result = calculator.calculate_distances([monchique_stats], [faro_facility])
            >>> result[0].avg_distance_to_nearest
            71.23
        """
        for stats in city_stats:
            distance = self._calculate_distance_for_city(stats, all_facilities)
            stats.avg_distance_to_nearest = distance
        
        return city_stats
    
    def _calculate_distance_for_city(
        self,
        city_stats: CityStats,
        all_facilities: List[Facility]
    ) -> float:
        """
        Calculate distance for a single city (handles zero-facility cities).
        
        This method detects whether a city has facilities and uses the appropriate
        calculation strategy:
        - If city has facilities: delegates to calculate_distance_to_nearest()
        - If city has zero facilities: calculates from city center to nearest facility
        
        Args:
            city_stats: CityStats object containing city information and coordinates
            all_facilities: Complete list of facilities across all cities
            
        Returns:
            Distance in kilometers, rounded to 2 decimal places. Returns 0.0 if:
            - No facilities exist anywhere (can't calculate)
            - City has facilities but no neighbors (edge case)
            
        Example:
            >>> calculator = DistanceCalculator()
            >>> monchique_stats = CityStats(city="Monchique", total_facilities=0,
            ...                             center_lat=37.3167, center_lng=-8.5556, ...)
            >>> facilities = [Facility(city="Lagos", latitude=37.1028, longitude=-8.6732, ...)]
            >>> calculator._calculate_distance_for_city(monchique_stats, facilities)
            27.45
        """
        # Check if city has facilities
        city_facilities = [f for f in all_facilities if f.city == city_stats.city]
        
        if not city_facilities:
            # Zero-facility city: calculate from city center to nearest facility
            if not all_facilities:
                return 0.0  # No facilities anywhere - can't calculate
            
            # Use city center coordinates from CityStats
            city_center = (city_stats.center_lat, city_stats.center_lng)
            
            # Find nearest facility across ALL cities
            distances = [
                geodesic(city_center, (f.latitude, f.longitude)).kilometers
                for f in all_facilities
            ]
            
            return round(min(distances), 2)
        else:
            # City has facilities: use existing static method (DRY principle)
            return self.calculate_distance_to_nearest(city_stats.city, all_facilities)
    
    @staticmethod
    def calculate_distance_to_nearest(
        city: str,
        all_facilities: List[Facility]
    ) -> float:
        """
        Calculate minimum distance to nearest facility for a city.
        
        **Legacy API**: For new code, use calculate_distances() instance method which
        properly handles zero-facility cities. This static method only works for cities
        that have at least one facility.
        
        Uses the center point of the city (average of all facility coordinates)
        and finds the closest facility in other cities using geodesic distance.
        
        Args:
            city: Name of the city to analyze
            all_facilities: Complete list of facilities across all cities
            
        Returns:
            Minimum distance in kilometers to nearest facility in other cities,
            rounded to 2 decimal places. Returns 0.0 if:
            - Facility list is empty
            - City has no facilities
            - No facilities exist in other cities
            
        Example:
            >>> facilities = [
            ...     Facility(city="Albufeira", latitude=37.0885, longitude=-8.2475, ...),
            ...     Facility(city="Faro", latitude=37.0194, longitude=-7.9322, ...)
            ... ]
            >>> DistanceCalculator.calculate_distance_to_nearest("Albufeira", facilities)
            26.01
        """
        # Edge case: empty facility list
        if not all_facilities:
            return 0.0
        
        # Filter facilities in the target city
        city_facilities = [f for f in all_facilities if f.city == city]
        
        # Edge case: no facilities in the target city
        if not city_facilities:
            return 0.0
        
        # Calculate city center (average latitude and longitude)
        center_lat = sum(f.latitude for f in city_facilities) / len(city_facilities)
        center_lng = sum(f.longitude for f in city_facilities) / len(city_facilities)
        city_center = (center_lat, center_lng)
        
        # Filter facilities NOT in the target city
        external_facilities = [f for f in all_facilities if f.city != city]
        
        # Edge case: no facilities in other cities
        if not external_facilities:
            return 0.0
        
        # Calculate distances from city center to all external facilities
        distances = [
            geodesic(city_center, (f.latitude, f.longitude)).kilometers
            for f in external_facilities
        ]
        
        # Return minimum distance, rounded to 2 decimal places
        return round(min(distances), 2)
    
    @staticmethod
    def calculate_travel_willingness_radius(city_population: int) -> float:
        """
        Estimate how far people are willing to travel based on city size.
        
        Assumptions:
        - Larger cities (>50,000): people travel less (more local options expected)
        - Mid-size cities (20,000-50,000): moderate travel willingness
        - Smaller cities (<20,000): people travel more (fewer local options)
        
        Args:
            city_population: Population of the city
            
        Returns:
            Estimated travel radius in kilometers:
            - 5.0 km for urban areas (>50,000 population)
            - 10.0 km for mid-size towns (20,000-50,000 population)
            - 15.0 km for small towns (<20,000 population)
            
        Example:
            >>> DistanceCalculator.calculate_travel_willingness_radius(60000)
            5.0
            >>> DistanceCalculator.calculate_travel_willingness_radius(30000)
            10.0
            >>> DistanceCalculator.calculate_travel_willingness_radius(10000)
            15.0
        """
        if city_population > 50000:
            return 5.0
        elif city_population >= 20000:
            return 10.0
        else:
            return 15.0

