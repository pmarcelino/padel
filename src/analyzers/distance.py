"""
Distance calculator for geographic analysis of padel facilities.

This module provides utilities for calculating distances between facilities
and estimating travel willingness based on city population size.
"""

from typing import List
from geopy.distance import geodesic
from src.models.facility import Facility


class DistanceCalculator:
    """
    Calculate geographic distances between facilities.
    
    This class provides static methods for:
    - Calculating minimum distance from a city to nearest facilities in other cities
    - Estimating travel willingness radius based on population size
    
    All methods are static and require no instance state.
    """
    
    @staticmethod
    def calculate_distance_to_nearest(
        city: str,
        all_facilities: List[Facility]
    ) -> float:
        """
        Calculate minimum distance to nearest facility for a city.
        
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

