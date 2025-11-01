"""
Integration tests for data collection CLI.

Tests the full pipeline execution with realistic data flow and mocked API calls.
These tests verify that all components work together correctly and data flows
through the entire pipeline as expected.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.models.facility import Facility


@pytest.fixture
def realistic_facilities():
    """Create realistic facility data for integration testing."""
    return [
        Facility(
            place_id="ChIJ_albufeira_1",
            name="Padel Club Albufeira",
            address="Rua Test 1, 8200-100 Albufeira",
            city="Albufeira",
            postal_code="8200-100",
            latitude=37.0885,
            longitude=-8.2475,
            rating=4.5,
            review_count=150,
            google_url="https://maps.google.com/?cid=123",
            facility_type="club",
            phone="+351 282 123 456",
            website="https://padelalbufeira.pt",
        ),
        Facility(
            place_id="ChIJ_faro_1",
            name="Faro Padel Center",
            address="Av. Test 5, 8000-100 Faro",
            city="Faro",
            postal_code="8000-100",
            latitude=37.0194,
            longitude=-7.9322,
            rating=4.2,
            review_count=80,
            google_url="https://maps.google.com/?cid=456",
            facility_type="sports_center",
        ),
        Facility(
            place_id="ChIJ_lagos_1",
            name="Lagos Padel",
            address="Rua Lagos 10, 8600-100 Lagos",
            city="Lagos",
            postal_code="8600-100",
            latitude=37.1028,
            longitude=-8.6731,
            rating=4.7,
            review_count=200,
            facility_type="club",
        ),
    ]


@pytest.fixture
def realistic_reviews():
    """Create realistic review data."""
    return {
        "ChIJ_albufeira_1": [
            "Great indoor facilities with excellent lighting",
            "The covered courts are perfect for all weather",
            "Modern indoor padel center with good amenities",
        ],
        "ChIJ_faro_1": [
            "Nice outdoor courts",
            "Open-air facility with good maintenance",
        ],
        "ChIJ_lagos_1": [
            "Mix of indoor and outdoor courts available",
            "Both covered and open courts to choose from",
        ],
    }


class TestFullPipelineIntegration:
    """Integration tests for complete pipeline execution."""

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_api_key_12345"})
    def test_basic_pipeline_no_enrichment(
        self,
        mock_dedup_class,
        mock_collector_class,
        realistic_facilities,
        tmp_path,
    ):
        """Test full pipeline without optional enrichment features."""
        from scripts.collect_data import main

        # Setup mocks
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = realistic_facilities
        mock_collector_class.return_value = mock_collector

        # Don't mock DataCleaner - let it run normally
        mock_dedup_class.deduplicate.return_value = realistic_facilities

        # Run pipeline
        output_path = tmp_path / "facilities.csv"
        exit_code = main(["--output", str(output_path)])

        # Verify success
        assert exit_code == 0
        assert output_path.exists()

        # Verify CSV output
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert set(df["city"]) == {"Albufeira", "Faro", "Lagos"}
        assert "place_id" in df.columns
        assert "name" in df.columns
        assert "rating" in df.columns

        # Verify all pipeline stages were called
        mock_collector.search_padel_facilities.assert_called_once()
        mock_dedup_class.deduplicate.assert_called_once()

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.ReviewCollector")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_api_key_12345"})
    def test_pipeline_with_reviews(
        self,
        mock_dedup_class,
        mock_review_class,
        mock_collector_class,
        realistic_facilities,
        realistic_reviews,
        tmp_path,
    ):
        """Test full pipeline with review collection."""
        from scripts.collect_data import main

        # Setup facility collector
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = realistic_facilities
        mock_collector_class.return_value = mock_collector

        # Setup review collector
        mock_review_collector = MagicMock()

        def get_reviews_side_effect(place_id):
            return realistic_reviews.get(place_id, [])

        mock_review_collector.get_reviews.side_effect = get_reviews_side_effect
        mock_review_class.return_value = mock_review_collector

        # Don't mock DataCleaner - let it run normally
        mock_dedup_class.deduplicate.return_value = realistic_facilities

        # Run pipeline with reviews
        output_path = tmp_path / "facilities_with_reviews.csv"
        exit_code = main(["--with-reviews", "--output", str(output_path)])

        # Verify success
        assert exit_code == 0
        assert output_path.exists()

        # Verify reviews were collected
        assert mock_review_collector.get_reviews.call_count == len(realistic_facilities)

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.ReviewCollector")
    @patch("scripts.collect_data.IndoorOutdoorAnalyzer")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict(
        "os.environ",
        {"GOOGLE_API_KEY": "test_api_key", "OPENAI_API_KEY": "test_openai_key"},
    )
    def test_pipeline_with_llm_enrichment(
        self,
        mock_dedup_class,
        mock_analyzer_class,
        mock_review_class,
        mock_collector_class,
        realistic_facilities,
        realistic_reviews,
        tmp_path,
    ):
        """Test full pipeline with LLM enrichment."""
        from scripts.collect_data import main

        # Setup facility collector
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = realistic_facilities
        mock_collector_class.return_value = mock_collector

        # Setup review collector
        mock_review_collector = MagicMock()

        def get_reviews_side_effect(place_id):
            return realistic_reviews.get(place_id, [])

        mock_review_collector.get_reviews.side_effect = get_reviews_side_effect
        mock_review_class.return_value = mock_review_collector

        # Setup LLM analyzer
        mock_analyzer = MagicMock()

        def enrich_facility_side_effect(facility, reviews):
            # Simulate LLM analysis based on reviews
            facility_dict = facility.model_dump()
            if "indoor" in " ".join(reviews).lower():
                facility_dict["indoor_outdoor"] = "indoor"
            elif "outdoor" in " ".join(reviews).lower():
                facility_dict["indoor_outdoor"] = "outdoor"
            elif "both" in " ".join(reviews).lower():
                facility_dict["indoor_outdoor"] = "both"
            return Facility(**facility_dict)

        mock_analyzer.enrich_facility.side_effect = enrich_facility_side_effect
        mock_analyzer_class.return_value = mock_analyzer

        # Don't mock DataCleaner - let it run normally
        mock_dedup_class.deduplicate.side_effect = lambda x: x

        # Run pipeline with full enrichment
        output_path = tmp_path / "facilities_enriched.csv"
        exit_code = main([
            "--with-reviews",
            "--enrich-indoor-outdoor",
            "--output",
            str(output_path),
        ])

        # Verify success
        assert exit_code == 0
        assert output_path.exists()

        # Verify LLM was called for each facility
        assert mock_analyzer.enrich_facility.call_count == len(realistic_facilities)

        # Verify enrichment actually occurred
        df = pd.read_csv(output_path)
        # At least some facilities should have indoor_outdoor set
        assert df["indoor_outdoor"].notna().any()

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_api_key"})
    def test_pipeline_handles_cleaning_and_deduplication(
        self,
        mock_dedup_class,
        mock_collector_class,
        realistic_facilities,
        tmp_path,
    ):
        """Test that cleaning and deduplication are applied correctly."""
        from scripts.collect_data import main

        # Setup collector with duplicates
        facilities_with_duplicates = realistic_facilities + [realistic_facilities[0]]
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = facilities_with_duplicates
        mock_collector_class.return_value = mock_collector

        # Deduplicator removes duplicates
        mock_dedup_class.deduplicate.return_value = realistic_facilities

        # Run pipeline
        output_path = tmp_path / "facilities_deduplicated.csv"
        exit_code = main(["--output", str(output_path)])

        # Verify success
        assert exit_code == 0

        # Verify deduplication was called
        mock_dedup_class.deduplicate.assert_called_once()

        # Verify final output has no duplicates
        df = pd.read_csv(output_path)
        assert len(df) == 3  # Original 3 unique facilities


class TestPipelineErrorRecovery:
    """Test error recovery and graceful degradation."""

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.ReviewCollector")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_api_key"})
    def test_pipeline_continues_after_review_errors(
        self,
        mock_dedup_class,
        mock_review_class,
        mock_collector_class,
        realistic_facilities,
        tmp_path,
    ):
        """Test that pipeline continues if individual review collection fails."""
        from scripts.collect_data import main

        # Setup collector
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = realistic_facilities
        mock_collector_class.return_value = mock_collector

        # Setup review collector that fails for some facilities
        mock_review_collector = MagicMock()

        def failing_reviews(place_id):
            if "albufeira" in place_id.lower():
                raise Exception("API rate limit exceeded")
            return ["Review text"]

        mock_review_collector.get_reviews.side_effect = failing_reviews
        mock_review_class.return_value = mock_review_collector

        # Don't mock DataCleaner - let it run normally
        mock_dedup_class.deduplicate.return_value = realistic_facilities

        # Run pipeline
        output_path = tmp_path / "facilities.csv"
        exit_code = main(["--with-reviews", "--output", str(output_path)])

        # Should still succeed despite individual failures
        assert exit_code == 0
        assert output_path.exists()

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_api_key"})
    def test_pipeline_fails_gracefully_on_no_facilities(
        self, mock_collector_class, tmp_path
    ):
        """Test that pipeline handles case where no facilities are found."""
        from scripts.collect_data import main

        # Setup collector that returns no facilities
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = []
        mock_collector_class.return_value = mock_collector

        # Run pipeline
        output_path = tmp_path / "facilities.csv"
        exit_code = main(["--output", str(output_path)])

        # Should fail with appropriate exit code
        assert exit_code == 2  # EXIT_COLLECTION_FAILED


class TestCSVOutputFormat:
    """Test CSV output format and data integrity."""

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_api_key"})
    def test_csv_contains_all_required_columns(
        self,
        mock_dedup_class,
        mock_collector_class,
        realistic_facilities,
        tmp_path,
    ):
        """Test that CSV output contains all required columns."""
        from scripts.collect_data import main

        # Setup mocks
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = realistic_facilities
        mock_collector_class.return_value = mock_collector

        # Don't mock DataCleaner - let it run normally
        mock_dedup_class.deduplicate.return_value = realistic_facilities

        # Run pipeline
        output_path = tmp_path / "facilities.csv"
        main(["--output", str(output_path)])

        # Verify CSV structure
        df = pd.read_csv(output_path)

        # Check required columns
        required_columns = [
            "place_id",
            "name",
            "address",
            "city",
            "latitude",
            "longitude",
            "rating",
            "review_count",
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

        # Verify data types
        assert df["latitude"].dtype == "float64"
        assert df["longitude"].dtype == "float64"
        assert df["review_count"].dtype == "int64"

    @patch("scripts.collect_data.GooglePlacesCollector")
    @patch("scripts.collect_data.Deduplicator")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test_api_key"})
    def test_csv_data_matches_input_facilities(
        self,
        mock_dedup_class,
        mock_collector_class,
        realistic_facilities,
        tmp_path,
    ):
        """Test that CSV data accurately represents input facilities."""
        from scripts.collect_data import main

        # Setup mocks
        mock_collector = MagicMock()
        mock_collector.search_padel_facilities.return_value = realistic_facilities
        mock_collector_class.return_value = mock_collector

        # Don't mock DataCleaner - let it run normally
        mock_dedup_class.deduplicate.return_value = realistic_facilities

        # Run pipeline
        output_path = tmp_path / "facilities.csv"
        main(["--output", str(output_path)])

        # Verify data integrity
        df = pd.read_csv(output_path)

        # Check first facility data
        first_row = df.iloc[0]
        first_facility = realistic_facilities[0]

        assert first_row["place_id"] == first_facility.place_id
        assert first_row["name"] == first_facility.name
        assert first_row["city"] == first_facility.city
        assert first_row["latitude"] == pytest.approx(first_facility.latitude)
        assert first_row["longitude"] == pytest.approx(first_facility.longitude)

