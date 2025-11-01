"""
Google Trends collector for padel interest by region.

This module provides functionality to collect Google Trends data for padel 
interest across different regions using the pytrends library. It handles 
rate limiting, caching, and graceful error handling.
"""

import logging
import time
from typing import Dict, List

import pandas as pd
from pytrends.request import TrendReq

from src.config import settings
from src.utils.cache import cache_response

# Setup module logger
logger = logging.getLogger(__name__)


class GoogleTrendsCollector:
    """
    Collect Google Trends data for padel interest by region.

    This collector fetches regional interest scores for specified keywords
    and regions using the Google Trends API (via pytrends). It implements
    caching to reduce API calls and graceful error handling to ensure
    robustness.

    Attributes:
        pytrends: PyTrends API client
        rate_limit_delay: Delay between API requests in seconds
    """

    def __init__(self) -> None:
        """
        Initialize the Google Trends collector using pytrends.

        No API key is required for Google Trends. The client is configured
        for Portuguese locale (pt-PT) to better match Algarve region data.
        """
        # Initialize pytrends with Portuguese locale
        self.pytrends = TrendReq(hl='pt-PT', tz=360)
        self.rate_limit_delay = settings.rate_limit_delay
        logger.debug("Initialized GoogleTrendsCollector with Portuguese locale")

    @cache_response(ttl_days=30)
    def get_regional_interest(
        self,
        keyword: str,
        regions: List[str],
        timeframe: str = "today 12-m"
    ) -> Dict[str, float]:
        """
        Get regional interest scores for a keyword.

        Fetches Google Trends interest scores for the specified keyword across
        multiple regions. Scores are normalized to a 0-100 range. Regions with
        no data or errors return 0.0.

        Args:
            keyword: Search term (e.g., "padel")
            regions: List of region names to fetch data for
            timeframe: Time period for trends (default: last 12 months)
                      Examples: "today 12-m", "today 6-m", "today 3-m"

        Returns:
            Dictionary mapping city names to interest scores (0-100).
            Returns 0.0 for cities with no data.

        Example:
            >>> collector = GoogleTrendsCollector()
            >>> scores = collector.get_regional_interest(
            ...     keyword="padel",
            ...     regions=["Faro", "Lagos", "Albufeira"]
            ... )
            >>> print(scores)
            {'Faro': 92.0, 'Lagos': 78.5, 'Albufeira': 85.0}
        """
        logger.info(f"Fetching trends for keyword '{keyword}' across {len(regions)} regions")

        # Initialize result dict with zeros for all regions
        result: Dict[str, float] = {region: 0.0 for region in regions}

        try:
            # Apply rate limiting delay
            time.sleep(self.rate_limit_delay)

            # Build payload for pytrends
            # We search for the keyword in Portugal to get regional breakdown
            self.pytrends.build_payload(
                kw_list=[keyword],
                timeframe=timeframe,
                geo='PT'  # Portugal country code
            )

            # Get interest by region
            interest_df = self.pytrends.interest_by_region(
                resolution='REGION',
                inc_low_vol=True,  # Include low volume regions
                inc_geo_code=False
            )

            # Process the results
            if interest_df is not None and not interest_df.empty:
                # The DataFrame has regions as index and keyword as column
                if keyword in interest_df.columns:
                    # Extract scores for requested regions
                    for region in regions:
                        if region in interest_df.index:
                            score = interest_df.loc[region, keyword]
                            # Convert to float and ensure in 0-100 range
                            result[region] = float(score) if pd.notna(score) else 0.0
                            logger.debug(f"Region '{region}': score = {result[region]}")
                        else:
                            logger.debug(f"No data for region '{region}', using 0.0")
                else:
                    logger.warning(f"Keyword '{keyword}' not found in results")
            else:
                logger.warning(f"Empty results for keyword '{keyword}'")

        except Exception as e:
            # Log error but return zeros for all regions (graceful degradation)
            logger.error(f"Error fetching trends for keyword '{keyword}': {e}")
            # result is already initialized with zeros, so just return it

        logger.info(
            f"Completed trends fetch: {sum(1 for v in result.values() if v > 0)}/{len(regions)} "
            f"regions with data"
        )
        
        return result

