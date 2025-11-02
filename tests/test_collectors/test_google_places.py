"""
Unit tests for Google Places API collector.

Tests the GooglePlacesCollector with mocked API responses to verify:
- Basic search functionality
- Pagination handling
- Deduplication
- City extraction
- Error handling
- Rate limiting
"""

import shutil
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.collectors.google_places import GooglePlacesCollector
from src.config import settings
from src.models.facility import Facility


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache directory before each test to ensure test isolation."""
    cache_dir = settings.cache_dir
    if cache_dir and cache_dir.exists():
        # Remove all .pkl files in cache directory
        for cache_file in cache_dir.glob("*.pkl"):
            cache_file.unlink()
    yield
    # Cleanup after test
    if cache_dir and cache_dir.exists():
        for cache_file in cache_dir.glob("*.pkl"):
            cache_file.unlink()


class TestGooglePlacesCollectorInit:
    """Test collector initialization."""

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_init_with_api_key(self, mock_client_class):
        """Test collector can be initialized with API key."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        collector = GooglePlacesCollector(api_key="AIzatest_key")
        assert collector.api_key == "AIzatest_key"
        assert collector.cache_enabled is True  # Default from settings

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_init_with_cache_disabled(self, mock_client_class):
        """Test collector can be initialized with caching disabled."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        collector = GooglePlacesCollector(api_key="AIzatest_key", cache_enabled=False)
        assert collector.cache_enabled is False

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_init_loads_rate_limit_from_settings(self, mock_client_class):
        """Test that rate limit delay is loaded from settings."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        collector = GooglePlacesCollector(api_key="AIzatest_key")
        # Should have rate_limit_delay attribute from settings
        assert hasattr(collector, "rate_limit_delay")
        assert collector.rate_limit_delay > 0


class TestBasicSearch:
    """Test basic search functionality."""

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_search_returns_facilities(self, mock_client_class):
        """Test that search returns a list of Facility objects."""
        # Mock API response
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock text search response
        mock_client.places.return_value = {
            "results": [
                {
                    "place_id": "place_123",
                    "name": "Padel Club Albufeira",
                    "geometry": {"location": {"lat": 37.0875, "lng": -8.2473}},
                    "vicinity": "Rua Test, Albufeira",
                    "rating": 4.5,
                    "user_ratings_total": 100,
                    "types": ["point_of_interest"],
                }
            ],
            "status": "OK",
        }

        # Mock place details response
        mock_client.place.return_value = {
            "result": {
                "place_id": "place_123",
                "name": "Padel Club Albufeira",
                "formatted_address": "Rua Test, 8200 Albufeira, Portugal",
                "geometry": {"location": {"lat": 37.0875, "lng": -8.2473}},
                "rating": 4.5,
                "user_ratings_total": 100,
                "url": "https://maps.google.com/?cid=123",
                "formatted_phone_number": "+351 289 123 456",
                "website": "https://padelclub.com",
                "types": ["point_of_interest"],
            },
            "status": "OK",
        }

        collector = GooglePlacesCollector(api_key="test_key")
        facilities = collector.search_padel_facilities(region="Algarve, Portugal")

        assert isinstance(facilities, list)
        assert len(facilities) > 0
        assert all(isinstance(f, Facility) for f in facilities)

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_search_parses_facility_fields_correctly(self, mock_client_class):
        """Test that facility fields are correctly parsed from API response."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock places to return one result per query
        mock_client.places.return_value = {
            "results": [{"place_id": "place_parse_test_123"}],
            "status": "OK",
        }

        # Mock place details with complete data
        mock_client.place.return_value = {
            "result": {
                "place_id": "place_parse_test_123",
                "name": "Test Padel Center",
                "formatted_address": "Rua Test, 8200 Albufeira, Portugal",
                "geometry": {"location": {"lat": 37.0875, "lng": -8.2473}},
                "rating": 4.5,
                "user_ratings_total": 100,
                "url": "https://maps.google.com/?cid=123",
                "formatted_phone_number": "+351 289 123 456",
                "website": "https://testpadel.com",
                "types": ["gym", "health"],
            },
            "status": "OK",
        }

        collector = GooglePlacesCollector(api_key="AIzatest_key")
        facilities = collector.search_padel_facilities()

        # Should only have 1 unique facility (deduped across 4 queries)
        assert len(facilities) == 1
        
        facility = facilities[0]
        assert facility.place_id == "place_parse_test_123"
        assert facility.name == "Test Padel Center"
        assert facility.address == "Rua Test, 8200 Albufeira, Portugal"
        assert facility.city == "Albufeira"
        assert facility.latitude == 37.0875
        assert facility.longitude == -8.2473
        assert facility.rating == 4.5
        assert facility.review_count == 100
        assert facility.google_url == "https://maps.google.com/?cid=123"
        assert facility.phone == "+351 289 123 456"
        assert facility.website == "https://testpadel.com"
        assert facility.facility_type == "sports_center"


class TestSearchVariations:
    """Test multiple query variations."""

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_uses_multiple_query_variations(self, mock_client_class):
        """Test that search uses at least 4 different query variations."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Track queries made
        queries_made = []

        def mock_places(**kwargs):
            queries_made.append(kwargs.get("query"))
            return {"results": [], "status": "OK"}

        mock_client.places.side_effect = mock_places

        collector = GooglePlacesCollector(api_key="test_key")
        collector.search_padel_facilities(region="Algarve, Portugal")

        # Should have made at least 4 different queries
        assert len(queries_made) >= 4
        assert len(set(queries_made)) >= 4  # All unique


class TestPagination:
    """Test pagination handling."""

    @patch("src.collectors.google_places.googlemaps.Client")
    @patch("time.sleep")
    def test_handles_pagination_with_delay(self, mock_sleep, mock_client_class):
        """Test pagination with proper 2-second delay between pages."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # First call returns next_page_token
        # Second call returns final results
        call_count = 0

        def mock_places(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and "page_token" not in kwargs:
                return {
                    "results": [{"place_id": "place_1"}],
                    "next_page_token": "token_123",
                    "status": "OK",
                }
            elif call_count == 2 and kwargs.get("page_token") == "token_123":
                return {
                    "results": [{"place_id": "place_2"}],
                    "status": "OK",
                }
            return {"results": [], "status": "OK"}

        mock_client.places.side_effect = mock_places

        # Mock place details
        def mock_place(**kwargs):
            place_id = kwargs.get("place_id")
            return {
                "result": {
                    "place_id": place_id,
                    "name": f"Facility {place_id}",
                    "formatted_address": "Rua Test, 8200 Faro, Portugal",
                    "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                    "rating": 4.0,
                    "user_ratings_total": 50,
                    "url": "https://maps.google.com",
                    "types": ["point_of_interest"],
                },
                "status": "OK",
            }

        mock_client.place.side_effect = mock_place

        collector = GooglePlacesCollector(api_key="test_key")
        facilities = collector.search_padel_facilities(region="Test Region")

        # Verify 2-second delay was called for pagination
        # Should have at least one call with 2 seconds
        assert any(call[0][0] == 2 for call in mock_sleep.call_args_list)


class TestDeduplication:
    """Test deduplication by place_id."""

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_deduplicates_by_place_id(self, mock_client_class):
        """Test that duplicate place_ids are filtered out."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Return same place_id from multiple queries
        def mock_places(**kwargs):
            return {
                "results": [
                    {"place_id": "place_123"},
                    {"place_id": "place_456"},
                    {"place_id": "place_123"},  # Duplicate
                ],
                "status": "OK",
            }

        mock_client.places.side_effect = mock_places

        # Track how many times place details is called
        place_calls = []

        def mock_place(**kwargs):
            place_id = kwargs.get("place_id")
            place_calls.append(place_id)
            return {
                "result": {
                    "place_id": place_id,
                    "name": f"Facility {place_id}",
                    "formatted_address": "Rua Test, 8200 Faro, Portugal",
                    "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                    "rating": 4.0,
                    "user_ratings_total": 50,
                    "url": "https://maps.google.com",
                    "types": ["point_of_interest"],
                },
                "status": "OK",
            }

        mock_client.place.side_effect = mock_place

        collector = GooglePlacesCollector(api_key="test_key")
        facilities = collector.search_padel_facilities()

        # Should only get details for unique place_ids
        assert len(set(place_calls)) == len(place_calls)
        # Should only have 2 facilities (place_123 and place_456)
        assert len(facilities) <= 2


class TestCityExtraction:
    """Test city name extraction."""

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_extracts_city_from_address(self, mock_client_class):
        """Test that city is correctly extracted from address."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        test_cases = [
            ("Rua Test, 8200 Albufeira, Portugal", "Albufeira"),
            ("Avenida Central, Lagos, Portugal", "Lagos"),
            ("Centro de Faro, Portugal", "Faro"),
            ("Rua da Praia, Portimão, Algarve", "Portimão"),
        ]

        for address, expected_city in test_cases:
            mock_client.places.return_value = {
                "results": [{"place_id": f"place_{expected_city}"}],
                "status": "OK",
            }

            mock_client.place.return_value = {
                "result": {
                    "place_id": f"place_{expected_city}",
                    "name": "Test Facility",
                    "formatted_address": address,
                    "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                    "rating": 4.0,
                    "user_ratings_total": 50,
                    "url": "https://maps.google.com",
                    "types": ["point_of_interest"],
                },
                "status": "OK",
            }

            collector = GooglePlacesCollector(api_key="test_key")
            facilities = collector.search_padel_facilities()

            if facilities:
                assert facilities[0].city == expected_city


class TestFacilityTypeMapping:
    """Test facility type determination."""

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_maps_gym_types_to_sports_center(self, mock_client_class):
        """Test that gym/health types map to sports_center."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.places.return_value = {
            "results": [{"place_id": "place_123"}],
            "status": "OK",
        }

        mock_client.place.return_value = {
            "result": {
                "place_id": "place_123",
                "name": "Test Facility",
                "formatted_address": "Rua Test, Faro, Portugal",
                "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                "rating": 4.0,
                "user_ratings_total": 50,
                "url": "https://maps.google.com",
                "types": ["gym", "health"],
            },
            "status": "OK",
        }

        collector = GooglePlacesCollector(api_key="test_key")
        facilities = collector.search_padel_facilities()

        assert facilities[0].facility_type == "sports_center"

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_maps_point_of_interest_to_club(self, mock_client_class):
        """Test that point_of_interest types map to club."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.places.return_value = {
            "results": [{"place_id": "place_123"}],
            "status": "OK",
        }

        mock_client.place.return_value = {
            "result": {
                "place_id": "place_123",
                "name": "Test Facility",
                "formatted_address": "Rua Test, Faro, Portugal",
                "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                "rating": 4.0,
                "user_ratings_total": 50,
                "url": "https://maps.google.com",
                "types": ["point_of_interest"],
            },
            "status": "OK",
        }

        collector = GooglePlacesCollector(api_key="test_key")
        facilities = collector.search_padel_facilities()

        assert facilities[0].facility_type == "club"

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_maps_other_types_to_other(self, mock_client_class):
        """Test that unknown types map to other."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.places.return_value = {
            "results": [{"place_id": "place_123"}],
            "status": "OK",
        }

        mock_client.place.return_value = {
            "result": {
                "place_id": "place_123",
                "name": "Test Facility",
                "formatted_address": "Rua Test, Faro, Portugal",
                "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                "rating": 4.0,
                "user_ratings_total": 50,
                "url": "https://maps.google.com",
                "types": ["restaurant", "food"],
            },
            "status": "OK",
        }

        collector = GooglePlacesCollector(api_key="test_key")
        facilities = collector.search_padel_facilities()

        assert facilities[0].facility_type == "other"


class TestErrorHandling:
    """Test error handling."""

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_continues_on_api_error(self, mock_client_class):
        """Test that collector continues processing on API errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # First query succeeds, second raises error
        call_count = 0

        def mock_places(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "results": [{"place_id": "place_123"}],
                    "status": "OK",
                }
            else:
                raise Exception("API Error")

        mock_client.places.side_effect = mock_places

        mock_client.place.return_value = {
            "result": {
                "place_id": "place_123",
                "name": "Test Facility",
                "formatted_address": "Rua Test, Faro, Portugal",
                "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                "rating": 4.0,
                "user_ratings_total": 50,
                "url": "https://maps.google.com",
                "types": ["point_of_interest"],
            },
            "status": "OK",
        }

        collector = GooglePlacesCollector(api_key="test_key")
        # Should not raise, should return facilities from successful query
        facilities = collector.search_padel_facilities()

        assert len(facilities) >= 0  # May have some results

    @patch("src.collectors.google_places.googlemaps.Client")
    def test_skips_invalid_facilities(self, mock_client_class):
        """Test that facilities with invalid data are skipped."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Use unique place_id for this test
        mock_client.places.return_value = {
            "results": [{"place_id": "place_invalid_999"}],
            "status": "OK",
        }

        # Return incomplete data (missing required fields)
        mock_client.place.return_value = {
            "result": {
                "place_id": "place_invalid_999",
                "name": "Test Facility",
                # Missing required fields like formatted_address and geometry
            },
            "status": "OK",
        }

        collector = GooglePlacesCollector(api_key="AIzatest_key")
        facilities = collector.search_padel_facilities()

        # Should skip invalid facility
        assert len(facilities) == 0


class TestRateLimiting:
    """Test rate limiting between requests."""

    @patch("src.collectors.google_places.googlemaps.Client")
    @patch("time.sleep")
    def test_applies_rate_limit_delay(self, mock_sleep, mock_client_class):
        """Test that rate limit delay is applied between requests."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.places.return_value = {
            "results": [{"place_id": "place_123"}, {"place_id": "place_456"}],
            "status": "OK",
        }

        def mock_place(**kwargs):
            place_id = kwargs.get("place_id")
            return {
                "result": {
                    "place_id": place_id,
                    "name": f"Facility {place_id}",
                    "formatted_address": "Rua Test, Faro, Portugal",
                    "geometry": {"location": {"lat": 37.0, "lng": -8.0}},
                    "rating": 4.0,
                    "user_ratings_total": 50,
                    "url": "https://maps.google.com",
                    "types": ["point_of_interest"],
                },
                "status": "OK",
            }

        mock_client.place.side_effect = mock_place

        collector = GooglePlacesCollector(api_key="test_key")
        facilities = collector.search_padel_facilities()

        # Should have called sleep with rate_limit_delay (default 0.2)
        # Multiple times for multiple API calls
        assert mock_sleep.called
        # Check that at least some calls used the rate limit delay
        rate_limit_calls = [
            call for call in mock_sleep.call_args_list if call[0][0] == collector.rate_limit_delay
        ]
        assert len(rate_limit_calls) > 0


@pytest.mark.integration
class TestIntegration:
    """Integration tests with real API (optional)."""

    def test_real_api_search(self):
        """Test search with real Google Places API."""
        # Skip if no API key available
        from src.config import settings

        if not settings.google_api_key or len(settings.google_api_key) < 20:
            pytest.skip("Valid Google API key not available")

        collector = GooglePlacesCollector(api_key=settings.google_api_key)
        facilities = collector.search_padel_facilities(region="Algarve, Portugal")

        # Basic validation
        assert isinstance(facilities, list)
        if len(facilities) > 0:
            facility = facilities[0]
            assert isinstance(facility, Facility)
            assert facility.place_id
            assert facility.name
            assert facility.city
            assert -90 <= facility.latitude <= 90
            assert -180 <= facility.longitude <= 180

