"""
Core business logic for the Streamlit application.

This module provides pure, testable functions for:
- Loading data from processed CSV files
- Filtering facilities and city data
- Calculating dashboard metrics

These functions are separated from the UI layer to enable comprehensive
unit testing and maintain clean architecture.
"""

from pathlib import Path
from typing import Tuple

import pandas as pd


def load_data(base_path: Path | None = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load facilities and city stats from processed CSV files.

    Args:
        base_path: Optional base path for data directory (used for testing).
                   If None, uses the project root directory.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing:
            - facilities_df: DataFrame with facility information
            - city_stats_df: DataFrame with city-level statistics

    Raises:
        FileNotFoundError: If either CSV file is missing

    Note:
        This function has an optional parameter that defaults to None to be
        compatible with Streamlit's @st.cache_data decorator while remaining testable.
    """
    # Get the project root (app directory is at root level)
    if base_path is None:
        base_path = Path(__file__).parent.parent

    facilities_path = base_path / "data" / "processed" / "facilities.csv"
    city_stats_path = base_path / "data" / "processed" / "city_stats.csv"

    # Check if files exist
    if not facilities_path.exists():
        raise FileNotFoundError(
            f"Facilities data not found at {facilities_path}. "
            "Please run data collection and processing scripts first."
        )

    if not city_stats_path.exists():
        raise FileNotFoundError(
            f"City stats data not found at {city_stats_path}. "
            "Please run data processing script first."
        )

    # Load the CSV files
    facilities_df = pd.read_csv(facilities_path)
    city_stats_df = pd.read_csv(city_stats_path)

    return facilities_df, city_stats_df


def filter_facilities(df: pd.DataFrame, cities: list[str], min_rating: float) -> pd.DataFrame:
    """
    Filter facilities by city list and minimum rating.

    Args:
        df: DataFrame containing facility data
        cities: List of city names to include
        min_rating: Minimum rating threshold (0.0 to 5.0)

    Returns:
        pd.DataFrame: Filtered facilities DataFrame

    Note:
        Returns empty DataFrame if no facilities match the criteria.
    """
    # Handle empty city list
    if not cities:
        return df.iloc[0:0]  # Return empty DataFrame with same schema

    # Filter by city and rating
    filtered = df[(df["city"].isin(cities)) & (df["rating"] >= min_rating)]

    return filtered


def filter_cities(df: pd.DataFrame, cities: list[str]) -> pd.DataFrame:
    """
    Filter city stats by city list.

    Args:
        df: DataFrame containing city statistics
        cities: List of city names to include

    Returns:
        pd.DataFrame: Filtered city stats DataFrame

    Note:
        Returns empty DataFrame if no cities match the criteria.
    """
    # Handle empty city list
    if not cities:
        return df.iloc[0:0]  # Return empty DataFrame with same schema

    # Filter by city
    filtered = df[df["city"].isin(cities)]

    return filtered


def calculate_metrics(facilities_df: pd.DataFrame, cities_df: pd.DataFrame) -> dict:
    """
    Calculate key metrics for dashboard display.

    Args:
        facilities_df: DataFrame containing facility data
        cities_df: DataFrame containing city statistics

    Returns:
        dict: Dictionary containing:
            - total_facilities: Total number of facilities
            - avg_rating: Average rating across all facilities
            - total_reviews: Sum of all review counts
            - top_opportunity_city: City with highest opportunity score

    Note:
        Handles empty DataFrames gracefully by returning sensible defaults.
    """
    metrics = {}

    # Total facilities count
    metrics["total_facilities"] = len(facilities_df)

    # Average rating
    if len(facilities_df) > 0:
        metrics["avg_rating"] = float(facilities_df["rating"].mean())
    else:
        metrics["avg_rating"] = 0.0

    # Total reviews
    if len(facilities_df) > 0:
        metrics["total_reviews"] = int(facilities_df["review_count"].sum())
    else:
        metrics["total_reviews"] = 0

    # Top opportunity city
    if len(cities_df) > 0:
        top_city_idx = cities_df["opportunity_score"].idxmax()
        metrics["top_opportunity_city"] = str(cities_df.loc[top_city_idx, "city"])
    else:
        metrics["top_opportunity_city"] = "N/A"

    return metrics
