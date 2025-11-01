"""
Review collector for fetching Google reviews.

This module provides functionality to fetch reviews for padel facilities from
the Google Places API. It handles rate limiting, exponential backoff for HTTP 429
errors, and graceful error handling to ensure robust data collection.
"""

import logging
import time
from typing import List, Optional

import googlemaps
from googlemaps.exceptions import ApiError

from src.config import settings

# Setup module logger
logger = logging.getLogger(__name__)


class ReviewCollector:
    """
    Collect Google reviews for facilities.
    
    This collector fetches review texts from the Google Places API for a given
    place ID. It implements rate limiting, exponential backoff for rate limit
    errors, and comprehensive error handling to ensure reliable data collection.
    
    Attributes:
        api_key: Google Places API key
        client: Google Maps API client
        rate_limit_delay: Delay in seconds between API requests
    
    Example:
        >>> collector = ReviewCollector(api_key="YOUR_API_KEY")
        >>> reviews = collector.get_reviews(place_id="ChIJ123abc", max_reviews=20)
        >>> print(f"Fetched {len(reviews)} reviews")
    """
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize the review collector.
        
        Args:
            api_key: Google Places API key for authentication
        """
        self.api_key = api_key
        self.client = googlemaps.Client(key=api_key)
        self.rate_limit_delay = settings.rate_limit_delay
    
    def get_reviews(self, place_id: str, max_reviews: int = 20) -> List[str]:
        """
        Fetch reviews for a place.
        
        Retrieves review texts from Google Places API for the specified place ID.
        Implements rate limiting and comprehensive error handling. All errors are
        caught and logged, returning an empty list on failure to ensure the calling
        code continues processing other facilities.
        
        Args:
            place_id: Google Place ID for the facility
            max_reviews: Maximum number of reviews to return (default: 20)
            
        Returns:
            List of review text strings. Returns empty list if:
            - No reviews are available
            - API call fails
            - Rate limit exceeded after max retries
            
        Example:
            >>> reviews = collector.get_reviews("ChIJ123abc")
            >>> for review in reviews:
            ...     print(review)
        """
        try:
            # Fetch reviews with retry logic for rate limiting
            result = self._fetch_with_retry(place_id)
            
            if result is None:
                return []
            
            # Extract reviews from response
            reviews = result.get('result', {}).get('reviews', [])
            
            # Extract text content and filter empty strings
            review_texts = []
            for review in reviews:
                text = review.get('text', '').strip()
                if text:  # Filter out empty or whitespace-only texts
                    review_texts.append(text)
            
            # Limit to max_reviews
            review_texts = review_texts[:max_reviews]
            
            # Apply rate limiting delay after successful API call
            time.sleep(self.rate_limit_delay)
            
            return review_texts
            
        except Exception as e:
            # Log error but don't raise - return empty list to continue processing
            logger.warning(
                f"Error fetching reviews for place_id {place_id}: {e}"
            )
            return []
    
    def _fetch_with_retry(self, place_id: str) -> Optional[dict]:
        """
        Fetch place details with exponential backoff for rate limit errors.
        
        Implements retry logic with exponential backoff specifically for HTTP 429
        (rate limit) errors. Other errors are propagated to the caller.
        
        Retry strategy:
        - Max 3 attempts
        - Exponential backoff delays: 1s, 2s, 4s (2^attempt seconds)
        - Only retries on RESOURCE_EXHAUSTED or 429 errors
        - Other errors are propagated immediately
        
        Args:
            place_id: Google Place ID to fetch details for
            
        Returns:
            API response dictionary if successful, None if max retries exceeded
            
        Raises:
            ApiError: For non-rate-limit API errors
            Exception: For other unexpected errors
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Call Place Details API requesting only reviews field
                result = self.client.place(
                    place_id=place_id,
                    fields=['reviews']
                )
                return result  # type: ignore[no-any-return]
                
            except ApiError as e:
                error_message = str(e)
                
                # Check if this is a rate limit error
                is_rate_limit = (
                    "RESOURCE_EXHAUSTED" in error_message or
                    "429" in error_message
                )
                
                if is_rate_limit:
                    if attempt < max_retries - 1:
                        # Calculate exponential backoff delay
                        wait_time = 2 ** attempt  # 1s, 2s, 4s
                        logger.warning(
                            f"Rate limit hit for place_id {place_id}, "
                            f"attempt {attempt + 1}/{max_retries}, "
                            f"waiting {wait_time}s before retry"
                        )
                        time.sleep(wait_time)
                    else:
                        # Max retries exceeded
                        logger.error(
                            f"Max retries exceeded for place_id {place_id} "
                            f"after {max_retries} attempts"
                        )
                        return None
                else:
                    # Not a rate limit error, propagate it
                    raise
        
        # Should not reach here, but return None as fallback
        return None

