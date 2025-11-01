"""
City aggregator for facility data.

This module provides the CityAggregator class which aggregates facility-level
data into city-level statistics including ratings, review counts, geographic
centers, and facilities per capita metrics.
"""

from typing import Dict, List

import pandas as pd

from src.models.city import CityStats
from src.models.facility import Facility


class CityAggregator:
    """
    Aggregate facility data by city to compute city-level statistics.
    
    This class processes a list of facilities and groups them by city,
    calculating key metrics such as:
    - Total facility counts
    - Average and median ratings
    - Total review counts
    - Geographic centers (mean lat/lng)
    - Population data and facilities per capita
    
    Population data is sourced from the 2021 Census Data from INE Portugal
    (Instituto Nacional de Estatística) for the 15 Algarve municipalities.
    """
    
    # Algarve city populations (2021 Census Data from INE Portugal)
    CITY_POPULATIONS: Dict[str, int] = {
        "Albufeira": 42388,
        "Aljezur": 5347,
        "Castro Marim": 6747,
        "Faro": 64560,
        "Lagoa": 23676,
        "Lagos": 31049,
        "Loulé": 72162,
        "Monchique": 5958,
        "Olhão": 45396,
        "Portimão": 59896,
        "São Brás De Alportel": 11381,
        "Silves": 37126,
        "Tavira": 26167,
        "Vila Do Bispo": 5717,
        "Vila Real De Santo António": 19156,
    }
    
    def aggregate(self, facilities: List[Facility]) -> List[CityStats]:
        """
        Aggregate facility data by city.
        
        Groups facilities by city and calculates statistics including:
        - Total facilities
        - Average rating (ignoring null values)
        - Median rating (ignoring null values)
        - Total reviews
        - Geographic center (mean latitude and longitude)
        - Population (from CITY_POPULATIONS lookup)
        - Facilities per capita (per 10,000 residents)
        
        Args:
            facilities: List of Facility objects to aggregate
            
        Returns:
            List of CityStats objects, one per unique city
            
        Example:
            >>> aggregator = CityAggregator()
            >>> facilities = [
            ...     Facility(place_id="1", name="Club A", city="Faro", ...),
            ...     Facility(place_id="2", name="Club B", city="Faro", ...),
            ... ]
            >>> stats = aggregator.aggregate(facilities)
            >>> len(stats)
            1
            >>> stats[0].city
            'Faro'
        """
        # Handle empty input
        if not facilities:
            return []
        
        # Convert facilities to DataFrame for efficient aggregation
        facility_dicts = [f.model_dump() for f in facilities]
        df = pd.DataFrame(facility_dicts)
        
        # Group by city and aggregate
        city_stats_list = []
        
        for city_name, city_group in df.groupby('city'):
            # Calculate rating statistics
            ratings = city_group['rating'].dropna()
            
            if len(ratings) > 0:
                avg_rating = float(ratings.mean())
                median_rating = float(ratings.median())
            else:
                avg_rating = None
                median_rating = None
            
            # Calculate counts
            total_facilities = len(city_group)
            total_reviews = int(city_group['review_count'].sum())
            
            # Calculate geographic center
            center_lat = float(city_group['latitude'].mean())
            center_lng = float(city_group['longitude'].mean())
            
            # Lookup population
            population = self.CITY_POPULATIONS.get(city_name, None)
            
            # Calculate facilities per capita (per 10,000 residents)
            if population is not None:
                facilities_per_capita = (total_facilities / population) * 10000
            else:
                facilities_per_capita = None
            
            # Create CityStats object
            city_stats = CityStats(
                city=city_name,
                total_facilities=total_facilities,
                avg_rating=avg_rating,
                median_rating=median_rating,
                total_reviews=total_reviews,
                center_lat=center_lat,
                center_lng=center_lng,
                population=population,
                facilities_per_capita=facilities_per_capita,
            )
            
            city_stats_list.append(city_stats)
        
        return city_stats_list

