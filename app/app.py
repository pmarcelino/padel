"""
Main Streamlit application for Algarve Padel Market Research.

This application provides an interactive web interface for exploring padel
facility data and opportunity scores across the Algarve region.

Launch with: streamlit run app/app.py
"""

import sys
from pathlib import Path

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

from core import calculate_metrics, filter_cities, filter_facilities, load_data

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Algarve Padel Market Research",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# Data Loading
# ============================================================================


@st.cache_data
def load_cached_data():
    """
    Load and cache data from CSV files.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Facilities and city stats DataFrames

    Note:
        Uses Streamlit's caching to avoid reloading data on every interaction.
    """
    return load_data()


# ============================================================================
# Main App
# ============================================================================


def main():
    """Main application entry point."""

    # App title and description
    st.title("🎾 Algarve Padel Market Research")
    st.markdown(
        "Explore padel facility data and identify market opportunities across the Algarve region."
    )

    # Load data with error handling
    try:
        facilities_df, cities_df = load_cached_data()
    except FileNotFoundError as e:
        st.error("📁 Data not found. Please run data collection first.")
        st.markdown("Run the following commands to collect and process data:")
        st.code("python scripts/collect_data.py", language="bash")
        st.code("python scripts/process_data.py", language="bash")
        st.info(f"Error details: {str(e)}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.stop()

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Get all unique cities
    all_cities = sorted(cities_df["city"].unique().tolist())

    # City multi-select
    selected_cities = st.sidebar.multiselect(
        "Select Cities",
        options=all_cities,
        default=all_cities,
        help="Choose one or more cities to analyze",
    )

    # Rating slider
    min_rating = st.sidebar.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.5,
        help="Filter facilities by minimum rating",
    )

    # Handle edge case: no cities selected
    if not selected_cities:
        st.warning("⚠️ Please select at least one city to view data.")
        st.stop()

    # Apply filters
    filtered_facilities = filter_facilities(facilities_df, selected_cities, min_rating)
    filtered_cities = filter_cities(cities_df, selected_cities)

    # Handle edge case: no facilities after filtering
    if len(filtered_facilities) == 0:
        st.warning(f"⚠️ No facilities found with rating >= {min_rating} in selected cities.")
        st.info("Try adjusting your filters to see more results.")

    # ========================================================================
    # Export Section
    # ========================================================================
    
    st.sidebar.markdown("---")
    st.sidebar.header("📥 Export Data")
    
    from src.utils.exporters import DataExporter
    exporter = DataExporter()
    
    # Show data summary
    st.sidebar.write(f"Facilities: {len(filtered_facilities)} rows")
    st.sidebar.write(f"Cities: {len(filtered_cities)} rows")
    
    # Facilities export button
    if len(filtered_facilities) > 0:
        facilities_csv = exporter.export_to_csv(filtered_facilities, prefix="facilities")
        with open(facilities_csv, 'rb') as f:
            st.sidebar.download_button(
                label="Download Facilities CSV",
                data=f,
                file_name=facilities_csv.name,
                mime="text/csv",
                help="Download filtered facilities data"
            )
    else:
        st.sidebar.warning("No facilities data to export")
    
    # City stats export button
    if len(filtered_cities) > 0:
        cities_csv = exporter.export_to_csv(filtered_cities, prefix="city_stats")
        with open(cities_csv, 'rb') as f:
            st.sidebar.download_button(
                label="Download City Stats CSV",
                data=f,
                file_name=cities_csv.name,
                mime="text/csv",
                help="Download city statistics"
            )
    else:
        st.sidebar.warning("No city data to export")

    # Calculate metrics
    metrics = calculate_metrics(filtered_facilities, filtered_cities)

    # Display key metrics in 4 columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Facilities", value=metrics["total_facilities"])

    with col2:
        avg_rating = metrics["avg_rating"]
        if avg_rating > 0:
            st.metric(label="Average Rating", value=f"{avg_rating:.1f} ⭐")
        else:
            st.metric(label="Average Rating", value="N/A")

    with col3:
        st.metric(label="Total Reviews", value=f"{metrics['total_reviews']:,}")

    with col4:
        st.metric(label="Top Opportunity", value=metrics["top_opportunity_city"])

    st.divider()

    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🗺️ Map", "📈 Analysis"])

    with tab1:
        render_overview(filtered_facilities, filtered_cities)

    with tab2:
        render_map(filtered_facilities, filtered_cities)

    with tab3:
        render_analysis(filtered_cities)


# ============================================================================
# Tab Rendering Functions (Placeholders)
# ============================================================================


def render_overview(facilities_df: pd.DataFrame, cities_df: pd.DataFrame):
    """
    Render overview tab with interactive charts.

    Args:
        facilities_df: Filtered facilities DataFrame
        cities_df: Filtered city stats DataFrame

    Note:
        Implemented in Story 6.3 (Dashboard & Charts).
    """
    from app.components.dashboard import render_overview as dashboard_render_overview

    dashboard_render_overview(facilities_df, cities_df)


def render_map(facilities_df: pd.DataFrame, cities_df: pd.DataFrame):
    """
    Render interactive map tab with facility and city markers.

    Args:
        facilities_df: Filtered facilities DataFrame
        cities_df: Filtered city stats DataFrame

    Displays:
        - Interactive Folium map with facility markers (color-coded by rating)
        - City center markers with opportunity scores
        - Heatmap layer for facility density
        - Layer control for toggling heatmap
    """
    from streamlit_folium import st_folium
    from app.components.map_view import create_map

    st.subheader("🗺️ Interactive Map")
    
    # Debug info
    st.write(f"📍 Facilities to display: {len(facilities_df)}")
    st.write(f"🏙️ Cities to display: {len(cities_df)}")
    
    # Check if we have data
    if len(facilities_df) == 0 and len(cities_df) == 0:
        st.warning("No data available to display on the map. Please adjust your filters.")
        return
    
    # Create and display the map
    try:
        import streamlit.components.v1 as components
        
        map_obj = create_map(facilities_df, cities_df)
        
        # Render map HTML directly using Streamlit components
        # This is more reliable than st_folium
        map_html = map_obj._repr_html_()
        components.html(map_html, height=650, scrolling=False)
        
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    # Add legend/instructions
    st.markdown("""
    **Map Legend:**
    - 🟢 **Green markers**: High-rated facilities (≥4.5⭐)
    - 🔵 **Blue markers**: Good facilities (≥4.0⭐)
    - 🟠 **Orange markers**: Average facilities (≥3.5⭐)
    - 🔴 **Red markers**: Lower-rated facilities (<3.5⭐)
    - ⚫ **Gray markers**: No rating available
    - 🟣 **Purple markers**: City centers with opportunity scores
    
    **Tip:** Click on markers for details. Use the layer control (top-right) to toggle the heatmap.
    """)


def render_analysis(cities_df: pd.DataFrame):
    """
    Render analysis tab with opportunity metrics.

    Args:
        cities_df: Filtered city stats DataFrame

    Note:
        Implemented in Story 6.3 (Dashboard & Charts).
    """
    from app.components.dashboard import render_analysis as dashboard_render_analysis

    dashboard_render_analysis(cities_df)


# ============================================================================
# App Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
