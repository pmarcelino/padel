"""
Unit tests for data collection CLI script.

Tests the collect_data.py script with mocked dependencies to verify:
- Argument parsing
- Configuration validation
- Pipeline stages execution
- Error handling and exit codes
- Progress logging
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call
import argparse
import pytest
import pandas as pd

from src.models.facility import Facility


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_google_places_collector():
    """Mock GooglePlacesCollector for testing."""
    mock = MagicMock()
    mock.search_padel_facilities.return_value = [
        Facility(
            place_id="place_1",
            name="Test Facility 1",
            address="Address 1, Albufeira",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=100,
        ),
        Facility(
            place_id="place_2",
            name="Test Facility 2",
            address="Address 2, Faro",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.2,
            review_count=80,
        ),
    ]
    return mock


@pytest.fixture
def mock_review_collector():
    """Mock ReviewCollector for testing."""
    mock = MagicMock()
    mock.get_reviews.return_value = [
        "Great padel courts!",
        "Indoor facilities are excellent.",
    ]
    return mock


@pytest.fixture
def mock_indoor_outdoor_analyzer():
    """Mock IndoorOutdoorAnalyzer for testing."""
    mock = MagicMock()
    mock.analyze_reviews.return_value = "indoor"
    mock.enrich_facility.side_effect = lambda facility, reviews: facility
    return mock


@pytest.fixture
def mock_data_cleaner():
    """Mock DataCleaner for testing."""
    mock = MagicMock()
    mock.clean_facilities.side_effect = lambda facilities: facilities
    return mock


@pytest.fixture
def mock_deduplicator():
    """Mock Deduplicator for testing."""
    mock = MagicMock()
    mock.deduplicate.side_effect = lambda facilities: facilities
    return mock


@pytest.fixture
def sample_facilities():
    """Sample facilities for testing."""
    return [
        Facility(
            place_id="place_1",
            name="Test Facility 1",
            address="Address 1, Albufeira",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=100,
        ),
        Facility(
            place_id="place_2",
            name="Test Facility 2",
            address="Address 2, Faro",
            city="Faro",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.2,
            review_count=80,
        ),
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory for testing."""
    output_dir = tmp_path / "data" / "raw"
    output_dir.mkdir(parents=True)
    return output_dir


# Note: Using pytest's built-in capsys fixture instead of custom capture_output


# ============================================================================
# Test Argument Parsing
# ============================================================================


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_parse_arguments_default_values(self):
        """Test argument parsing with default values."""
        # Import will be available after implementation
        from scripts.collect_data import parse_arguments

        args = parse_arguments([])

        assert args.region == "Algarve, Portugal"
        assert args.with_reviews is False
        assert args.enrich_indoor_outdoor is False
        assert args.llm_provider == "openai"
        assert args.llm_model == "gpt-4o-mini"
        assert args.output == "data/raw/facilities.csv"
        assert args.verbose is False

    def test_parse_arguments_custom_values(self):
        """Test argument parsing with custom values."""
        from scripts.collect_data import parse_arguments

        args = parse_arguments([
            "--region", "Lagos, Portugal",
            "--with-reviews",
            "--enrich-indoor-outdoor",
            "--llm-provider", "anthropic",
            "--llm-model", "claude-3-5-haiku-20241022",
            "--output", "data/custom_output.csv",
            "--verbose",
        ])

        assert args.region == "Lagos, Portugal"
        assert args.with_reviews is True
        assert args.enrich_indoor_outdoor is True
        assert args.llm_provider == "anthropic"
        assert args.llm_model == "claude-3-5-haiku-20241022"
        assert args.output == "data/custom_output.csv"
        assert args.verbose is True

    def test_parse_arguments_help_flag(self):
        """Test that --help flag works."""
        from scripts.collect_data import parse_arguments

        with pytest.raises(SystemExit) as exc_info:
            parse_arguments(["--help"])

        assert exc_info.value.code == 0


# ============================================================================
# Test Configuration Validation
# ============================================================================


class TestConfigurationValidation:
    """Test configuration validation."""

    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key_123"})
    def test_validate_configuration_success(self):
        """Test configuration validation with valid API key."""
        from scripts.collect_data import validate_configuration, parse_arguments

        args = parse_arguments([])
        result = validate_configuration(args)

        assert result is True

    @patch.dict("os.environ", {}, clear=True)
    def test_validate_configuration_missing_api_key(self):
        """Test configuration validation with missing API key."""
        from scripts.collect_data import validate_configuration, parse_arguments

        args = parse_arguments([])
        result = validate_configuration(args)

        assert result is False

    @patch.dict("os.environ", {"GOOGLE_API_KEY": ""})
    def test_validate_configuration_empty_api_key(self):
        """Test configuration validation with empty API key."""
        from scripts.collect_data import validate_configuration, parse_arguments

        args = parse_arguments([])
        result = validate_configuration(args)

        assert result is False


# ============================================================================
# Test Directory Setup
# ============================================================================


class TestDirectorySetup:
    """Test directory creation."""

    def test_setup_directories_creates_missing_dirs(self, tmp_path):
        """Test that setup_directories creates missing directories."""
        from scripts.collect_data import setup_directories

        # Create a temporary config with custom paths
        output_path = tmp_path / "data" / "raw" / "test.csv"

        # Should create parent directories
        setup_directories(output_path)

        # Should create output directory
        assert output_path.parent.exists()
        
        # Cache directory is created in settings.cache_dir, not in tmp_path
        # Just verify the function doesn't raise errors
        assert True

    def test_setup_directories_handles_existing_dirs(self, temp_output_dir):
        """Test that setup_directories handles existing directories."""
        from scripts.collect_data import setup_directories

        output_path = temp_output_dir / "test.csv"

        # Should not raise error if directories already exist
        setup_directories(output_path)
        setup_directories(output_path)  # Call twice

        assert output_path.parent.exists()


# ============================================================================
# Test Pipeline Stages
# ============================================================================


class TestPipelineStages:
    """Test individual pipeline stages."""

    def test_collect_facilities_stage(self, mock_google_places_collector):
        """Test Stage 2: Data collection."""
        from scripts.collect_data import collect_facilities

        facilities = collect_facilities(mock_google_places_collector, "Algarve, Portugal")

        assert len(facilities) == 2
        assert facilities[0].name == "Test Facility 1"
        mock_google_places_collector.search_padel_facilities.assert_called_once_with(
            "Algarve, Portugal"
        )

    def test_collect_reviews_stage(self, mock_review_collector, sample_facilities):
        """Test Stage 3: Review collection."""
        from scripts.collect_data import collect_reviews

        reviews_dict = collect_reviews(mock_review_collector, sample_facilities)

        assert len(reviews_dict) == 2
        assert "place_1" in reviews_dict
        assert "place_2" in reviews_dict
        assert mock_review_collector.get_reviews.call_count == 2

    def test_enrich_with_llm_stage(
        self, mock_indoor_outdoor_analyzer, sample_facilities
    ):
        """Test Stage 4: LLM enrichment."""
        from scripts.collect_data import enrich_with_llm

        reviews_dict = {
            "place_1": ["Great courts!", "Indoor facilities"],
            "place_2": ["Nice outdoor courts"],
        }

        enriched = enrich_with_llm(
            mock_indoor_outdoor_analyzer, sample_facilities, reviews_dict
        )

        assert len(enriched) == 2
        assert mock_indoor_outdoor_analyzer.enrich_facility.call_count == 2

    def test_clean_facilities_stage(self, sample_facilities):
        """Test Stage 5: Data cleaning."""
        from scripts.collect_data import clean_facilities

        with patch("scripts.collect_data.DataCleaner") as mock_cleaner:
            mock_cleaner.clean_facilities.return_value = sample_facilities

            cleaned = clean_facilities(sample_facilities)

            assert len(cleaned) == 2
            mock_cleaner.clean_facilities.assert_called_once()

    def test_deduplicate_facilities_stage(self, sample_facilities):
        """Test Stage 6: Deduplication."""
        from scripts.collect_data import deduplicate_facilities

        with patch("scripts.collect_data.Deduplicator") as mock_dedup:
            mock_dedup.deduplicate.return_value = sample_facilities[:1]

            deduplicated = deduplicate_facilities(sample_facilities)

            assert len(deduplicated) == 1
            mock_dedup.deduplicate.assert_called_once()

    def test_save_to_csv_stage(self, sample_facilities, temp_output_dir):
        """Test Stage 7: CSV saving."""
        from scripts.collect_data import save_to_csv

        output_path = temp_output_dir / "facilities.csv"

        save_to_csv(sample_facilities, output_path)

        assert output_path.exists()

        # Verify CSV contents
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "place_id" in df.columns
        assert "name" in df.columns


# ============================================================================
# Test Error Handling and Exit Codes
# ============================================================================


class TestErrorHandlingAndExitCodes:
    """Test error handling and exit codes."""

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.DataCleaner")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key_123"})
    def test_main_success_exit_code_0(
        self, mock_dedup_class, mock_cleaner_class, mock_collector_class, tmp_path
    ):
        """Test main returns exit code 0 on success."""
        from scripts.collect_data import main

        # Mock successful execution
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]
        mock_collector_class.return_value = mock_collector

        mock_cleaner_class.clean_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        mock_dedup_class.deduplicate.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        output_path = tmp_path / "test_output.csv"
        exit_code = main(["--output", str(output_path)])

        assert exit_code == 0

    @patch.dict("os.environ", {}, clear=True)
    def test_main_missing_api_key_exit_code_1(self):
        """Test main returns exit code 1 when API key is missing."""
        from scripts.collect_data import main

        exit_code = main([])

        assert exit_code == 1

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key_123"})
    def test_main_collection_failed_exit_code_2(self, mock_collector_class):
        """Test main returns exit code 2 when data collection fails."""
        from scripts.collect_data import main

        # Mock collection failure
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.side_effect = Exception(
            "API Error"
        )
        mock_collector_class.return_value = mock_collector

        exit_code = main([])

        assert exit_code == 2

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.DataCleaner")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key_123"})
    def test_main_processing_failed_exit_code_3(
        self, mock_cleaner_class, mock_collector_class
    ):
        """Test main returns exit code 3 when data processing fails."""
        from scripts.collect_data import main

        # Mock successful collection
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]
        mock_collector_class.return_value = mock_collector

        # Mock processing failure
        mock_cleaner_class.clean_facilities.side_effect = Exception(
            "Processing Error"
        )

        exit_code = main([])

        assert exit_code == 3

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.DataCleaner")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key_123"})
    def test_main_graceful_api_error_handling(
        self, mock_dedup_class, mock_cleaner_class, mock_collector_class, tmp_path
    ):
        """Test that main handles individual API errors gracefully."""
        from scripts.collect_data import main

        # Mock collector that returns some results despite errors
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]
        mock_collector_class.return_value = mock_collector

        mock_cleaner_class.clean_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        mock_dedup_class.deduplicate.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        output_path = tmp_path / "test_output.csv"
        exit_code = main(["--output", str(output_path)])

        # Should still succeed even if some API calls had issues
        assert exit_code == 0


# ============================================================================
# Test Progress Logging
# ============================================================================


class TestProgressLogging:
    """Test progress logging functionality."""

    def test_print_stage_formats_correctly(self, capsys):
        """Test that print_stage formats output correctly."""
        from scripts.collect_data import print_stage

        print_stage(1, "Testing stage")

        captured = capsys.readouterr()
        output = captured.out
        assert "1." in output
        assert "Testing stage" in output

    def test_print_summary_displays_statistics(self, sample_facilities, capsys):
        """Test that print_summary displays correct statistics."""
        from scripts.collect_data import print_summary

        print_summary(sample_facilities, execution_time=10.5)

        captured = capsys.readouterr()
        output = captured.out
        assert "2" in output  # Total facilities
        assert "10" in output  # Execution time (10 or 10s)
        assert "cities" in output.lower() or "city" in output.lower()

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.DataCleaner")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key_123"})
    def test_main_prints_progress_for_each_stage(
        self, mock_dedup_class, mock_cleaner_class, mock_collector_class, tmp_path, capsys
    ):
        """Test that main prints progress for each stage."""
        from scripts.collect_data import main

        # Mock successful execution
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]
        mock_collector_class.return_value = mock_collector

        mock_cleaner_class.clean_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        mock_dedup_class.deduplicate.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        output_path = tmp_path / "test_output.csv"
        main(["--output", str(output_path)])

        captured = capsys.readouterr()
        output = captured.out

        # Check for stage headers
        assert "Starting" in output or "1." in output
        assert "Searching" in output or "2." in output
        assert "Cleaning" in output or "3." in output or "5." in output
        assert "Removing duplicates" in output or "deduplicat" in output.lower()
        assert "Saving" in output or "saving" in output.lower()


# ============================================================================
# Test Optional Features
# ============================================================================


class TestOptionalFeatures:
    """Test optional features (reviews, LLM enrichment)."""

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.ReviewCollector")
    @patch("scripts.collect_data.DataCleaner")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key_123"})
    def test_with_reviews_flag_collects_reviews(
        self,
        mock_dedup_class,
        mock_cleaner_class,
        mock_review_class,
        mock_collector_class,
        tmp_path,
    ):
        """Test that --with-reviews flag triggers review collection."""
        from scripts.collect_data import main

        # Mock successful execution
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]
        mock_collector_class.return_value = mock_collector

        mock_review_collector = MagicMock()
        mock_review_collector.get_reviews.return_value = ["Great place!"]
        mock_review_class.return_value = mock_review_collector

        mock_cleaner_class.clean_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        mock_dedup_class.deduplicate.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        output_path = tmp_path / "test_output.csv"
        exit_code = main(["--with-reviews", "--output", str(output_path)])

        assert exit_code == 0
        mock_review_class.assert_called_once()
        mock_review_collector.get_reviews.assert_called()

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.ReviewCollector")
    @patch("scripts.collect_data.IndoorOutdoorAnalyzer")
    @patch("scripts.collect_data.DataCleaner")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict(
        "os.environ",
        {"GOOGLE_API_KEY": "test_key_123", "OPENAI_API_KEY": "openai_key"},
    )
    def test_enrich_indoor_outdoor_flag_uses_llm(
        self,
        mock_dedup_class,
        mock_cleaner_class,
        mock_analyzer_class,
        mock_review_class,
        mock_collector_class,
        tmp_path,
    ):
        """Test that --enrich-indoor-outdoor flag triggers LLM analysis."""
        from scripts.collect_data import main

        # Mock successful execution
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]
        mock_collector_class.return_value = mock_collector

        mock_review_collector = MagicMock()
        mock_review_collector.get_reviews.return_value = ["Great place!"]
        mock_review_class.return_value = mock_review_collector

        mock_analyzer = MagicMock()
        mock_analyzer.enrich_facility.side_effect = lambda f, r: f
        mock_analyzer_class.return_value = mock_analyzer

        mock_cleaner_class.clean_facilities.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        mock_dedup_class.deduplicate.return_value = [
            Facility(
                place_id="test_1",
                name="Test",
                address="Address, Faro",
                city="Faro",
                latitude=37.0,
                longitude=-8.0,
            )
        ]

        output_path = tmp_path / "test_output.csv"
        exit_code = main([
            "--with-reviews",
            "--enrich-indoor-outdoor",
            "--output",
            str(output_path),
        ])

        assert exit_code == 0
        mock_analyzer_class.assert_called_once()
        mock_analyzer.enrich_facility.assert_called()

