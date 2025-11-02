"""
Unit tests for dashboard components (app.components.dashboard module).

Tests the dashboard chart creation functions using TDD approach:
- Facilities bar chart
- Opportunity scores bar chart
- Population saturation scatter plot
- Rating distribution pie chart
- Dashboard rendering functions
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_facilities_df():
    """Create sample facilities DataFrame for testing."""
    return pd.DataFrame(
        {
            "place_id": ["place_1", "place_2", "place_3", "place_4", "place_5"],
            "name": [
                "Padel Center Albufeira",
                "Faro Tennis Club",
                "Lagos Sports",
                "Albufeira Pro",
                "Portimao Club",
            ],
            "city": ["Albufeira", "Faro", "Lagos", "Albufeira", "Portimao"],
            "rating": [4.5, 4.2, 3.8, 5.0, 0.0],  # Last one has no rating
            "review_count": [100, 80, 45, 120, 0],
        }
    )


@pytest.fixture
def sample_cities_df():
    """Create sample city stats DataFrame for testing."""
    return pd.DataFrame(
        {
            "city": ["Albufeira", "Faro", "Lagos", "Portimao"],
            "total_facilities": [2, 1, 1, 1],
            "avg_rating": [4.75, 4.2, 3.8, 0.0],
            "median_rating": [4.75, 4.2, 3.8, 0.0],
            "total_reviews": [220, 80, 45, 0],
            "center_lat": [37.0888, 37.0194, 37.1028, 37.1879],
            "center_lng": [-8.2478, -7.9322, -8.6729, -8.5373],
            "population": [30000.0, 60000.0, 25000.0, 45000.0],
            "facilities_per_capita": [0.0667, 0.0167, 0.0400, 0.0222],
            "avg_distance_to_nearest": [2.5, 5.0, 0.0, 3.2],
            "opportunity_score": [75.5, 85.2, 65.0, 55.3],
            "population_weight": [6.0, 8.5, 5.0, 7.2],
            "saturation_weight": [8.0, 9.2, 7.5, 6.8],
            "quality_gap_weight": [6.5, 6.1, 8.0, 5.5],
            "geographic_gap_weight": [7.5, 7.8, 6.0, 6.3],
        }
    )


@pytest.fixture
def empty_facilities_df():
    """Create empty facilities DataFrame with correct schema."""
    return pd.DataFrame(
        columns=["place_id", "name", "city", "rating", "review_count"]
    )


@pytest.fixture
def empty_cities_df():
    """Create empty city stats DataFrame with correct schema."""
    return pd.DataFrame(
        columns=[
            "city",
            "total_facilities",
            "avg_rating",
            "median_rating",
            "total_reviews",
            "center_lat",
            "center_lng",
            "population",
            "facilities_per_capita",
            "avg_distance_to_nearest",
            "opportunity_score",
            "population_weight",
            "saturation_weight",
            "quality_gap_weight",
            "geographic_gap_weight",
        ]
    )


@pytest.fixture
def single_city_df():
    """Create city stats DataFrame with a single city."""
    return pd.DataFrame(
        {
            "city": ["Faro"],
            "total_facilities": [5],
            "avg_rating": [4.2],
            "median_rating": [4.2],
            "total_reviews": [250],
            "center_lat": [37.0194],
            "center_lng": [-7.9322],
            "population": [60000.0],
            "facilities_per_capita": [0.0833],
            "avg_distance_to_nearest": [5.0],
            "opportunity_score": [85.2],
            "population_weight": [8.5],
            "saturation_weight": [9.2],
            "quality_gap_weight": [6.1],
            "geographic_gap_weight": [7.8],
        }
    )


@pytest.fixture
def cities_with_missing_population():
    """Create city stats DataFrame with missing population data."""
    return pd.DataFrame(
        {
            "city": ["Albufeira", "Faro", "Lagos"],
            "total_facilities": [2, 1, 1],
            "avg_rating": [4.75, 4.2, 3.8],
            "median_rating": [4.75, 4.2, 3.8],
            "total_reviews": [220, 80, 45],
            "center_lat": [37.0888, 37.0194, 37.1028],
            "center_lng": [-8.2478, -7.9322, -8.6729],
            "population": [30000.0, np.nan, 25000.0],  # Faro has missing population
            "facilities_per_capita": [0.0667, np.nan, 0.0400],
            "avg_distance_to_nearest": [2.5, 5.0, 0.0],
            "opportunity_score": [75.5, 85.2, 65.0],
            "population_weight": [6.0, 8.5, 5.0],
            "saturation_weight": [8.0, 9.2, 7.5],
            "quality_gap_weight": [6.5, 6.1, 8.0],
            "geographic_gap_weight": [7.5, 7.8, 6.0],
        }
    )


@pytest.fixture
def facilities_all_no_rating():
    """Create facilities DataFrame where all facilities have no rating."""
    return pd.DataFrame(
        {
            "place_id": ["place_1", "place_2", "place_3"],
            "name": ["Facility 1", "Facility 2", "Facility 3"],
            "city": ["Albufeira", "Faro", "Lagos"],
            "rating": [0.0, 0.0, 0.0],
            "review_count": [0, 0, 0],
        }
    )


# ============================================================================
# Test Facilities Bar Chart
# ============================================================================


class TestFacilitiesBarChart:
    """Test facilities per city bar chart creation."""

    def test_facilities_bar_chart_creation(self, sample_cities_df):
        """Test basic bar chart creation returns a valid Plotly figure."""
        from app.components.dashboard import create_facilities_bar_chart

        fig = create_facilities_bar_chart(sample_cities_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_facilities_bar_chart_sorted(self, sample_cities_df):
        """Test that cities are sorted by facility count in descending order."""
        from app.components.dashboard import create_facilities_bar_chart

        fig = create_facilities_bar_chart(sample_cities_df)

        # Get the x-axis data (cities) from the figure
        cities_in_chart = list(fig.data[0].x)
        facilities_in_chart = list(fig.data[0].y)

        # Verify descending order
        assert facilities_in_chart == sorted(facilities_in_chart, reverse=True)
        # First city should be Albufeira (2 facilities)
        assert cities_in_chart[0] == "Albufeira"

    def test_facilities_bar_chart_empty_data(self, empty_cities_df):
        """Test bar chart handles empty DataFrame gracefully."""
        from app.components.dashboard import create_facilities_bar_chart

        fig = create_facilities_bar_chart(empty_cities_df)

        assert isinstance(fig, go.Figure)
        # Should have annotation indicating no data
        assert len(fig.layout.annotations) > 0
        assert "no data" in fig.layout.annotations[0].text.lower()

    def test_facilities_bar_chart_hover_data(self, sample_cities_df):
        """Test that hover tooltips contain city name and count."""
        from app.components.dashboard import create_facilities_bar_chart

        fig = create_facilities_bar_chart(sample_cities_df)

        # Verify hover template is set (contains customdata or hovertemplate)
        assert fig.data[0].hovertemplate is not None or fig.data[0].customdata is not None


# ============================================================================
# Test Opportunity Scores Bar Chart
# ============================================================================


class TestOpportunityChart:
    """Test opportunity scores bar chart creation."""

    def test_opportunity_chart_creation(self, sample_cities_df):
        """Test basic opportunity chart creation returns a valid Plotly figure."""
        from app.components.dashboard import create_opportunity_chart

        fig = create_opportunity_chart(sample_cities_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_opportunity_chart_colors(self, sample_cities_df):
        """Test color coding based on opportunity scores."""
        from app.components.dashboard import create_opportunity_chart

        fig = create_opportunity_chart(sample_cities_df)

        # Verify that marker colors are set
        assert fig.data[0].marker is not None
        assert fig.data[0].marker.color is not None

    def test_opportunity_chart_sorted(self, sample_cities_df):
        """Test that cities are sorted by opportunity score in descending order."""
        from app.components.dashboard import create_opportunity_chart

        fig = create_opportunity_chart(sample_cities_df)

        # Get the y-axis data (scores) from the figure
        scores_in_chart = list(fig.data[0].x)  # Assuming horizontal bar chart

        # Verify descending order
        assert scores_in_chart == sorted(scores_in_chart, reverse=True)

    def test_opportunity_chart_empty_data(self, empty_cities_df):
        """Test opportunity chart handles empty DataFrame gracefully."""
        from app.components.dashboard import create_opportunity_chart

        fig = create_opportunity_chart(empty_cities_df)

        assert isinstance(fig, go.Figure)
        # Should have annotation indicating no data
        assert len(fig.layout.annotations) > 0
        assert "no data" in fig.layout.annotations[0].text.lower()


# ============================================================================
# Test Population Saturation Scatter Plot
# ============================================================================


class TestPopulationScatter:
    """Test population vs saturation scatter plot creation."""

    def test_population_scatter_creation(self, sample_cities_df):
        """Test basic scatter plot creation returns a valid Plotly figure."""
        from app.components.dashboard import create_population_saturation_scatter

        fig = create_population_saturation_scatter(sample_cities_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_population_scatter_point_sizes(self, sample_cities_df):
        """Test that point sizes are mapped to total facilities."""
        from app.components.dashboard import create_population_saturation_scatter

        fig = create_population_saturation_scatter(sample_cities_df)

        # Verify marker sizes are set
        assert fig.data[0].marker is not None
        assert fig.data[0].marker.size is not None

    def test_population_scatter_missing_population(self, cities_with_missing_population):
        """Test scatter plot handles missing population data."""
        from app.components.dashboard import create_population_saturation_scatter

        fig = create_population_saturation_scatter(cities_with_missing_population)

        assert isinstance(fig, go.Figure)
        # Should only plot cities with valid population data (2 out of 3)
        assert len(fig.data[0].x) == 2

    def test_population_scatter_color_by_score(self, sample_cities_df):
        """Test that points are colored by opportunity score."""
        from app.components.dashboard import create_population_saturation_scatter

        fig = create_population_saturation_scatter(sample_cities_df)

        # Verify marker colors are set
        assert fig.data[0].marker is not None
        assert fig.data[0].marker.color is not None


# ============================================================================
# Test Rating Distribution Pie Chart
# ============================================================================


class TestRatingPieChart:
    """Test rating distribution pie chart creation."""

    def test_rating_pie_creation(self, sample_facilities_df):
        """Test basic pie chart creation returns a valid Plotly figure."""
        from app.components.dashboard import create_rating_distribution_pie

        fig = create_rating_distribution_pie(sample_facilities_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_rating_pie_categories(self, sample_facilities_df):
        """Test that ratings are categorized into correct segments."""
        from app.components.dashboard import create_rating_distribution_pie

        fig = create_rating_distribution_pie(sample_facilities_df)

        # Get labels from the pie chart
        labels = list(fig.data[0].labels)

        # Should have categories (exact categories depend on data)
        assert len(labels) > 0
        # Verify some expected categories exist
        # Categories: 5★, 4-5★, 3-4★, <3★, No rating

    def test_rating_pie_empty_data(self, empty_facilities_df):
        """Test pie chart handles empty DataFrame gracefully."""
        from app.components.dashboard import create_rating_distribution_pie

        fig = create_rating_distribution_pie(empty_facilities_df)

        assert isinstance(fig, go.Figure)
        # Should have annotation indicating no data
        assert len(fig.layout.annotations) > 0
        assert "no data" in fig.layout.annotations[0].text.lower()

    def test_rating_pie_percentages(self, sample_facilities_df):
        """Test that pie chart shows percentages."""
        from app.components.dashboard import create_rating_distribution_pie

        fig = create_rating_distribution_pie(sample_facilities_df)

        # Verify textinfo is set to show percentages
        assert "percent" in fig.data[0].textinfo or fig.data[0].texttemplate is not None

    def test_rating_pie_all_no_rating(self, facilities_all_no_rating):
        """Test pie chart when all facilities have no rating."""
        from app.components.dashboard import create_rating_distribution_pie

        fig = create_rating_distribution_pie(facilities_all_no_rating)

        assert isinstance(fig, go.Figure)
        # Should show "No rating" category with 100%
        labels = list(fig.data[0].labels)
        assert "No rating" in labels or "No Rating" in labels


# ============================================================================
# Test Render Functions
# ============================================================================


class TestRenderFunctions:
    """Test dashboard rendering functions."""

    def test_render_overview_no_errors(
        self, sample_facilities_df, sample_cities_df, monkeypatch
    ):
        """Test render_overview executes without errors."""
        import streamlit as st

        from app.components.dashboard import render_overview

        # Mock streamlit functions
        calls = []

        def mock_subheader(text):
            calls.append(("subheader", text))

        def mock_columns(n):
            class MockColumn:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return [MockColumn() for _ in range(n)]

        def mock_plotly_chart(fig, **kwargs):
            calls.append(("plotly_chart", fig))

        monkeypatch.setattr(st, "subheader", mock_subheader)
        monkeypatch.setattr(st, "columns", mock_columns)
        monkeypatch.setattr(st, "plotly_chart", mock_plotly_chart)

        # Should not raise any exceptions
        render_overview(sample_facilities_df, sample_cities_df)

        # Verify functions were called
        assert len(calls) > 0

    def test_render_analysis_no_errors(self, sample_cities_df, monkeypatch):
        """Test render_analysis executes without errors."""
        import streamlit as st

        from app.components.dashboard import render_analysis

        # Mock streamlit functions
        calls = []

        def mock_subheader(text):
            calls.append(("subheader", text))

        def mock_plotly_chart(fig, **kwargs):
            calls.append(("plotly_chart", fig))

        monkeypatch.setattr(st, "subheader", mock_subheader)
        monkeypatch.setattr(st, "plotly_chart", mock_plotly_chart)

        # Should not raise any exceptions
        render_analysis(sample_cities_df)

        # Verify functions were called
        assert len(calls) > 0

