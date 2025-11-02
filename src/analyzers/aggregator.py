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
    
    # Algarve city center coordinates (geographic centers of municipalities)
    CITY_CENTERS: Dict[str, Dict[str, float]] = {
        "Albufeira": {"lat": 37.0885, "lng": -8.2475},
        "Aljezur": {"lat": 37.3183, "lng": -8.8042},
        "Castro Marim": {"lat": 37.2169, "lng": -7.4472},
        "Faro": {"lat": 37.0194, "lng": -7.9322},
        "Lagoa": {"lat": 37.1333, "lng": -8.4500},
        "Lagos": {"lat": 37.1028, "lng": -8.6732},
        "Loulé": {"lat": 37.1376, "lng": -8.0222},
        "Monchique": {"lat": 37.3167, "lng": -8.5556},
        "Olhão": {"lat": 37.0267, "lng": -7.8411},
        "Portimão": {"lat": 37.1391, "lng": -8.5372},
        "São Brás De Alportel": {"lat": 37.1525, "lng": -7.8836},
        "Silves": {"lat": 37.1875, "lng": -8.4383},
        "Tavira": {"lat": 37.1267, "lng": -7.6486},
        "Vila Do Bispo": {"lat": 37.0833, "lng": -8.9122},
        "Vila Real De Santo António": {"lat": 37.1961, "lng": -7.4167},
    }
    
    def aggregate(self, facilities: List[Facility]) -> List[CityStats]:
        """
        Aggregate facility data by city.
        
        Returns statistics for all 15 Algarve cities, regardless of whether they have
        facilities in the input. Cities with zero facilities receive default zero/null values.
        
        Groups facilities by city and calculates statistics including:
        - Total facilities
        - Average rating (ignoring null values)
        - Median rating (ignoring null values)
        - Total reviews
        - Geographic center (from CITY_CENTERS for zero-facility cities, mean lat/lng for others)
        - Population (from CITY_POPULATIONS lookup)
        - Facilities per capita (per 10,000 residents)
        
        Args:
            facilities: List of Facility objects to aggregate
            
        Returns:
            List of CityStats objects - guaranteed to include all 15 Algarve cities,
            plus any additional cities found in facilities that are not in CITY_POPULATIONS
            
        Example:
            >>> aggregator = CityAggregator()
            >>> facilities = [
            ...     Facility(place_id="1", name="Club A", city="Faro", ...),
            ... ]
            >>> stats = aggregator.aggregate(facilities)
            >>> len(stats)  # All 15 Algarve cities
            15
            >>> faro_stats = [s for s in stats if s.city == "Faro"][0]
            >>> faro_stats.total_facilities
            1
            >>> monchique_stats = [s for s in stats if s.city == "Monchique"][0]
            >>> monchique_stats.total_facilities
            0
        """
        # Step 1: Aggregate facilities by city (existing logic)
        facility_stats = {}
        
        if facilities:
            # Convert facilities to DataFrame for efficient aggregation
            facility_dicts = [f.model_dump() for f in facilities]
            df = pd.DataFrame(facility_dicts)
            
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
                
                # Store stats for this city
                facility_stats[city_name] = {
                    'city': city_name,
                    'total_facilities': total_facilities,
                    'avg_rating': avg_rating,
                    'median_rating': median_rating,
                    'total_reviews': total_reviews,
                    'center_lat': center_lat,
                    'center_lng': center_lng,
                    'population': population,
                    'facilities_per_capita': facilities_per_capita,
                }
        
        # Step 2: Create CityStats for ALL cities in CITY_POPULATIONS
        all_city_stats = []
        
        for city_name, population in self.CITY_POPULATIONS.items():
            if city_name in facility_stats:
                # City has facilities - use aggregated stats
                stats = CityStats(**facility_stats[city_name])
            else:
                # Zero-facility city - use defaults with city center coordinates
                center = self.CITY_CENTERS[city_name]
                stats = CityStats(
                    city=city_name,
                    total_facilities=0,
                    avg_rating=None,
                    median_rating=None,
                    total_reviews=0,
                    center_lat=center['lat'],
                    center_lng=center['lng'],
                    population=population,
                    facilities_per_capita=0.0,
                )
            
            all_city_stats.append(stats)
        
        # Step 3: Handle cities not in CITY_POPULATIONS (unknown cities with facilities)
        for city_name in facility_stats:
            if city_name not in self.CITY_POPULATIONS:
                stats = CityStats(**facility_stats[city_name])
                all_city_stats.append(stats)
        
        return all_city_stats

