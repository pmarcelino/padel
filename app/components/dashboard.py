"""
Dashboard components for visualization of padel facility data.

This module provides interactive Plotly charts for analyzing facility data,
city statistics, and market opportunities across the Algarve region.

Functions:
    create_facilities_bar_chart: Bar chart of facilities per city
    create_opportunity_chart: Bar chart of opportunity scores by city
    create_population_saturation_scatter: Scatter plot of population vs saturation
    create_rating_distribution_pie: Pie chart of rating distribution
    render_overview: Render overview dashboard with basic charts
    render_analysis: Render analysis dashboard with opportunity metrics
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


@st.cache_data
def create_facilities_bar_chart(cities_df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart of facilities per city.

    Args:
        cities_df: City statistics DataFrame with columns:
                   - city: City name
                   - total_facilities: Number of facilities

    Returns:
        Plotly Figure object showing facilities per city, sorted descending

    Note:
        Returns empty figure with "No data" annotation if DataFrame is empty
    """
    # Handle empty DataFrame
    if len(cities_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            title="Facilities per City",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # Sort by total_facilities descending
    sorted_df = cities_df.sort_values("total_facilities", ascending=False).copy()

    # Calculate percentages
    total = sorted_df["total_facilities"].sum()
    sorted_df["percentage"] = (sorted_df["total_facilities"] / total * 100).round(1)

    # Create bar chart
    fig = px.bar(
        sorted_df,
        x="city",
        y="total_facilities",
        title="Facilities per City",
        labels={
            "city": "City",
            "total_facilities": "Number of Facilities",
        },
        color="total_facilities",
        color_continuous_scale="Blues",
    )

    # Customize hover template
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>"
        + "Facilities: %{y}<br>"
        + "Percentage: %{customdata[0]:.1f}%<br>"
        + "<extra></extra>",
        customdata=sorted_df[["percentage"]].values,
    )

    # Update layout
    fig.update_layout(
        showlegend=False,
        xaxis_tickangle=-90,
        height=400,
    )

    return fig


@st.cache_data
def create_opportunity_chart(cities_df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart of opportunity scores by city.

    Color-coded: green (>70), yellow (40-70), red (<40)

    Args:
        cities_df: City statistics DataFrame with columns:
                   - city: City name
                   - opportunity_score: Score from 0-100
                   - population_weight: Population component
                   - saturation_weight: Saturation component
                   - quality_gap_weight: Quality gap component
                   - geographic_gap_weight: Geographic gap component

    Returns:
        Plotly Figure object showing opportunity scores by city, sorted descending

    Note:
        Returns empty figure with "No data" annotation if DataFrame is empty
    """
    # Handle empty DataFrame
    if len(cities_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            title="Opportunity Scores by City",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # Sort by opportunity_score descending
    sorted_df = cities_df.sort_values("opportunity_score", ascending=False).copy()

    # Assign colors based on score ranges
    def get_color(score):
        if score >= 70:
            return "#2ecc71"  # Green
        elif score >= 40:
            return "#f39c12"  # Yellow/Orange
        else:
            return "#e74c3c"  # Red

    sorted_df["color"] = sorted_df["opportunity_score"].apply(get_color)

    # Create horizontal bar chart
    fig = go.Figure(
        data=[
            go.Bar(
                y=sorted_df["city"],
                x=sorted_df["opportunity_score"],
                orientation="h",
                marker=dict(color=sorted_df["color"]),
                hovertemplate="<b>%{y}</b><br>"
                + "Opportunity Score: %{x:.1f}/100<br>"
                + "<br><b>Breakdown:</b><br>"
                + "• Population: %{customdata[0]:.1f}/10<br>"
                + "• Low Saturation: %{customdata[1]:.1f}/10<br>"
                + "• Quality Gap: %{customdata[2]:.1f}/10<br>"
                + "• Geographic Gap: %{customdata[3]:.1f}/10<br>"
                + "<extra></extra>",
                customdata=sorted_df[
                    [
                        "population_weight",
                        "saturation_weight",
                        "quality_gap_weight",
                        "geographic_gap_weight",
                    ]
                ].values,
            )
        ]
    )

    # Update layout
    fig.update_layout(
        title="Opportunity Scores by City",
        xaxis_title="Opportunity Score (0-100)",
        yaxis_title="City",
        showlegend=False,
        height=400,
    )

    return fig


@st.cache_data
def create_population_saturation_scatter(cities_df: pd.DataFrame) -> go.Figure:
    """
    Create scatter plot: population vs facilities per capita.

    Shows saturation levels across different city sizes.

    Args:
        cities_df: City statistics DataFrame with columns:
                   - city: City name
                   - population: City population
                   - facilities_per_capita: Facilities per capita (as decimal)
                   - total_facilities: Total number of facilities
                   - opportunity_score: Score from 0-100

    Returns:
        Plotly Figure object showing population vs saturation scatter plot

    Note:
        - Skips cities with missing population data
        - Point size scaled by total_facilities
        - Point color scaled by opportunity_score
    """
    # Handle empty DataFrame
    if len(cities_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            title="Population vs Saturation",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # Filter out cities with missing population data
    valid_df = cities_df.dropna(subset=["population", "facilities_per_capita"]).copy()

    # Handle case where all cities have missing data
    if len(valid_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No population data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # Convert facilities_per_capita to per 10,000 people for better readability
    valid_df["facilities_per_10k"] = valid_df["facilities_per_capita"] * 10000

    # Create scatter plot
    fig = px.scatter(
        valid_df,
        x="population",
        y="facilities_per_10k",
        size="total_facilities",
        color="opportunity_score",
        hover_name="city",
        labels={
            "population": "Population",
            "facilities_per_10k": "Facilities per 10,000 people",
            "opportunity_score": "Opportunity Score",
        },
        title="Population vs Saturation",
        color_continuous_scale="Viridis",
    )

    # Customize hover template
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>"
        + "Population: %{x:,}<br>"
        + "Facilities: %{customdata[0]}<br>"
        + "Per 10k people: %{y:.2f}<br>"
        + "Opportunity Score: %{customdata[1]:.1f}<br>"
        + "<extra></extra>",
        customdata=valid_df[["total_facilities", "opportunity_score"]].values,
    )

    # Update layout
    fig.update_layout(height=500)

    return fig


@st.cache_data
def create_rating_distribution_pie(facilities_df: pd.DataFrame) -> go.Figure:
    """
    Create pie chart of rating distribution.

    Categories: 5 stars, 4-5 stars, 3-4 stars, <3 stars, No rating

    Args:
        facilities_df: Facilities DataFrame with columns:
                       - rating: Facility rating (0.0 to 5.0, or 0.0 for no rating)

    Returns:
        Plotly Figure object showing rating distribution

    Note:
        Returns empty figure with "No data" annotation if DataFrame is empty
    """
    # Handle empty DataFrame
    if len(facilities_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            title="Rating Distribution",
            showlegend=False,
        )
        return fig

    # Categorize ratings
    def categorize_rating(rating):
        if rating == 0.0 or pd.isna(rating):
            return "No Rating"
        elif rating == 5.0:
            return "5★"
        elif rating >= 4.0:
            return "4-5★"
        elif rating >= 3.0:
            return "3-4★"
        else:
            return "<3★"

    facilities_df = facilities_df.copy()
    facilities_df["rating_category"] = facilities_df["rating"].apply(categorize_rating)

    # Count facilities in each category
    category_counts = facilities_df["rating_category"].value_counts()

    # Define category order and colors (colorblind-safe palette)
    category_order = ["5★", "4-5★", "3-4★", "<3★", "No Rating"]
    colors = {
        "5★": "#2ecc71",  # Green
        "4-5★": "#3498db",  # Blue
        "3-4★": "#f39c12",  # Orange
        "<3★": "#e74c3c",  # Red
        "No Rating": "#95a5a6",  # Gray
    }

    # Filter to only categories present in data and maintain order
    present_categories = [cat for cat in category_order if cat in category_counts.index]
    values = [category_counts[cat] for cat in present_categories]
    category_colors = [colors[cat] for cat in present_categories]

    # Create pie chart
    fig = go.Figure(
        data=[
            go.Pie(
                labels=present_categories,
                values=values,
                marker=dict(colors=category_colors),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>"
                + "Facilities: %{value}<br>"
                + "Percentage: %{percent}<br>"
                + "<extra></extra>",
            )
        ]
    )

    # Update layout
    fig.update_layout(
        title="Rating Distribution",
        height=400,
    )

    return fig


def render_overview(facilities_df: pd.DataFrame, cities_df: pd.DataFrame) -> None:
    """
    Render overview dashboard with basic charts.

    Displays facilities bar chart and rating distribution pie chart in a 2-column layout.

    Args:
        facilities_df: Filtered facilities DataFrame
        cities_df: Filtered city statistics DataFrame

    Note:
        Uses Streamlit components for rendering. Charts are displayed side-by-side.
    """
    st.subheader("📊 Facilities Overview")

    # 2-column layout
    col1, col2 = st.columns(2)

    with col1:
        fig = create_facilities_bar_chart(cities_df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = create_rating_distribution_pie(facilities_df)
        st.plotly_chart(fig, use_container_width=True)


def render_analysis(cities_df: pd.DataFrame) -> None:
    """
    Render analysis dashboard with opportunity metrics.

    Displays opportunity scores bar chart and population saturation scatter plot.

    Args:
        cities_df: Filtered city statistics DataFrame

    Note:
        Uses Streamlit components for rendering. Charts are displayed full-width.
    """
    st.subheader("📈 Market Opportunity Analysis")

    # Opportunity chart (full width)
    fig = create_opportunity_chart(cities_df)
    st.plotly_chart(fig, use_container_width=True)

    # Scatter plot (full width)
    st.subheader("Population vs Saturation")
    fig = create_population_saturation_scatter(cities_df)
    st.plotly_chart(fig, use_container_width=True)

