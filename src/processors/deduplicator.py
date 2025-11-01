"""
Deduplicator for removing duplicate facilities.

This module provides functionality to remove duplicate facilities from collected data
using both exact place_id matching and fuzzy name+location matching.
"""

import logging
from typing import List

import pandas as pd

from ..models.facility import Facility

logger = logging.getLogger(__name__)


def _completeness_score(facility: Facility) -> int:
    """
    Calculate completeness score for a facility.

    Counts the number of non-null optional fields. Used to determine
    which facility to keep when duplicates are found.

    Args:
        facility: Facility object to score

    Returns:
        Integer score from 0-6 representing number of populated optional fields
    """
    score = 0
    if facility.phone:
        score += 1
    if facility.website:
        score += 1
    if facility.indoor_outdoor:
        score += 1
    if facility.num_courts:
        score += 1
    if facility.postal_code:
        score += 1
    if facility.facility_type:
        score += 1
    return score


class Deduplicator:
    """
    Remove duplicate facilities using exact and fuzzy matching.

    This class provides static methods to deduplicate facility lists based on:
    1. Exact place_id matching
    2. Fuzzy name and location matching (case-insensitive, rounded coordinates)

    When duplicates are found, the facility with the highest completeness score
    (most non-null optional fields) is kept.
    """

    @staticmethod
    def deduplicate(facilities: List[Facility]) -> List[Facility]:
        """
        Remove duplicates based on place_id and fuzzy name+location matching.

        Two-pass algorithm:
        1. Remove facilities with identical place_id (keep most complete)
        2. Remove facilities with same name/city and similar location (keep most complete)

        Args:
            facilities: List of facilities (may contain duplicates)

        Returns:
            List of unique facilities
        """
        initial_count = len(facilities)

        # Handle edge cases
        if not facilities:
            logger.info("No facilities to deduplicate")
            return []

        if len(facilities) == 1:
            logger.info("Single facility, no deduplication needed")
            return facilities

        # Pass 1: Remove exact place_id duplicates
        seen_ids = {}
        for facility in facilities:
            if facility.place_id not in seen_ids:
                seen_ids[facility.place_id] = facility
            else:
                # Keep facility with higher completeness score
                existing = seen_ids[facility.place_id]
                if _completeness_score(facility) > _completeness_score(existing):
                    seen_ids[facility.place_id] = facility

        facilities_after_pass1 = list(seen_ids.values())
        removed_pass1 = initial_count - len(facilities_after_pass1)

        # Pass 2: Fuzzy name + location matching
        if len(facilities_after_pass1) <= 1:
            logger.info(
                f"Deduplicated {initial_count} facilities: "
                f"{len(facilities_after_pass1)} unique, {removed_pass1} removed (place_id)"
            )
            return facilities_after_pass1

        # Convert to DataFrame for efficient grouping
        df = pd.DataFrame([f.to_dict() for f in facilities_after_pass1])

        # Create normalized columns for fuzzy matching
        df["name_lower"] = df["name"].str.lower().str.strip()
        df["lat_round"] = df["latitude"].round(3)
        df["lng_round"] = df["longitude"].round(3)

        # Calculate completeness score for each facility
        df["completeness"] = [
            _completeness_score(facilities_after_pass1[idx])
            for idx in range(len(facilities_after_pass1))
        ]

        # Sort by completeness (descending) before dropping duplicates
        # This ensures we keep the most complete facility
        df = df.sort_values("completeness", ascending=False)

        # Remove fuzzy duplicates
        df_unique = df.drop_duplicates(
            subset=["city", "name_lower", "lat_round", "lng_round"], keep="first"
        )

        # Convert back to Facility objects using original indices
        result = [facilities_after_pass1[idx] for idx in df_unique.index]

        removed_pass2 = len(facilities_after_pass1) - len(result)
        total_removed = initial_count - len(result)

        logger.info(
            f"Deduplicated {initial_count} facilities: "
            f"{len(result)} unique, {total_removed} removed "
            f"({removed_pass1} place_id, {removed_pass2} fuzzy)"
        )

        return result
