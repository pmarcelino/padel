"""
Example usage of Google Places Collector.

This script demonstrates how to use the GooglePlacesCollector to search for
padel facilities in the Algarve region.
"""

from src.collectors import GooglePlacesCollector
from src.config import settings


def main():
    """Collect padel facilities from Google Places API."""
    
    # Initialize collector with API key from settings
    collector = GooglePlacesCollector(api_key=settings.google_api_key)
    
    print("Searching for padel facilities in Algarve...")
    print(f"Cache enabled: {collector.cache_enabled}")
    print(f"Rate limit delay: {collector.rate_limit_delay}s")
    print()
    
    # Search for facilities
    facilities = collector.search_padel_facilities(region="Algarve, Portugal")
    
    # Display results
    print(f"Found {len(facilities)} unique facilities")
    print()
    
    # Group by city
    cities = {}
    for facility in facilities:
        if facility.city not in cities:
            cities[facility.city] = []
        cities[facility.city].append(facility)
    
    # Display summary by city
    for city in sorted(cities.keys()):
        city_facilities = cities[city]
        avg_rating = sum(f.rating for f in city_facilities if f.rating) / len(city_facilities)
        print(f"{city}: {len(city_facilities)} facilities (avg rating: {avg_rating:.1f})")
    
    print()
    print("Sample facility details:")
    if facilities:
        facility = facilities[0]
        print(f"  Name: {facility.name}")
        print(f"  City: {facility.city}")
        print(f"  Address: {facility.address}")
        print(f"  Location: {facility.latitude}, {facility.longitude}")
        print(f"  Rating: {facility.rating} ({facility.review_count} reviews)")
        print(f"  Type: {facility.facility_type}")
        if facility.phone:
            print(f"  Phone: {facility.phone}")
        if facility.website:
            print(f"  Website: {facility.website}")


if __name__ == "__main__":
    main()

