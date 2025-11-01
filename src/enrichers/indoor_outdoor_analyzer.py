"""
Indoor/Outdoor Analyzer using LLMs.

This module uses Large Language Models (OpenAI or Anthropic) to analyze facility
reviews and determine if courts are indoor, outdoor, or both. It implements
cost-efficient analysis with confidence thresholds and error handling.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from .base_llm import BaseLLMEnricher
from ..models.facility import Facility
from ..config import settings

logger = logging.getLogger(__name__)

# Constants
CONFIDENCE_THRESHOLD = 0.6
MAX_REVIEWS = 20

# Prompt template for LLM analysis
PROMPT_TEMPLATE = """Analyze the following reviews of a padel facility and determine if the courts are:
- "indoor" (only indoor courts)
- "outdoor" (only outdoor courts)  
- "both" (has both indoor and outdoor courts)
- "unknown" (cannot determine from reviews)

Look for keywords like: indoor, outdoor, covered, open-air, roof, ceiling, weather, rain, sun, etc.

Reviews:
{review_text}

Respond with ONLY a valid JSON object in this exact format:
{{"court_type": "indoor|outdoor|both|unknown", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""


def log_llm_cost(model: str, input_tokens: int, output_tokens: int) -> None:
    """
    Log LLM API usage for cost tracking.
    
    This function calculates and logs the estimated cost of an LLM API call
    based on token usage. Cost estimates are approximate and based on current
    pricing as of the implementation date.
    
    Args:
        model: Model name (e.g., 'gpt-4o-mini', 'claude-3-5-haiku-20241022')
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
    """
    # Cost calculation (approximate, update as needed)
    costs_per_1k = {
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'claude-3-5-haiku-20241022': {'input': 0.00025, 'output': 0.00125}
    }
    
    if model in costs_per_1k:
        cost = (input_tokens / 1000 * costs_per_1k[model]['input'] +
                output_tokens / 1000 * costs_per_1k[model]['output'])
        logger.info(f"LLM call: {model}, {input_tokens} in + {output_tokens} out tokens, ${cost:.6f}")
    else:
        logger.info(f"LLM call: {model}, {input_tokens} in + {output_tokens} out tokens")


class IndoorOutdoorAnalyzer(BaseLLMEnricher):
    """
    Analyze facility reviews to determine if courts are indoor, outdoor, or both.
    
    This analyzer uses LLM providers (OpenAI or Anthropic) to extract structured
    information from review text. It implements cost optimization, confidence
    thresholds, and graceful error handling.
    
    Attributes:
        provider: LLM provider name ('openai' or 'anthropic')
        model: Specific model name to use
        api_key: API key for the provider
        client: Initialized LLM client
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> None:
        """
        Initialize analyzer with LLM provider.
        
        If parameters are not provided, they will be loaded from settings/environment.
        
        Args:
            provider: 'openai' or 'anthropic' (default: from settings)
            model: Model name (e.g., 'gpt-4o-mini') (default: from settings)
            api_key: API key (if None, uses environment variable via settings)
            
        Raises:
            ValueError: If provider is not 'openai' or 'anthropic'
            ImportError: If required provider library is not installed
        """
        # Load defaults from settings if not provided
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        
        # Validate provider
        if self.provider not in ['openai', 'anthropic']:
            raise ValueError(f"Invalid provider: {self.provider}. Must be 'openai' or 'anthropic'")
        
        # Get API key
        if api_key is None:
            if self.provider == 'openai':
                api_key = settings.openai_api_key
            else:
                api_key = settings.anthropic_api_key
        
        self.api_key = api_key
        
        # Initialize client
        if self.provider == 'openai':
            if openai is None:
                raise ImportError("openai package not installed. Install with: pip install openai")
            self.client = openai.OpenAI(api_key=self.api_key)
        else:  # anthropic
            if anthropic is None:
                raise ImportError("anthropic package not installed. Install with: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def analyze_reviews(self, reviews: Optional[List[str]]) -> Optional[str]:
        """
        Analyze reviews to determine indoor/outdoor status.
        
        This method sends reviews to the LLM provider and parses the response
        to determine if the facility has indoor, outdoor, or both types of courts.
        It implements confidence thresholding and only returns results with
        confidence >= 0.6.
        
        Args:
            reviews: List of review texts to analyze
            
        Returns:
            'indoor', 'outdoor', 'both', or None if:
            - Cannot determine from reviews
            - Confidence is below threshold
            - No reviews provided
            - API error occurs
        """
        # Return None if no reviews
        if not reviews or len(reviews) == 0:
            logger.debug("No reviews provided for analysis")
            return None
        
        # Limit to first MAX_REVIEWS reviews
        limited_reviews = reviews[:MAX_REVIEWS]
        
        # Combine reviews into prompt
        review_text = "\n".join(limited_reviews)
        prompt = PROMPT_TEMPLATE.format(review_text=review_text)
        
        try:
            # Call appropriate provider
            if self.provider == 'openai':
                result = self._call_openai(prompt)
            else:  # anthropic
                result = self._call_anthropic(prompt)
            
            return result
            
        except Exception as e:
            # Pattern 1: Data Collection Errors - log but don't crash
            logger.error(f"Error analyzing reviews with {self.provider}: {e}")
            return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """
        Call OpenAI API with the prompt.
        
        Args:
            prompt: Formatted prompt with reviews
            
        Returns:
            Court type or None
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            # Extract response
            content = response.choices[0].message.content
            
            # Log cost
            log_llm_cost(
                self.model,
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            
            # Parse and validate response
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """
        Call Anthropic API with the prompt.
        
        Args:
            prompt: Formatted prompt with reviews
            
        Returns:
            Court type or None
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response
            content = response.content[0].text
            
            # Log cost
            log_llm_cost(
                self.model,
                response.usage.input_tokens,
                response.usage.output_tokens
            )
            
            # Parse and validate response
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
    
    def _parse_response(self, content: str) -> Optional[str]:
        """
        Parse and validate LLM response.
        
        This method parses the JSON response from the LLM and validates that:
        1. JSON is valid
        2. Required fields are present
        3. Confidence meets threshold
        4. Court type is not 'unknown'
        
        Args:
            content: JSON string from LLM
            
        Returns:
            Court type or None if validation fails
        """
        try:
            data = json.loads(content)
            
            # Validate required fields
            if 'court_type' not in data or 'confidence' not in data:
                logger.warning(f"LLM response missing required fields: {data}")
                return None
            
            court_type = data['court_type']
            confidence = data['confidence']
            reasoning = data.get('reasoning', 'No reasoning provided')
            
            # Check if unknown
            if court_type == 'unknown':
                logger.debug(f"LLM returned unknown court type: {reasoning}")
                return None
            
            # Check confidence threshold
            if confidence < CONFIDENCE_THRESHOLD:
                logger.debug(f"Low confidence ({confidence:.2f}) for court type '{court_type}': {reasoning}")
                return None
            
            # Validate court type
            if court_type not in ['indoor', 'outdoor', 'both']:
                logger.warning(f"Invalid court type '{court_type}' from LLM")
                return None
            
            logger.info(f"Determined court type: {court_type} (confidence: {confidence:.2f})")
            return court_type
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def enrich_facility(self, facility: Facility, reviews: List[str]) -> Facility:
        """
        Enrich a facility with indoor/outdoor information.
        
        This method analyzes the provided reviews and updates the facility's
        indoor_outdoor field if it is currently None. If the field is already
        set, the facility is returned unchanged to avoid unnecessary API calls.
        
        Args:
            facility: Facility object to enrich
            reviews: List of review texts to analyze
            
        Returns:
            Updated facility object with indoor_outdoor information and
            updated last_updated timestamp
        """
        # Skip if already set (optimization)
        if facility.indoor_outdoor is not None:
            logger.debug(f"Facility {facility.place_id} already has indoor_outdoor set to '{facility.indoor_outdoor}'")
            return facility
        
        # Analyze reviews
        court_type = self.analyze_reviews(reviews)
        
        # Create updated facility
        if court_type is not None:
            # Update the facility
            facility_dict = facility.model_dump()
            facility_dict['indoor_outdoor'] = court_type
            facility_dict['last_updated'] = datetime.now()
            
            enriched_facility = Facility(**facility_dict)
            logger.info(f"Enriched facility {facility.place_id} with indoor_outdoor='{court_type}'")
            return enriched_facility
        else:
            logger.debug(f"Could not determine indoor/outdoor for facility {facility.place_id}")
            return facility

