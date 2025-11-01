"""
Tests for the Deduplicator class.

This module contains comprehensive tests for facility deduplication,
including exact place_id matching, fuzzy name+location matching,
and completeness score preservation.
"""


import pytest

from src.models.facility import Facility
from src.processors.deduplicator import Deduplicator, _completeness_score

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_facility_minimal():
    """Facility with only required fields (completeness score = 0)."""
    return Facility(
        place_id="test_minimal",
        name="Minimal Padel Club",
        address="Rua Minimal, 1",
        city="Albufeira",
        latitude=37.0885,
        longitude=-8.2475,
    )


@pytest.fixture
def sample_facility_partial():
    """Facility with some optional fields (completeness score = 2)."""
    return Facility(
        place_id="test_partial",
        name="Partial Padel Club",
        address="Rua Partial, 2",
        city="Albufeira",
        latitude=37.0886,
        longitude=-8.2476,
        phone="+351 282 123 456",
        website="https://partial-padel.com",
    )


@pytest.fixture
def sample_facility_complete():
    """Facility with all optional fields (completeness score = 6)."""
    return Facility(
        place_id="test_complete",
        name="Complete Padel Club",
        address="Rua Complete, 3",
        city="Albufeira",
        latitude=37.0887,
        longitude=-8.2477,
        postal_code="8200-001",
        phone="+351 282 123 456",
        website="https://complete-padel.com",
        facility_type="club",
        num_courts=6,
        indoor_outdoor="both",
    )


@pytest.fixture
def duplicate_facilities_exact_place_id():
    """Facilities with exact place_id duplicates."""
    return [
        Facility(
            place_id="dup_1",
            name="Club A",
            address="Rua A, 1",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        ),
        Facility(
            place_id="dup_1",  # Duplicate
            name="Club A",
            address="Rua A, 1",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        ),
        Facility(
            place_id="dup_2",
            name="Club B",
            address="Rua B, 2",
            city="Faro",
            latitude=37.0186,
            longitude=-7.9304,
        ),
        Facility(
            place_id="dup_2",  # Duplicate
            name="Club B",
            address="Rua B, 2",
            city="Faro",
            latitude=37.0186,
            longitude=-7.9304,
        ),
        Facility(
            place_id="unique_1",
            name="Club C",
            address="Rua C, 3",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6742,
        ),
    ]


@pytest.fixture
def duplicate_facilities_with_completeness():
    """Duplicate facilities with different completeness scores."""
    return [
        # First duplicate - minimal fields (score = 0)
        Facility(
            place_id="dup_completeness",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        ),
        # Second duplicate - all fields (score = 6)
        Facility(
            place_id="dup_completeness",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
            postal_code="8200-001",
            phone="+351 282 123 456",
            website="https://padel-club.com",
            facility_type="club",
            num_courts=6,
            indoor_outdoor="both",
        ),
    ]


@pytest.fixture
def fuzzy_duplicate_facilities():
    """Facilities with fuzzy name/location duplicates."""
    return [
        Facility(
            place_id="fuzzy_1",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0881,
            longitude=-8.2475,
        ),
        # Same name/city, slightly different coordinates (within 0.001)
        Facility(
            place_id="fuzzy_2",
            name="padel club",  # Lowercase
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0882,
            longitude=-8.2476,
        ),
    ]


@pytest.fixture
def case_insensitive_duplicates():
    """Facilities with case variations of the same name."""
    return [
        Facility(
            place_id="case_1",
            name="PADEL CLUB",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0881,
            longitude=-8.2475,
        ),
        Facility(
            place_id="case_2",
            name="Padel Club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0881,
            longitude=-8.2475,
        ),
        Facility(
            place_id="case_3",
            name="padel club",
            address="Rua Example, 123",
            city="Albufeira",
            latitude=37.0881,
            longitude=-8.2475,
        ),
    ]


@pytest.fixture
def distinct_facilities_same_city():
    """Distinct facilities in the same city."""
    return [
        Facility(
            place_id="distinct_1",
            name="Padel Club A",
            address="Rua A, 1",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        ),
        Facility(
            place_id="distinct_2",
            name="Padel Club B",
            address="Rua B, 2",
            city="Albufeira",
            latitude=37.0900,
            longitude=-8.2500,
        ),
    ]


@pytest.fixture
def unique_facilities():
    """All unique facilities with no duplicates."""
    return [
        Facility(
            place_id="unique_1",
            name="Club A",
            address="Rua A, 1",
            city="Albufeira",
            latitude=37.0885,
            longitude=-8.2475,
        ),
        Facility(
            place_id="unique_2",
            name="Club B",
            address="Rua B, 2",
            city="Faro",
            latitude=37.0186,
            longitude=-7.9304,
        ),
        Facility(
            place_id="unique_3",
            name="Club C",
            address="Rua C, 3",
            city="Lagos",
            latitude=37.1028,
            longitude=-8.6742,
        ),
    ]


# ============================================================================
# Tests
# ============================================================================


class TestCompletenessScore:
    """Test completeness score calculation."""

    def test_completeness_score_all_fields(self, sample_facility_complete):
        """Test facility with all optional fields has score of 6."""
        score = _completeness_score(sample_facility_complete)
        assert score == 6

    def test_completeness_score_partial_fields(self, sample_facility_partial):
        """Test facility with phone and website has score of 2."""
        score = _completeness_score(sample_facility_partial)
        assert score == 2

    def test_completeness_score_no_optional_fields(self, sample_facility_minimal):
        """Test facility with no optional fields has score of 0."""
        score = _completeness_score(sample_facility_minimal)
        assert score == 0


class TestDeduplicateExactPlaceId:
    """Test exact place_id deduplication."""

    def test_deduplicate_exact_place_id(self, duplicate_facilities_exact_place_id):
        """Test removal of exact place_id duplicates."""
        result = Deduplicator.deduplicate(duplicate_facilities_exact_place_id)

        # Should return 3 unique facilities (2 duplicates removed)
        assert len(result) == 3

        # All place_ids should be unique
        place_ids = [f.place_id for f in result]
        assert len(place_ids) == len(set(place_ids))
        assert set(place_ids) == {"dup_1", "dup_2", "unique_1"}

    def test_keep_most_complete_duplicate(self, duplicate_facilities_with_completeness):
        """Test that the facility with highest completeness is kept."""
        result = Deduplicator.deduplicate(duplicate_facilities_with_completeness)

        # Should return only 1 facility
        assert len(result) == 1

        # Should be the one with all fields filled
        kept_facility = result[0]
        assert kept_facility.postal_code == "8200-001"
        assert kept_facility.phone == "+351 282 123 456"
        assert kept_facility.website == "https://padel-club.com"
        assert kept_facility.facility_type == "club"
        assert kept_facility.num_courts == 6
        assert kept_facility.indoor_outdoor == "both"


class TestDeduplicateFuzzyMatching:
    """Test fuzzy name+location deduplication."""

    def test_deduplicate_fuzzy_name_location(self, fuzzy_duplicate_facilities):
        """Test removal of fuzzy duplicates with similar name and location."""
        result = Deduplicator.deduplicate(fuzzy_duplicate_facilities)

        # Should return only 1 facility
        assert len(result) == 1

    def test_case_insensitive_names(self, case_insensitive_duplicates):
        """Test that name matching is case-insensitive."""
        result = Deduplicator.deduplicate(case_insensitive_duplicates)

        # Should return only 1 facility (all three are duplicates)
        assert len(result) == 1


class TestPreserveDistinctFacilities:
    """Test that legitimate distinct facilities are preserved."""

    def test_preserve_distinct_facilities(self, distinct_facilities_same_city):
        """Test that facilities with different names in same city are kept."""
        result = Deduplicator.deduplicate(distinct_facilities_same_city)

        # Both facilities should be kept
        assert len(result) == 2

        # Verify both are present
        names = {f.name for f in result}
        assert names == {"Padel Club A", "Padel Club B"}


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_list(self):
        """Test that empty list returns empty list."""
        result = Deduplicator.deduplicate([])
        assert result == []

    def test_single_facility(self, sample_facility_minimal):
        """Test that single facility is returned unchanged."""
        result = Deduplicator.deduplicate([sample_facility_minimal])

        assert len(result) == 1
        assert result[0].place_id == sample_facility_minimal.place_id

    def test_no_duplicates(self, unique_facilities):
        """Test that all unique facilities are returned."""
        result = Deduplicator.deduplicate(unique_facilities)

        # All 3 facilities should be returned
        assert len(result) == 3

        # Verify all place_ids are present
        place_ids = {f.place_id for f in result}
        assert place_ids == {"unique_1", "unique_2", "unique_3"}
