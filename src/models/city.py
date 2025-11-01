"""
CityStats data model.

This module defines the CityStats Pydantic model for representing aggregated
city-level statistics and opportunity scores.
"""

from typing import Optional

from pydantic import BaseModel, Field


class CityStats(BaseModel):
    """
    Represents aggregated statistics for a city's padel facilities.

    This model includes facility counts, ratings, geographic data, population
    information, and calculated opportunity scores for market analysis.
    """

    # Basic Info
    city: str = Field(..., description="City name")

    # Facility Counts
    total_facilities: int = Field(..., ge=0, description="Total number of facilities")

    # Rating Statistics
    avg_rating: Optional[float] = Field(
        None, ge=0, le=5, description="Average rating across all facilities"
    )
    median_rating: Optional[float] = Field(
        None, ge=0, le=5, description="Median rating across all facilities"
    )
    total_reviews: int = Field(0, ge=0, description="Total review count across all facilities")

    # Geographic
    center_lat: float = Field(..., description="City center latitude")
    center_lng: float = Field(..., description="City center longitude")

    # Population
    population: Optional[int] = Field(None, ge=0, description="City population")

    # Calculated Metrics
    facilities_per_capita: Optional[float] = Field(
        None, description="Facilities per 10,000 residents"
    )
    avg_distance_to_nearest: Optional[float] = Field(
        None, description="Average distance to nearest facility (km)"
    )

    # Opportunity Scoring
    opportunity_score: float = Field(
        0.0, ge=0, le=100, description="Final opportunity score (0-100)"
    )
    population_weight: float = Field(0.0, ge=0, le=1, description="Population component (0-1)")
    saturation_weight: float = Field(0.0, ge=0, le=1, description="Saturation component (0-1)")
    quality_gap_weight: float = Field(0.0, ge=0, le=1, description="Quality gap component (0-1)")
    geographic_gap_weight: float = Field(
        0.0, ge=0, le=1, description="Geographic gap component (0-1)"
    )

    def calculate_opportunity_score(self) -> None:
        """
        Calculate weighted opportunity score using component weights.

        The formula applies different weights to each component:
        - Population: 20%
        - Saturation: 30%
        - Quality Gap: 20%
        - Geographic Gap: 30%

        The final score is scaled to 0-100 range.

        Updates the opportunity_score field in place.
        """
        self.opportunity_score = (
            self.population_weight * 0.2
            + self.saturation_weight * 0.3
            + self.quality_gap_weight * 0.2
            + self.geographic_gap_weight * 0.3
        ) * 100
