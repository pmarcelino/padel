"""
Unit tests for Indoor/Outdoor Analyzer.

Tests the IndoorOutdoorAnalyzer with mocked LLM responses to verify:
- Initialization with different providers
- High/low confidence handling
- API error handling
- Review limit enforcement
- Facility enrichment logic
- Cost tracking
- JSON parsing
- Integration tests (marked as optional)
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, call
from typing import List

import pytest

from src.models.facility import Facility


# We'll import these after implementation
# from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
# from src.enrichers.base_llm import BaseLLMEnricher


class TestIndoorOutdoorAnalyzerInit:
    """Test analyzer initialization."""

    def test_init_openai_provider(self):
        """Test analyzer can be initialized with OpenAI provider."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        analyzer = IndoorOutdoorAnalyzer(
            provider="openai",
            model="gpt-4o-mini",
            api_key="test_key"
        )
        assert analyzer.provider == "openai"
        assert analyzer.model == "gpt-4o-mini"
        assert analyzer.api_key == "test_key"

    def test_init_anthropic_provider(self):
        """Test analyzer can be initialized with Anthropic provider."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        analyzer = IndoorOutdoorAnalyzer(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            api_key="test_key"
        )
        assert analyzer.provider == "anthropic"
        assert analyzer.model == "claude-3-5-haiku-20241022"

    def test_init_invalid_provider(self):
        """Test initialization with invalid provider raises ValueError."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        with pytest.raises(ValueError, match="Invalid provider"):
            IndoorOutdoorAnalyzer(provider="invalid", api_key="test_key")

    def test_init_default_values(self):
        """Test analyzer uses default values from settings."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        analyzer = IndoorOutdoorAnalyzer(api_key="test_key")
        # Should use defaults from config (openai, gpt-4o-mini)
        assert analyzer.provider in ["openai", "anthropic"]
        assert analyzer.model is not None

    def test_init_no_api_key_uses_env(self):
        """Test initialization without api_key uses environment variable."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        with patch("src.enrichers.indoor_outdoor_analyzer.settings") as mock_settings:
            mock_settings.openai_api_key = "env_key"
            mock_settings.llm_provider = "openai"
            mock_settings.llm_model = "gpt-4o-mini"
            
            analyzer = IndoorOutdoorAnalyzer()
            assert analyzer.api_key == "env_key"


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_openai_high_confidence_indoor(self, mock_openai_class):
        """Test OpenAI provider returns 'indoor' with high confidence."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "indoor", "confidence": 0.9, "reasoning": "Multiple reviews mention indoor courts and climate control"}'
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 30
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Great indoor courts!", "Love the climate controlled indoor facility"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result == "indoor"
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_openai_low_confidence_returns_none(self, mock_openai_class):
        """Test OpenAI provider returns None with low confidence."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "outdoor", "confidence": 0.4, "reasoning": "Not enough information"}'
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 20
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Nice place"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result is None

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_openai_outdoor_high_confidence(self, mock_openai_class):
        """Test OpenAI provider returns 'outdoor' with high confidence."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "outdoor", "confidence": 0.85, "reasoning": "Reviews mention sun, outdoor facilities"}'
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 25
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Beautiful outdoor courts with great sun exposure"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result == "outdoor"

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_openai_both_courts(self, mock_openai_class):
        """Test OpenAI provider returns 'both' when facility has both types."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "both", "confidence": 0.95, "reasoning": "Reviews clearly mention both indoor and outdoor courts"}'
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 35
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Has both indoor and outdoor courts", "Play inside when it rains, outside when sunny"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result == "both"

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_openai_unknown_returns_none(self, mock_openai_class):
        """Test OpenAI provider returns None when court_type is 'unknown'."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "unknown", "confidence": 0.9, "reasoning": "No mentions of indoor or outdoor"}'
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 15
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Great service"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result is None


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""

    @patch("src.enrichers.indoor_outdoor_analyzer.anthropic.Anthropic")
    def test_anthropic_both_courts(self, mock_anthropic_class):
        """Test Anthropic provider returns 'both' with high confidence."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"court_type": "both", "confidence": 0.85, "reasoning": "Facility has indoor and outdoor options"}'
        mock_response.usage.input_tokens = 180
        mock_response.usage.output_tokens = 28
        mock_client.messages.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="anthropic", api_key="test_key")
        reviews = ["Indoor courts for winter, outdoor for summer"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result == "both"
        mock_client.messages.create.assert_called_once()

    @patch("src.enrichers.indoor_outdoor_analyzer.anthropic.Anthropic")
    def test_anthropic_indoor_high_confidence(self, mock_anthropic_class):
        """Test Anthropic provider returns 'indoor' with high confidence."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"court_type": "indoor", "confidence": 0.92, "reasoning": "All reviews mention covered courts"}'
        mock_response.usage.input_tokens = 160
        mock_response.usage.output_tokens = 25
        mock_client.messages.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="anthropic", api_key="test_key")
        reviews = ["Perfect indoor facility"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result == "indoor"


class TestReviewProcessing:
    """Test review processing logic."""

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_empty_reviews_returns_none(self, mock_openai_class):
        """Test empty review list returns None without API call."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        
        result = analyzer.analyze_reviews([])
        
        assert result is None
        # Should not make API call for empty reviews
        mock_client.chat.completions.create.assert_not_called()

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_review_limit_enforced(self, mock_openai_class):
        """Test only first 20 reviews are used."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "indoor", "confidence": 0.8, "reasoning": "Indoor mentions"}'
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 30
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        
        # Create 30 reviews
        reviews = [f"Review {i}" for i in range(30)]
        
        result = analyzer.analyze_reviews(reviews)
        
        # Check that the prompt contains only 20 reviews
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        prompt_content = messages[0]['content']
        
        # Should only have first 20 reviews in prompt
        assert "Review 19" in prompt_content
        assert "Review 20" not in prompt_content

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_none_reviews_returns_none(self, mock_openai_class):
        """Test None review list returns None without API call."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        
        result = analyzer.analyze_reviews(None)
        
        assert result is None
        mock_client.chat.completions.create.assert_not_called()


class TestErrorHandling:
    """Test error handling and graceful failures."""

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_api_error_returns_none(self, mock_openai_class):
        """Test API error returns None gracefully."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Indoor courts"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result is None

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_invalid_json_returns_none(self, mock_openai_class):
        """Test invalid JSON response returns None gracefully."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON {not valid"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Indoor courts"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result is None

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_missing_fields_returns_none(self, mock_openai_class):
        """Test JSON with missing required fields returns None."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "indoor"}'  # Missing confidence
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        reviews = ["Indoor courts"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result is None

    @patch("src.enrichers.indoor_outdoor_analyzer.anthropic.Anthropic")
    def test_anthropic_api_error_returns_none(self, mock_anthropic_class):
        """Test Anthropic API error returns None gracefully."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("Anthropic API Error")
        
        analyzer = IndoorOutdoorAnalyzer(provider="anthropic", api_key="test_key")
        reviews = ["Outdoor courts"]
        
        result = analyzer.analyze_reviews(reviews)
        
        assert result is None


class TestFacilityEnrichment:
    """Test facility enrichment functionality."""

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_enrich_facility_not_set(self, mock_openai_class):
        """Test facility enrichment when indoor_outdoor is None."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "indoor", "confidence": 0.9, "reasoning": "Indoor courts"}'
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 25
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        
        facility = Facility(
            place_id="test123",
            name="Test Padel",
            address="Test Address",
            city="Lisbon",
            latitude=38.7223,
            longitude=-9.1393,
            indoor_outdoor=None
        )
        
        reviews = ["Great indoor facility"]
        
        enriched = analyzer.enrich_facility(facility, reviews)
        
        assert enriched.indoor_outdoor == "indoor"
        # Verify last_updated was updated
        assert enriched.last_updated >= facility.last_updated

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_enrich_facility_already_set(self, mock_openai_class):
        """Test facility enrichment skips when indoor_outdoor already set."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        
        facility = Facility(
            place_id="test123",
            name="Test Padel",
            address="Test Address",
            city="Lisbon",
            latitude=38.7223,
            longitude=-9.1393,
            indoor_outdoor="outdoor"  # Already set
        )
        
        reviews = ["Great indoor facility"]
        
        enriched = analyzer.enrich_facility(facility, reviews)
        
        # Should remain unchanged
        assert enriched.indoor_outdoor == "outdoor"
        # Should not call API
        mock_client.chat.completions.create.assert_not_called()

    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_enrich_facility_low_confidence(self, mock_openai_class):
        """Test facility enrichment with low confidence keeps None."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "indoor", "confidence": 0.3, "reasoning": "Not sure"}'
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 15
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", api_key="test_key")
        
        facility = Facility(
            place_id="test123",
            name="Test Padel",
            address="Test Address",
            city="Lisbon",
            latitude=38.7223,
            longitude=-9.1393,
            indoor_outdoor=None
        )
        
        reviews = ["Nice place"]
        
        enriched = analyzer.enrich_facility(facility, reviews)
        
        # Should remain None due to low confidence
        assert enriched.indoor_outdoor is None


class TestCostTracking:
    """Test cost tracking functionality."""

    @patch("src.enrichers.indoor_outdoor_analyzer.logger")
    @patch("src.enrichers.indoor_outdoor_analyzer.openai.OpenAI")
    def test_cost_tracking_logged(self, mock_openai_class, mock_logger):
        """Test that cost tracking logs are created."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"court_type": "indoor", "confidence": 0.9, "reasoning": "Indoor"}'
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 30
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", model="gpt-4o-mini", api_key="test_key")
        reviews = ["Indoor courts"]
        
        analyzer.analyze_reviews(reviews)
        
        # Verify cost logging was called - check all info calls
        assert mock_logger.info.called
        # Get all log messages
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        # Find the cost tracking message
        cost_log = [msg for msg in log_messages if "gpt-4o-mini" in msg and "tokens" in msg]
        assert len(cost_log) > 0, f"Cost log not found in: {log_messages}"
        assert "150 in" in cost_log[0]
        assert "30 out" in cost_log[0]
        assert "$" in cost_log[0]

    @patch("src.enrichers.indoor_outdoor_analyzer.logger")
    @patch("src.enrichers.indoor_outdoor_analyzer.anthropic.Anthropic")
    def test_anthropic_cost_tracking(self, mock_anthropic_class, mock_logger):
        """Test cost tracking for Anthropic provider."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"court_type": "outdoor", "confidence": 0.85, "reasoning": "Outdoor"}'
        mock_response.usage.input_tokens = 180
        mock_response.usage.output_tokens = 28
        mock_client.messages.create.return_value = mock_response
        
        analyzer = IndoorOutdoorAnalyzer(provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test_key")
        reviews = ["Outdoor courts"]
        
        analyzer.analyze_reviews(reviews)
        
        # Verify cost logging - check all info calls
        assert mock_logger.info.called
        # Get all log messages
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        # Find the cost tracking message
        cost_log = [msg for msg in log_messages if "claude-3-5-haiku-20241022" in msg and "tokens" in msg]
        assert len(cost_log) > 0, f"Cost log not found in: {log_messages}"
        assert "180 in" in cost_log[0]
        assert "28 out" in cost_log[0]


# ============================================================================
# Integration Tests (Optional - marked with pytest.mark.integration)
# ============================================================================

@pytest.mark.integration
class TestRealOpenAIIntegration:
    """Integration tests with real OpenAI API (optional)."""

    def test_real_openai_indoor_classification(self):
        """Test real OpenAI API call with indoor reviews."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        from src.config import settings
        
        if not settings.openai_api_key:
            pytest.skip("OpenAI API key not available")
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", model="gpt-4o-mini")
        
        reviews = [
            "Love the indoor courts, perfect for rainy days",
            "Climate controlled indoor facility is amazing",
            "The covered courts are always available regardless of weather"
        ]
        
        result = analyzer.analyze_reviews(reviews)
        
        # Should detect indoor
        assert result == "indoor"

    def test_real_openai_outdoor_classification(self):
        """Test real OpenAI API call with outdoor reviews."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        from src.config import settings
        
        if not settings.openai_api_key:
            pytest.skip("OpenAI API key not available")
        
        analyzer = IndoorOutdoorAnalyzer(provider="openai", model="gpt-4o-mini")
        
        reviews = [
            "Beautiful outdoor courts with great views",
            "Love playing under the sun",
            "Open-air courts are perfect for summer evenings"
        ]
        
        result = analyzer.analyze_reviews(reviews)
        
        # Should detect outdoor
        assert result == "outdoor"


@pytest.mark.integration
class TestRealAnthropicIntegration:
    """Integration tests with real Anthropic API (optional)."""

    def test_real_anthropic_both_classification(self):
        """Test real Anthropic API call with both court types."""
        from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
        from src.config import settings
        
        if not settings.anthropic_api_key:
            pytest.skip("Anthropic API key not available")
        
        analyzer = IndoorOutdoorAnalyzer(provider="anthropic", model="claude-3-5-haiku-20241022")
        
        reviews = [
            "Has both indoor and outdoor courts",
            "Play inside when it rains, outside when sunny",
            "Great variety with covered and open courts"
        ]
        
        result = analyzer.analyze_reviews(reviews)
        
        # Should detect both
        assert result == "both"

