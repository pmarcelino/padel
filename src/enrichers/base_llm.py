"""
Abstract base class for LLM-based enrichers.

This module defines the base interface that all LLM enrichers must implement,
ensuring consistent behavior across different LLM-based analysis tools.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..models.facility import Facility


class BaseLLMEnricher(ABC):
    """
    Abstract base class for LLM-based enrichers.
    
    This class defines the interface that all LLM-based enrichment tools must
    implement. It ensures consistent behavior for analyzing reviews and enriching
    facility data across different LLM providers and analysis types.
    """

    @abstractmethod
    def analyze_reviews(self, reviews: List[str]) -> Optional[str]:
        """
        Analyze reviews and return result.
        
        This method should process a list of review texts and return an analysis
        result. The exact format of the result depends on the specific enricher.
        
        Args:
            reviews: List of review texts to analyze
            
        Returns:
            Analysis result as a string, or None if analysis cannot be performed
            or confidence is too low
        """
        pass

    @abstractmethod
    def enrich_facility(self, facility: Facility, reviews: List[str]) -> Facility:
        """
        Enrich facility with analysis result.
        
        This method takes a facility object and enriches it with information
        extracted from the provided reviews. The method should update the
        facility's last_updated timestamp.
        
        Args:
            facility: Facility object to enrich
            reviews: List of review texts to analyze
            
        Returns:
            Updated facility object with enriched data
        """
        pass

