"""
Data models package.

This package contains Pydantic models for data validation and serialization.
"""

from .city import CityStats
from .facility import Facility

__all__ = ["Facility", "CityStats"]
