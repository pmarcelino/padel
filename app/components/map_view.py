"""
Interactive map component for visualizing padel facilities and city opportunity scores.

This module provides Folium-based map visualization with:
- Facility markers color-coded by rating
- City center markers showing opportunity scores
- Heatmap layer for facility density
- Interactive popups with detailed information
- Comprehensive null value handling
"""

import folium
from folium import plugins
import pandas as pd


def _get_marker_color(rating):
    """
    Determine marker color based on facility rating.

    Args:
        rating: Facility rating (float or None/NaN)

    Returns:
        str: Color code ('green', 'blue', 'orange', 'red', or 'gray')

    Color scheme:
        - Green: Rating >= 4.5 (excellent)
        - Blue: Rating >= 4.0 (good)
        - Orange: Rating >= 3.5 (average)
        - Red: Rating < 3.5 (poor)
        - Gray: No rating available
    """
    if pd.isna(rating):
        return "gray"
    elif rating >= 4.5:
        return "green"
    elif rating >= 4.0:
        return "blue"
    elif rating >= 3.5:
        return "orange"
    else:
        return "red"


def _create_facility_popup(facility):
    """
    Generate HTML popup content for a facility marker.

    Args:
        facility: pandas Series containing facility data

    Returns:
        str: HTML string for popup content

    Handles null values:
        - rating: Displays "N/A" if null
        - google_url: Omits link if null
    """
    name = facility["name"]
    city = facility["city"]
    address = facility["address"]
    review_count = facility["review_count"]
    
    # Handle null rating
    if pd.isna(facility["rating"]):
        rating_display = "N/A"
    else:
        rating_display = f"{facility['rating']:.1f}⭐"
    
    # Build base HTML
    html = f"""
    <div style="width: 200px">
        <h4>{name}</h4>
        <p><b>City:</b> {city}</p>
        <p><b>Rating:</b> {rating_display} ({review_count} reviews)</p>
        <p><b>Address:</b> {address}</p>
    """
    
    # Add Google Maps link only if google_url is present
    if pd.notna(facility.get("google_url")):
        html += f'    <a href="{facility["google_url"]}" target="_blank">View on Google Maps</a>\n'
    
    html += "    </div>"
    
    return html


def _create_city_popup(city):
    """
    Generate HTML popup content for a city marker.

    Args:
        city: pandas Series containing city data

    Returns:
        str: HTML string for popup content

    Handles null values:
        - avg_rating: Displays "N/A" if null
        - population: Displays "Unknown" if null
    """
    city_name = city["city"]
    opportunity_score = city["opportunity_score"]
    total_facilities = city["total_facilities"]
    
    # Handle null avg_rating
    if pd.isna(city["avg_rating"]):
        avg_rating_display = "N/A"
    else:
        avg_rating_display = f"{city['avg_rating']:.2f}⭐"
    
    # Handle null population
    if pd.isna(city.get("population")):
        population_display = "Unknown"
    else:
        population_display = f"{int(city['population']):,}"
    
    html = f"""
    <div style="width: 200px">
        <h4>{city_name}</h4>
        <p><b>Opportunity Score:</b> {opportunity_score:.1f}/100</p>
        <p><b>Facilities:</b> {total_facilities}</p>
        <p><b>Avg Rating:</b> {avg_rating_display}</p>
        <p><b>Population:</b> {population_display}</p>
    </div>
    """
    
    return html


def create_map(facilities_df: pd.DataFrame, cities_df: pd.DataFrame) -> folium.Map:
    """
    Create an interactive Folium map with facility and city markers.

    Args:
        facilities_df: DataFrame with facility data (columns: place_id, name, city,
                      address, latitude, longitude, rating, review_count, google_url)
        cities_df: DataFrame with city stats (columns: city, center_lat, center_lng,
                  opportunity_score, total_facilities, avg_rating, population)

    Returns:
        folium.Map: Configured map object ready for rendering in Streamlit

    Features:
        - Facility markers color-coded by rating (with separate toggle layers)
        - City center markers with opportunity scores (toggleable)
        - Heatmap layer showing facility density
        - Layer control for toggling all marker groups
        - Handles null/missing values gracefully

    Map Configuration:
        - Center: Algarve region (37.1°N, -8.0°W)
        - Zoom: 10 (regional view)
        - Tiles: OpenStreetMap
    """
    # Create base map centered on Algarve region
    algarve_center = [37.1, -8.0]
    m = folium.Map(
        location=algarve_center,
        zoom_start=10,
        tiles="OpenStreetMap",
    )
    
    # Create feature groups for different marker types
    facility_groups = {
        "green": folium.FeatureGroup(name="🟢 Green Facilities (≥4.5⭐)", show=True),
        "blue": folium.FeatureGroup(name="🔵 Blue Facilities (≥4.0⭐)", show=True),
        "orange": folium.FeatureGroup(name="🟠 Orange Facilities (≥3.5⭐)", show=True),
        "red": folium.FeatureGroup(name="🔴 Red Facilities (<3.5⭐)", show=True),
        "gray": folium.FeatureGroup(name="⚫ Gray Facilities (No Rating)", show=True),
    }
    
    city_group = folium.FeatureGroup(name="🟣 City Centers", show=True)
    
    # Add facility markers to their respective groups
    for _, facility in facilities_df.iterrows():
        # Determine marker color based on rating
        color = _get_marker_color(facility["rating"])
        
        # Create popup HTML
        popup_html = _create_facility_popup(facility)
        
        # Add CircleMarker to the appropriate group
        folium.CircleMarker(
            location=[facility["latitude"], facility["longitude"]],
            radius=8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=facility["name"],
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
        ).add_to(facility_groups[color])
    
    # Add city center markers to city group
    for _, city in cities_df.iterrows():
        # Create popup HTML
        popup_html = _create_city_popup(city)
        
        # Create tooltip with city name and score
        tooltip_text = f"{city['city']}: {city['opportunity_score']:.0f} score"
        
        # Add marker to city group
        folium.Marker(
            location=[city["center_lat"], city["center_lng"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=tooltip_text,
            icon=folium.Icon(color="purple", icon="info-sign"),
        ).add_to(city_group)
    
    # Add all feature groups to the map
    for group in facility_groups.values():
        group.add_to(m)
    if len(cities_df) > 0:
        city_group.add_to(m)
    
    # Add heatmap layer for facility density (only if facilities exist)
    if len(facilities_df) > 0:
        heat_data = [
            [row["latitude"], row["longitude"]]
            for _, row in facilities_df.iterrows()
        ]
        
        heat_map = plugins.HeatMap(
            heat_data,
            radius=15,
            blur=25,
            name="🔥 Density Heatmap",
            show=True,
        )
        heat_map.add_to(m)
    
    # Add layer control to toggle groups
    folium.LayerControl(collapsed=False).add_to(m)
    
    return m

