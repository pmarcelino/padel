"""
Facility data model.

This module defines the Facility Pydantic model for representing padel facilities
with validation, normalization, and serialization capabilities.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Facility(BaseModel):
    """
    Represents a padel facility with location, ratings, and metadata.

    This model provides validation for all facility data and includes methods
    for serialization to dictionaries for CSV export.
    """

    # Identifiers
    place_id: str = Field(..., description="Google Places ID")
    name: str = Field(..., min_length=1, description="Facility name")

    # Location
    address: str = Field(..., description="Full address")
    city: str = Field(..., description="City name (normalized to Title Case)")
    postal_code: Optional[str] = Field(None, description="Postal code")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

    # Social Metrics
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating (0-5)")
    review_count: int = Field(0, ge=0, description="Number of reviews")
    google_url: Optional[str] = Field(None, description="Google Maps URL")

    # Facility Details (optional)
    facility_type: Optional[str] = Field(None, description="Type: club, sports_center, other")
    num_courts: Optional[int] = Field(None, ge=1, description="Number of courts")
    indoor_outdoor: Optional[str] = Field(
        None, description="Court type: indoor, outdoor, both, or None"
    )
    phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Website URL")

    # Metadata
    collected_at: datetime = Field(default_factory=datetime.now, description="Collection timestamp")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    @field_validator("indoor_outdoor")
    @classmethod
    def validate_indoor_outdoor(cls, value: Optional[str]) -> Optional[str]:
        """
        Validate that indoor_outdoor is one of the allowed values.

        Args:
            value: The indoor_outdoor value to validate

        Returns:
            The validated value

        Raises:
            ValueError: If value is not in allowed values
        """
        if value is None:
            return value

        allowed_values = {"indoor", "outdoor", "both"}
        if value not in allowed_values:
            raise ValueError(
                f"indoor_outdoor must be one of {allowed_values} or None, got '{value}'"
            )

        return value

    @field_validator("city")
    @classmethod
    def normalize_city(cls, value: str) -> str:
        """
        Normalize city name by stripping whitespace and converting to Title Case.

        Args:
            value: The city name to normalize

        Returns:
            The normalized city name
        """
        return value.strip().title()

    def to_dict(self) -> dict:
        """
        Convert the Facility model to a dictionary for CSV export.

        Datetime fields are converted to ISO format strings for compatibility.
        All other fields are preserved in their original types.

        Returns:
            Dictionary representation of the facility with ISO format timestamps
        """
        data = {
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "rating": self.rating,
            "review_count": self.review_count,
            "google_url": self.google_url,
            "facility_type": self.facility_type,
            "num_courts": self.num_courts,
            "indoor_outdoor": self.indoor_outdoor,
            "phone": self.phone,
            "website": self.website,
            "collected_at": self.collected_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
        return data
