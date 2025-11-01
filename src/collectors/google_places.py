"""
Google Places API collector for padel facilities.

This module provides functionality to search for and collect padel facility data
from the Google Places API. It handles pagination, rate limiting, caching, and
deduplication to ensure comprehensive and efficient data collection.
"""

import logging
import time
from typing import List, Optional, Set

import googlemaps
from googlemaps.exceptions import ApiError

from src.config import settings
from src.models.facility import Facility
from src.utils.cache import cache_response

# Setup module logger
logger = logging.getLogger(__name__)

# List of Algarve municipalities for city extraction
ALGARVE_CITIES = {
    "Albufeira",
    "Aljezur",
    "Castro Marim",
    "Faro",
    "Lagoa",
    "Lagos",
    "Loulé",
    "Monchique",
    "Olhão",
    "Portimão",
    "São Brás de Alportel",
    "Silves",
    "Tavira",
    "Vila do Bispo",
    "Vila Real de Santo António",
}


class GooglePlacesCollector:
    """
    Collects padel facility data from Google Places API.

    This collector searches for padel facilities using multiple query variations,
    handles pagination, implements rate limiting, and deduplicates results to
    ensure comprehensive coverage of the target region.

    Attributes:
        api_key: Google Places API key
        client: Google Maps API client
        cache_enabled: Whether to enable response caching
        rate_limit_delay: Delay between API requests in seconds
    """

    def __init__(self, api_key: str, cache_enabled: Optional[bool] = None) -> None:
        """
        Initialize the collector.

        Args:
            api_key: Google Places API key
            cache_enabled: Whether to enable response caching
                          (defaults to settings.cache_enabled)
        """
        self.api_key = api_key
        self.client = googlemaps.Client(key=api_key)
        self.cache_enabled = (
            cache_enabled if cache_enabled is not None else settings.cache_enabled
        )
        self.rate_limit_delay = settings.rate_limit_delay

    def search_padel_facilities(
        self, region: str = "Algarve, Portugal"
    ) -> List[Facility]:
        """
        Search for padel facilities in a region.

        Uses multiple query variations to maximize facility discovery and handles
        pagination to collect all available results. Facilities are deduplicated
        by place_id to avoid duplicates across different queries.

        Args:
            region: Geographic region to search

        Returns:
            List of Facility objects with complete data
        """
        # Query variations to maximize coverage
        query_variations = [
            f"padel {region}",
            f"padel court {region}",
            f"padel club {region}",
            f"centro de padel {region}",
        ]

        # Track seen place_ids for deduplication
        seen_place_ids: Set[str] = set()
        all_facilities: List[Facility] = []

        # Search with each query variation
        for query in query_variations:
            logger.info(f"Searching with query: {query}")

            try:
                # Get place IDs from text search
                place_ids = self._search_text(query)

                # Get details for each unique place
                for place_id in place_ids:
                    if place_id in seen_place_ids:
                        logger.debug(f"Skipping duplicate place_id: {place_id}")
                        continue

                    seen_place_ids.add(place_id)

                    try:
                        # Get place details and convert to Facility
                        facility = self._get_place_details(place_id)
                        if facility:
                            all_facilities.append(facility)
                            logger.debug(
                                f"Added facility: {facility.name} ({facility.city})"
                            )
                    except Exception as e:
                        # Log error but continue with other facilities
                        logger.warning(
                            f"Error getting details for place_id {place_id}: {e}"
                        )
                        continue

            except Exception as e:
                # Log error but continue with remaining queries
                logger.error(f"Error executing query '{query}': {e}")
                continue

        logger.info(
            f"Collected {len(all_facilities)} unique facilities from {region}"
        )
        return all_facilities

    def _search_text(self, query: str) -> List[str]:
        """
        Execute a text search and return list of place_ids.

        Handles pagination to collect all results with proper delays between pages.

        Args:
            query: Search query string

        Returns:
            List of unique place_ids found
        """
        place_ids: List[str] = []
        next_page_token: Optional[str] = None

        while True:
            try:
                # Apply rate limit delay before API call
                time.sleep(self.rate_limit_delay)

                # Call text search API (with caching if enabled)
                if next_page_token:
                    # Pagination request requires page_token
                    result = self._cached_text_search(query, page_token=next_page_token)
                else:
                    result = self._cached_text_search(query)

                # Extract place_ids from results
                for place in result.get("results", []):
                    place_id = place.get("place_id")
                    if place_id:
                        place_ids.append(place_id)

                # Check for next page
                next_page_token = result.get("next_page_token")
                if not next_page_token:
                    break

                # Required delay before next page request
                logger.debug("Waiting 2 seconds before fetching next page...")
                time.sleep(2)

            except ApiError as e:
                logger.error(f"Google API error during text search: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error during text search: {e}")
                break

        return place_ids

    @cache_response(ttl_days=30)
    def _cached_text_search(
        self, query: str, page_token: Optional[str] = None
    ) -> dict:
        """
        Execute cached text search.

        This method is decorated with @cache_response to cache results for 30 days.

        Args:
            query: Search query string
            page_token: Optional pagination token

        Returns:
            Raw API response dictionary
        """
        if page_token:
            return self.client.places_nearby(
                location=None, query=query, page_token=page_token
            )
        else:
            return self.client.places_nearby(location=None, query=query)

    def _get_place_details(self, place_id: str) -> Optional[Facility]:
        """
        Get detailed information for a place and convert to Facility object.

        Args:
            place_id: Google Places place_id

        Returns:
            Facility object if data is valid, None otherwise
        """
        try:
            # Apply rate limit delay before API call
            time.sleep(self.rate_limit_delay)

            # Get place details (with caching if enabled)
            result = self._cached_place_details(place_id)

            if result.get("status") != "OK":
                logger.warning(
                    f"Place details request failed for {place_id}: {result.get('status')}"
                )
                return None

            place = result.get("result", {})

            # Extract required fields
            name = place.get("name")
            address = place.get("formatted_address", "")
            geometry = place.get("geometry", {})
            location = geometry.get("location", {})
            latitude = location.get("lat")
            longitude = location.get("lng")

            # Validate required fields
            if not all([place_id, name, address, latitude, longitude]):
                logger.warning(
                    f"Missing required fields for place_id {place_id}, skipping"
                )
                return None

            # Extract city from address
            city = self._extract_city(address)
            if not city:
                logger.warning(
                    f"Could not extract city from address: {address}, skipping"
                )
                return None

            # Extract optional fields
            rating = place.get("rating")
            review_count = place.get("user_ratings_total", 0)
            google_url = place.get("url")
            phone = place.get("formatted_phone_number")
            website = place.get("website")

            # Determine facility type from Google types
            types = place.get("types", [])
            facility_type = self._determine_facility_type(types)

            # Create Facility object
            facility = Facility(
                place_id=place_id,
                name=name,
                address=address,
                city=city,
                latitude=latitude,
                longitude=longitude,
                rating=rating,
                review_count=review_count,
                google_url=google_url,
                phone=phone,
                website=website,
                facility_type=facility_type,
            )

            return facility

        except Exception as e:
            logger.error(f"Error creating Facility from place_id {place_id}: {e}")
            return None

    @cache_response(ttl_days=7)
    def _cached_place_details(self, place_id: str) -> dict:
        """
        Get cached place details.

        This method is decorated with @cache_response to cache results for 7 days.

        Args:
            place_id: Google Places place_id

        Returns:
            Raw API response dictionary
        """
        return self.client.place(
            place_id=place_id,
            fields=[
                "place_id",
                "name",
                "formatted_address",
                "geometry",
                "rating",
                "user_ratings_total",
                "url",
                "formatted_phone_number",
                "website",
                "types",
            ],
        )

    def _extract_city(self, address: str) -> Optional[str]:
        """
        Extract city name from address.

        Looks for Algarve municipality names in the address string.

        Args:
            address: Full formatted address

        Returns:
            City name if found in ALGARVE_CITIES, None otherwise
        """
        # Normalize address for comparison
        address_normalized = address.strip()

        # Check each Algarve city
        for city in ALGARVE_CITIES:
            # Look for city name in address (case-insensitive)
            if city.lower() in address_normalized.lower():
                return city

        return None

    def _determine_facility_type(self, types: List[str]) -> str:
        """
        Determine facility type from Google Place types.

        Maps Google types to internal facility type categories.

        Args:
            types: List of Google Place type strings

        Returns:
            Facility type: 'sports_center', 'club', or 'other'
        """
        # Convert to lowercase for comparison
        types_lower = [t.lower() for t in types]

        # Check for sports center indicators
        if any(t in types_lower for t in ["gym", "health"]):
            return "sports_center"

        # Check for club indicators
        if "point_of_interest" in types_lower:
            return "club"

        # Default to other
        return "other"

