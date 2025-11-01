"""
Unit tests for Google Trends collector.

Tests the GoogleTrendsCollector with mocked API responses to verify:
- Basic initialization
- Regional interest data retrieval
- Score normalization (0-100 range)
- Portuguese character handling
- Missing data handling (returns 0.0)
- Error handling
- Cache integration
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from src.collectors.google_trends import GoogleTrendsCollector
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


class TestGoogleTrendsCollectorInit:
    """Test collector initialization."""

    @patch("src.collectors.google_trends.TrendReq")
    def test_init_creates_pytrends_client(self, mock_trend_req):
        """Test collector can be initialized without API key."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        collector = GoogleTrendsCollector()
        
        assert collector is not None
        # Verify TrendReq was called with correct parameters
        mock_trend_req.assert_called_once_with(hl='pt-PT', tz=360)

    @patch("src.collectors.google_trends.TrendReq")
    def test_init_sets_rate_limit_delay(self, mock_trend_req):
        """Test that rate limit delay is set from settings."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        collector = GoogleTrendsCollector()
        
        assert hasattr(collector, "rate_limit_delay")
        assert collector.rate_limit_delay > 0


class TestBasicRegionalInterest:
    """Test basic regional interest retrieval."""

    @patch("src.collectors.google_trends.TrendReq")
    def test_get_regional_interest_returns_dict(self, mock_trend_req):
        """Test that get_regional_interest returns a dictionary."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        # Mock interest_by_region response
        mock_df = pd.DataFrame({
            'geoName': ['Faro', 'Lagos', 'Albufeira'],
            'padel': [100, 75, 50]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=["Faro", "Lagos", "Albufeira"]
        )

        assert isinstance(result, dict)
        assert len(result) == 3
        assert all(isinstance(v, float) for v in result.values())

    @patch("src.collectors.google_trends.TrendReq")
    def test_get_regional_interest_with_timeframe(self, mock_trend_req):
        """Test that custom timeframe is used."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        mock_df = pd.DataFrame({
            'geoName': ['Faro'],
            'padel': [80]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=["Faro"],
            timeframe="today 6-m"
        )

        assert "Faro" in result


class TestScoreNormalization:
    """Test score normalization to 0-100 range."""

    @patch("src.collectors.google_trends.TrendReq")
    def test_scores_in_valid_range(self, mock_trend_req):
        """Test that all scores are in 0-100 range."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        # Mock with various scores
        mock_df = pd.DataFrame({
            'geoName': ['Faro', 'Lagos', 'Albufeira', 'Tavira'],
            'padel': [100, 75, 50, 25]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=["Faro", "Lagos", "Albufeira", "Tavira"]
        )

        # Verify all scores are in 0-100 range
        for score in result.values():
            assert 0.0 <= score <= 100.0

    @patch("src.collectors.google_trends.TrendReq")
    def test_scores_are_floats(self, mock_trend_req):
        """Test that scores are returned as floats."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        mock_df = pd.DataFrame({
            'geoName': ['Faro'],
            'padel': [85]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=["Faro"]
        )

        assert isinstance(result["Faro"], float)


class TestPortugueseCharacters:
    """Test handling of Portuguese characters in city names."""

    @patch("src.collectors.google_trends.TrendReq")
    def test_handles_accented_characters(self, mock_trend_req):
        """Test cities with Portuguese accents."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        # Test cities with accents
        cities_with_accents = ["São Brás de Alportel", "Olhão"]

        mock_df = pd.DataFrame({
            'geoName': cities_with_accents,
            'padel': [60, 70]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=cities_with_accents
        )

        assert "São Brás de Alportel" in result
        assert "Olhão" in result
        assert result["São Brás de Alportel"] == 60.0
        assert result["Olhão"] == 70.0

    @patch("src.collectors.google_trends.TrendReq")
    def test_all_algarve_cities(self, mock_trend_req):
        """Test with all 15 Algarve municipalities."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        algarve_cities = [
            "Albufeira", "Aljezur", "Castro Marim", "Faro", "Lagoa",
            "Lagos", "Loulé", "Monchique", "Olhão", "Portimão",
            "São Brás de Alportel", "Silves", "Tavira", "Vila do Bispo",
            "Vila Real de Santo António"
        ]

        # Mock data for all cities
        mock_df = pd.DataFrame({
            'geoName': algarve_cities,
            'padel': [80 + i for i in range(len(algarve_cities))]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=algarve_cities
        )

        # Verify all cities are in result
        assert len(result) == 15
        for city in algarve_cities:
            assert city in result


class TestMissingData:
    """Test handling of missing/no data for regions."""

    @patch("src.collectors.google_trends.TrendReq")
    def test_missing_data_returns_zero(self, mock_trend_req):
        """Test that cities with no data return 0.0."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        requested_cities = ["Faro", "Lagos", "Monchique"]
        
        # Mock returns data only for Faro and Lagos
        mock_df = pd.DataFrame({
            'geoName': ['Faro', 'Lagos'],
            'padel': [90, 80]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=requested_cities
        )

        # Cities with data should have their scores
        assert result["Faro"] == 90.0
        assert result["Lagos"] == 80.0
        # Missing city should return 0.0
        assert result["Monchique"] == 0.0

    @patch("src.collectors.google_trends.TrendReq")
    def test_empty_response_returns_zeros(self, mock_trend_req):
        """Test that empty response returns 0.0 for all cities."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        requested_cities = ["Faro", "Lagos"]
        
        # Mock returns empty DataFrame
        mock_df = pd.DataFrame(columns=['padel'])
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=requested_cities
        )

        # All cities should return 0.0
        assert result["Faro"] == 0.0
        assert result["Lagos"] == 0.0


class TestErrorHandling:
    """Test error handling for API failures."""

    @patch("src.collectors.google_trends.TrendReq")
    def test_api_error_returns_zeros(self, mock_trend_req):
        """Test that API errors return 0.0 for all cities."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        # Mock API error
        mock_client.build_payload.side_effect = Exception("API Error")

        requested_cities = ["Faro", "Lagos"]

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=requested_cities
        )

        # Should return 0.0 for all cities on error
        assert result == {"Faro": 0.0, "Lagos": 0.0}

    @patch("src.collectors.google_trends.TrendReq")
    def test_network_timeout_handled(self, mock_trend_req):
        """Test that network timeouts are handled gracefully."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        # Mock timeout error
        mock_client.interest_by_region.side_effect = TimeoutError("Network timeout")

        requested_cities = ["Faro"]

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="padel",
            regions=requested_cities
        )

        # Should return 0.0 on timeout
        assert result == {"Faro": 0.0}

    @patch("src.collectors.google_trends.TrendReq")
    def test_invalid_keyword_handled(self, mock_trend_req):
        """Test that invalid keywords are handled gracefully."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        # Mock error for invalid keyword
        mock_client.build_payload.side_effect = ValueError("Invalid keyword")

        requested_cities = ["Faro"]

        collector = GoogleTrendsCollector()
        result = collector.get_regional_interest(
            keyword="",
            regions=requested_cities
        )

        # Should return 0.0 for all cities
        assert result == {"Faro": 0.0}


class TestCacheIntegration:
    """Test caching decorator integration."""

    @patch("src.collectors.google_trends.TrendReq")
    def test_cache_decorator_applied(self, mock_trend_req):
        """Test that caching decorator is applied to get_regional_interest."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        mock_df = pd.DataFrame({
            'geoName': ['Faro'],
            'padel': [85]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        
        # First call
        result1 = collector.get_regional_interest(
            keyword="padel",
            regions=["Faro"]
        )
        
        # Second call with same params
        result2 = collector.get_regional_interest(
            keyword="padel",
            regions=["Faro"]
        )

        # Results should be identical
        assert result1 == result2
        assert result1["Faro"] == 85.0

    @patch("src.collectors.google_trends.TrendReq")
    def test_different_params_not_cached(self, mock_trend_req):
        """Test that different parameters result in separate cache entries."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        # Different responses for different calls
        call_count = [0]
        
        def mock_interest_by_region(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock_df = pd.DataFrame({
                    'geoName': ['Faro'],
                    'padel': [85]
                })
            else:
                mock_df = pd.DataFrame({
                    'geoName': ['Lagos'],
                    'padel': [70]
                })
            mock_df.set_index('geoName', inplace=True)
            return mock_df

        mock_client.interest_by_region.side_effect = mock_interest_by_region

        collector = GoogleTrendsCollector()
        
        # Different keywords should not use same cache
        result1 = collector.get_regional_interest(
            keyword="padel",
            regions=["Faro"]
        )
        
        result2 = collector.get_regional_interest(
            keyword="tennis",
            regions=["Lagos"]
        )

        # Different results for different params
        assert result1 != result2


class TestRateLimiting:
    """Test rate limiting implementation."""

    @patch("src.collectors.google_trends.TrendReq")
    @patch("time.sleep")
    def test_applies_rate_limit_delay(self, mock_sleep, mock_trend_req):
        """Test that rate limit delay is applied."""
        mock_client = MagicMock()
        mock_trend_req.return_value = mock_client

        mock_df = pd.DataFrame({
            'geoName': ['Faro'],
            'padel': [85]
        })
        mock_df.set_index('geoName', inplace=True)
        mock_client.interest_by_region.return_value = mock_df

        collector = GoogleTrendsCollector()
        collector.get_regional_interest(
            keyword="padel",
            regions=["Faro"]
        )

        # Should have called sleep with rate_limit_delay
        assert mock_sleep.called

