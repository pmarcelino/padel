"""
Unit tests for Review Collector.

Tests the ReviewCollector with mocked API responses to verify:
- Initialization
- Successful review fetching
- Empty review handling
- API error handling
- Empty text filtering
- HTTP 429 rate limiting with exponential backoff
- Max retries exceeded
- Rate limiting between requests
"""

import time
from unittest.mock import MagicMock, Mock, patch, call

import pytest
from googlemaps.exceptions import ApiError

from src.collectors.review_collector import ReviewCollector
from src.config import settings


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


class TestReviewCollectorInit:
    """Test collector initialization."""

    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_init_with_api_key(self, mock_client_class):
        """Test collector can be initialized with API key."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        collector = ReviewCollector(api_key="AIzatest_key")
        assert collector.api_key == "AIzatest_key"
        mock_client_class.assert_called_once_with(key="AIzatest_key")

    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_init_loads_rate_limit_from_settings(self, mock_client_class):
        """Test that rate limit delay is loaded from settings."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        collector = ReviewCollector(api_key="AIzatest_key")
        # Should have rate_limit_delay attribute from settings
        assert hasattr(collector, "rate_limit_delay")
        assert collector.rate_limit_delay == settings.rate_limit_delay
        assert collector.rate_limit_delay > 0


class TestSuccessfulReviewFetching:
    """Test successful review fetching."""

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_get_reviews_success(self, mock_client_class, mock_sleep):
        """Test successful review fetching returns list of review texts."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock Place Details API response with reviews
        mock_client.place.return_value = {
            "result": {
                "reviews": [
                    {
                        "author_name": "User 1",
                        "rating": 5,
                        "text": "Great padel club with excellent outdoor courts.",
                        "time": 1234567890
                    },
                    {
                        "author_name": "User 2",
                        "rating": 4,
                        "text": "Indoor courts are perfect for rainy days.",
                        "time": 1234567891
                    },
                    {
                        "author_name": "User 3",
                        "rating": 3,
                        "text": "Nice place but can get crowded on weekends.",
                        "time": 1234567892
                    }
                ]
            }
        }
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        # Verify returns list of strings
        assert isinstance(reviews, list)
        assert len(reviews) == 3
        assert all(isinstance(r, str) for r in reviews)
        
        # Verify correct text extraction
        assert reviews[0] == "Great padel club with excellent outdoor courts."
        assert reviews[1] == "Indoor courts are perfect for rainy days."
        assert reviews[2] == "Nice place but can get crowded on weekends."
        
        # Verify API was called correctly
        mock_client.place.assert_called_once_with(
            place_id="place_123",
            fields=["reviews"]
        )
        
        # Verify rate limit delay was applied
        mock_sleep.assert_called_with(settings.rate_limit_delay)

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_get_reviews_respects_max_reviews(self, mock_client_class, mock_sleep):
        """Test that max_reviews parameter limits the number of reviews returned."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API response with 5 reviews
        mock_client.place.return_value = {
            "result": {
                "reviews": [
                    {"text": f"Review {i}", "rating": 5} for i in range(5)
                ]
            }
        }
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123", max_reviews=3)
        
        # Should return only 3 reviews
        assert len(reviews) == 3
        assert reviews == ["Review 0", "Review 1", "Review 2"]


class TestFacilityWithoutReviews:
    """Test facility without reviews."""

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_get_reviews_no_reviews(self, mock_client_class, mock_sleep):
        """Test facility without reviews returns empty list."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API response with empty reviews array
        mock_client.place.return_value = {
            "result": {
                "reviews": []
            }
        }
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        assert reviews == []

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_get_reviews_missing_reviews_field(self, mock_client_class, mock_sleep):
        """Test facility with missing reviews field returns empty list."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API response without reviews field
        mock_client.place.return_value = {
            "result": {}
        }
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        assert reviews == []


class TestAPIErrorHandling:
    """Test API error handling."""

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_get_reviews_api_error(self, mock_client_class, mock_sleep, caplog):
        """Test API error returns empty list and logs error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API to raise exception
        mock_client.place.side_effect = ApiError("API_ERROR")
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        # Should return empty list, not raise exception
        assert reviews == []
        
        # Should log error with place_id context
        assert "place_123" in caplog.text.lower() or "error" in caplog.text.lower()

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_get_reviews_generic_exception(self, mock_client_class, mock_sleep, caplog):
        """Test generic exception returns empty list and logs error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API to raise generic exception
        mock_client.place.side_effect = Exception("Unexpected error")
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        # Should return empty list, not raise exception
        assert reviews == []
        
        # Should log error
        assert "error" in caplog.text.lower()


class TestEmptyTextFiltering:
    """Test filtering of empty review texts."""

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_get_reviews_filters_empty_text(self, mock_client_class, mock_sleep):
        """Test that empty review texts are filtered out."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API response with mix of valid and empty texts
        mock_client.place.return_value = {
            "result": {
                "reviews": [
                    {"text": "Good review", "rating": 5},
                    {"text": "", "rating": 4},  # Empty string
                    {"text": "Another good review", "rating": 4},
                    {"rating": 3},  # Missing text field
                    {"text": "   ", "rating": 3},  # Whitespace only
                    {"text": "Final good review", "rating": 5}
                ]
            }
        }
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        # Should return only non-empty texts
        assert len(reviews) == 3
        assert reviews == ["Good review", "Another good review", "Final good review"]


class TestHTTP429RateLimitBackoff:
    """Test HTTP 429 rate limiting with exponential backoff."""

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_rate_limit_retry_success(self, mock_client_class, mock_sleep, caplog):
        """Test exponential backoff succeeds on retry after rate limit errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API to fail twice with rate limit, then succeed
        mock_client.place.side_effect = [
            ApiError("RESOURCE_EXHAUSTED"),
            ApiError("RESOURCE_EXHAUSTED"),
            {
                "result": {
                    "reviews": [
                        {"text": "Success after retry", "rating": 5}
                    ]
                }
            }
        ]
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        # Should succeed on 3rd attempt
        assert len(reviews) == 1
        assert reviews[0] == "Success after retry"
        
        # Verify exponential backoff delays (1s, 2s)
        assert mock_sleep.call_count >= 2
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        # First two calls should be exponential backoff (1s, 2s)
        assert 1 in sleep_calls
        assert 2 in sleep_calls
        
        # Verify rate limiting was logged
        assert "rate limit" in caplog.text.lower() or "retry" in caplog.text.lower()

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_rate_limit_with_429_in_message(self, mock_client_class, mock_sleep):
        """Test that HTTP 429 errors are detected from error message."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API to fail with 429 in message, then succeed
        mock_client.place.side_effect = [
            ApiError("HTTP 429: Too Many Requests"),
            {
                "result": {
                    "reviews": [{"text": "Success", "rating": 5}]
                }
            }
        ]
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        # Should succeed after retry
        assert len(reviews) == 1
        assert reviews[0] == "Success"


class TestHTTP429MaxRetriesExceeded:
    """Test HTTP 429 max retries exceeded."""

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_rate_limit_max_retries_exceeded(self, mock_client_class, mock_sleep, caplog):
        """Test that max retries (3) is enforced for rate limit errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API to always fail with rate limit error
        mock_client.place.side_effect = ApiError("RESOURCE_EXHAUSTED")
        
        collector = ReviewCollector(api_key="AIzatest_key")
        reviews = collector.get_reviews(place_id="place_123")
        
        # Should return empty list after max retries
        assert reviews == []
        
        # Should have attempted exactly 3 times
        assert mock_client.place.call_count == 3
        
        # Should have logged error about max retries
        assert "max" in caplog.text.lower() or "retry" in caplog.text.lower()


class TestRateLimitingBetweenRequests:
    """Test rate limiting between requests."""

    @patch("src.collectors.review_collector.time.sleep")
    @patch("src.collectors.review_collector.googlemaps.Client")
    def test_rate_limit_delay_applied(self, mock_client_class, mock_sleep):
        """Test that rate limit delay is applied after successful API call."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.place.return_value = {
            "result": {
                "reviews": [{"text": "Review", "rating": 5}]
            }
        }
        
        collector = ReviewCollector(api_key="AIzatest_key")
        collector.get_reviews(place_id="place_123")
        
        # Verify time.sleep was called with rate_limit_delay
        mock_sleep.assert_called_with(settings.rate_limit_delay)
        
        # Verify it was called at least once (after the successful API call)
        assert mock_sleep.call_count >= 1

