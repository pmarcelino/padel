"""
Data cleaning and validation module.

This module provides the DataCleaner class for validating and cleaning
facility data, including coordinate validation, city filtering, and
DataFrame conversion for downstream analysis.
"""

import logging
from typing import List

import pandas as pd

from ..models.facility import Facility

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Clean and validate facility data.

    This class provides static methods for cleaning facility data by:
    - Filtering facilities to Algarve geographic bounds
    - Removing facilities without city information
    - Converting facilities to pandas DataFrame format

    All methods are stateless and can be called without instantiation.
    """

    # Algarve geographic bounds
    ALGARVE_LAT_MIN = 36.96
    ALGARVE_LAT_MAX = 37.42
    ALGARVE_LON_MIN = -9.0
    ALGARVE_LON_MAX = -7.4

    @staticmethod
    def _is_within_algarve_bounds(facility: Facility) -> bool:
        """
        Check if facility coordinates are within Algarve geographic bounds.

        Args:
            facility: Facility to validate

        Returns:
            True if coordinates are within bounds, False otherwise
        """
        lat_valid = DataCleaner.ALGARVE_LAT_MIN <= facility.latitude <= DataCleaner.ALGARVE_LAT_MAX
        lon_valid = DataCleaner.ALGARVE_LON_MIN <= facility.longitude <= DataCleaner.ALGARVE_LON_MAX
        return lat_valid and lon_valid

    @staticmethod
    def clean_facilities(facilities: List[Facility]) -> List[Facility]:
        """
        Clean and validate facility data.

        This method filters facilities based on:
        - Geographic bounds (Algarve region)
        - City presence (must not be empty)

        City name normalization and rating validation are handled automatically
        by the Facility Pydantic model validators.

        Args:
            facilities: List of raw Facility objects

        Returns:
            List of cleaned Facility objects that pass all validation checks

        Note:
            Removed facilities are logged for transparency. The operation is
            idempotent and can be run multiple times safely.
        """
        if not facilities:
            return []

        initial_count = len(facilities)
        cleaned = []

        # Track removal reasons for logging
        removed_invalid_coords = 0
        removed_no_city = 0

        for facility in facilities:
            # Check if city is empty (Pydantic normalizes, but can still be empty)
            if not facility.city or facility.city.strip() == "":
                removed_no_city += 1
                continue

            # Validate coordinates are within Algarve bounds
            if not DataCleaner._is_within_algarve_bounds(facility):
                removed_invalid_coords += 1
                continue

            # All checks passed
            cleaned.append(facility)

        final_count = len(cleaned)
        removed = initial_count - final_count

        logger.info(f"Cleaned {initial_count} facilities: {final_count} kept, {removed} removed")

        if removed > 0:
            logger.debug(
                f"Removed: {removed_invalid_coords} invalid coordinates, "
                f"{removed_no_city} missing city"
            )

        return cleaned

    @staticmethod
    def to_dataframe(facilities: List[Facility]) -> pd.DataFrame:
        """
        Convert facilities to pandas DataFrame for analysis.

        Uses each Facility's to_dict() method to ensure consistent serialization
        with datetime fields converted to ISO format strings.

        Args:
            facilities: List of Facility objects

        Returns:
            DataFrame with all facility data, or empty DataFrame if input is empty

        Example:
            >>> facilities = [facility1, facility2]
            >>> df = DataCleaner.to_dataframe(facilities)
            >>> print(df.columns)
            Index(['place_id', 'name', 'address', 'city', ...])
        """
        if not facilities:
            return pd.DataFrame()

        # Convert each facility to dictionary using its to_dict() method
        data = [facility.to_dict() for facility in facilities]

        return pd.DataFrame(data)
