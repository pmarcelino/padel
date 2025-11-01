# Technical Design Document: Algarve Padel Field Market Research Tool

## 1. System Overview

A Python-based data collection and analysis tool with a Streamlit frontend for visualizing padel field market research in Algarve, Portugal.

**Architecture Style**: Modular pipeline architecture with clear separation between data collection, processing, analysis, and visualization layers.

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│  (Interactive Map, Dashboard, Filters, Export)              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Analysis Layer                             │
│  - Opportunity Scoring                                       │
│  - City-level Aggregations                                   │
│  - Statistical Calculations                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Data Processing Layer                       │
│  - Data cleaning and validation                              │
│  - Geocoding and address normalization                       │
│  - Deduplication                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                Data Collection Layer                         │
│  - Google Places API Client                                  │
│  - Google Trends Client (optional)                           │
│  - Rate limiting and caching                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Data Storage                               │
│  - CSV files (facilities.csv, cities.csv)                   │
│  - Cache directory (API responses)                           │
└─────────────────────────────────────────────────────────────┘
```

## 3. Technology Stack

### Core:
- **Python 3.10+**
- **Streamlit**: Web interface
- **Pandas**: Data manipulation
- **Requests**: HTTP client for APIs

### Data Collection:
- **googlemaps**: Python client for Google Maps APIs
- **pytrends**: Google Trends API wrapper
- **requests-cache**: API response caching

### Visualization:
- **Folium**: Interactive maps
- **Plotly**: Charts and graphs
- **streamlit-folium**: Folium integration in Streamlit

### Utilities:
- **python-dotenv**: Environment variable management
- **pydantic**: Data validation
- **geopy**: Distance calculations

### Development:
- **pytest**: Testing framework
- **pytest-cov**: Code coverage
- **black**: Code formatting
- **mypy**: Type checking

## 4. Project Structure

```
padel-research/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── pyproject.toml
│
├── docs/
│   ├── prd.md
│   ├── technical-design.md
│   └── api-setup.md
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # Configuration and constants
│   │
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base collector
│   │   ├── google_places.py       # Google Places API client
│   │   ├── google_trends.py       # Google Trends client
│   │   └── review_collector.py    # Collect Google reviews
│   │
│   ├── enrichers/
│   │   ├── __init__.py
│   │   ├── base_llm.py            # Abstract LLM enricher
│   │   └── indoor_outdoor_analyzer.py  # Analyze reviews for indoor/outdoor
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── cleaner.py             # Data cleaning
│   │   ├── geocoder.py            # Geocoding utilities
│   │   └── deduplicator.py        # Remove duplicates
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── aggregator.py          # City-level aggregations
│   │   ├── scorer.py              # Opportunity scoring
│   │   └── distance.py            # Geographic calculations
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── facility.py            # Facility data model
│   │   └── city.py                # City data model
│   │
│   └── utils/
│       ├── __init__.py
│       ├── cache.py               # Caching utilities
│       ├── validators.py          # Data validators
│       └── exporters.py           # CSV/Excel export
│
├── app/
│   ├── app.py                     # Main Streamlit app
│   ├── components/
│   │   ├── __init__.py
│   │   ├── map_view.py            # Map component
│   │   ├── dashboard.py           # Metrics dashboard
│   │   └── filters.py             # Filter sidebar
│   └── pages/
│       ├── 1_🗺️_Map.py
│       ├── 2_📊_Analysis.py
│       └── 3_⚙️_Settings.py
│
├── data/
│   ├── raw/                       # Raw collected data
│   ├── processed/                 # Cleaned data
│   ├── cache/                     # API response cache
│   └── exports/                   # User exports
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_collectors/
│   ├── test_processors/
│   ├── test_analyzers/
│   └── test_models/
│
└── scripts/
    ├── collect_data.py            # CLI data collection
    ├── process_data.py            # CLI data processing
    └── setup_env.py               # Environment setup
```

## 5. Data Models

### 5.1 Facility Model

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class Facility(BaseModel):
    """Represents a padel facility."""
    
    # Identifiers
    place_id: str = Field(..., description="Google Places ID")
    name: str = Field(..., min_length=1)
    
    # Location
    address: str
    city: str
    postal_code: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
    # Social Metrics
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: int = Field(0, ge=0)
    google_url: Optional[str] = None
    
    # Facility Details (optional)
    facility_type: Optional[str] = None  # "club", "sports_center", "other"
    num_courts: Optional[int] = Field(None, ge=1)
    indoor_outdoor: Optional[str] = Field(
        None, 
        description="Court type: 'indoor', 'outdoor', 'both', or None if unknown"
    )
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Metadata
    collected_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    @validator('indoor_outdoor')
    def validate_indoor_outdoor(cls, v):
        """Validate indoor/outdoor field."""
        if v is not None and v not in ['indoor', 'outdoor', 'both']:
            raise ValueError("indoor_outdoor must be 'indoor', 'outdoor', 'both', or None")
        return v
    
    @validator('city')
    def normalize_city(cls, v):
        """Normalize city names."""
        return v.strip().title()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export."""
        return {
            'place_id': self.place_id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'postal_code': self.postal_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'rating': self.rating,
            'review_count': self.review_count,
            'google_url': self.google_url,
            'facility_type': self.facility_type,
            'num_courts': self.num_courts,
            'indoor_outdoor': self.indoor_outdoor,
            'phone': self.phone,
            'website': self.website,
            'collected_at': self.collected_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
```

### 5.2 City Statistics Model

```python
from pydantic import BaseModel, Field
from typing import List

class CityStats(BaseModel):
    """Aggregated statistics for a city."""
    
    city: str
    
    # Facility counts
    total_facilities: int = Field(ge=0)
    
    # Rating statistics
    avg_rating: Optional[float] = Field(None, ge=0, le=5)
    median_rating: Optional[float] = Field(None, ge=0, le=5)
    total_reviews: int = Field(0, ge=0)
    
    # Geographic
    center_lat: float
    center_lng: float
    
    # Population (if available)
    population: Optional[int] = Field(None, ge=0)
    
    # Calculated metrics
    facilities_per_capita: Optional[float] = None
    avg_distance_to_nearest: Optional[float] = None  # km
    
    # Opportunity scoring
    opportunity_score: float = Field(0.0, ge=0, le=100)
    population_weight: float = Field(0.0, ge=0, le=1)
    saturation_weight: float = Field(0.0, ge=0, le=1)
    quality_gap_weight: float = Field(0.0, ge=0, le=1)
    geographic_gap_weight: float = Field(0.0, ge=0, le=1)
    
    def calculate_opportunity_score(self):
        """Calculate weighted opportunity score."""
        self.opportunity_score = (
            self.population_weight * 0.2 +
            self.saturation_weight * 0.3 +
            self.quality_gap_weight * 0.2 +
            self.geographic_gap_weight * 0.3
        ) * 100
```

## 6. Data Collection Implementation

### 6.1 Google Places API Integration

```python
# src/collectors/google_places.py

import googlemaps
from typing import List, Dict, Any
from ..models.facility import Facility
from ..utils.cache import cache_response
import time

class GooglePlacesCollector:
    """Collects padel facility data from Google Places API."""
    
    def __init__(self, api_key: str, cache_enabled: bool = True):
        self.client = googlemaps.Client(key=api_key)
        self.cache_enabled = cache_enabled
        self.rate_limit_delay = 0.2  # seconds between requests
        
    def search_padel_facilities(self, region: str = "Algarve, Portugal") -> List[Facility]:
        """
        Search for padel facilities in a region.
        
        Args:
            region: Geographic region to search
            
        Returns:
            List of Facility objects
        """
        facilities = []
        
        # Search queries to cover different facility types
        search_queries = [
            f"padel {region}",
            f"padel court {region}",
            f"padel club {region}",
            f"centro de padel {region}",
        ]
        
        seen_place_ids = set()
        
        for query in search_queries:
            results = self._text_search(query)
            
            for place_data in results:
                place_id = place_data.get('place_id')
                
                # Skip duplicates
                if place_id in seen_place_ids:
                    continue
                    
                seen_place_ids.add(place_id)
                
                # Get detailed information
                details = self._get_place_details(place_id)
                
                # Convert to Facility object
                facility = self._parse_facility(details)
                if facility:
                    facilities.append(facility)
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
        
        return facilities
    
    @cache_response(ttl_days=30)
    def _text_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform text search with caching."""
        all_results = []
        next_page_token = None
        
        while True:
            response = self.client.places(
                query=query,
                page_token=next_page_token
            )
            
            all_results.extend(response.get('results', []))
            next_page_token = response.get('next_page_token')
            
            if not next_page_token:
                break
                
            time.sleep(2)  # Required delay for next page token
        
        return all_results
    
    @cache_response(ttl_days=7)
    def _get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed place information."""
        return self.client.place(
            place_id=place_id,
            fields=[
                'place_id', 'name', 'formatted_address',
                'geometry', 'rating', 'user_ratings_total',
                'url', 'formatted_phone_number', 'website',
                'types'
            ]
        )['result']
    
    def _parse_facility(self, place_data: Dict[str, Any]) -> Optional[Facility]:
        """Parse Google Places data into Facility object."""
        try:
            # Extract city from address components
            city = self._extract_city(place_data)
            
            if not city:
                return None
            
            location = place_data['geometry']['location']
            
            return Facility(
                place_id=place_data['place_id'],
                name=place_data['name'],
                address=place_data.get('formatted_address', ''),
                city=city,
                latitude=location['lat'],
                longitude=location['lng'],
                rating=place_data.get('rating'),
                review_count=place_data.get('user_ratings_total', 0),
                google_url=place_data.get('url'),
                phone=place_data.get('formatted_phone_number'),
                website=place_data.get('website'),
                facility_type=self._determine_facility_type(place_data.get('types', []))
            )
        except Exception as e:
            print(f"Error parsing facility: {e}")
            return None
    
    def _extract_city(self, place_data: Dict[str, Any]) -> Optional[str]:
        """Extract city name from place data."""
        # Try to extract from formatted address
        address = place_data.get('formatted_address', '')
        
        # List of Algarve cities
        algarve_cities = [
            'Albufeira', 'Aljezur', 'Castro Marim', 'Faro', 'Lagoa',
            'Lagos', 'Loulé', 'Monchique', 'Olhão', 'Portimão',
            'São Brás de Alportel', 'Silves', 'Tavira', 'Vila do Bispo',
            'Vila Real de Santo António'
        ]
        
        for city in algarve_cities:
            if city.lower() in address.lower():
                return city
        
        return None
    
    def _determine_facility_type(self, types: List[str]) -> str:
        """Determine facility type from Google types."""
        if 'gym' in types or 'health' in types:
            return 'sports_center'
        elif 'point_of_interest' in types:
            return 'club'
        return 'other'
```

### 6.2 Caching Strategy

```python
# src/utils/cache.py

import pickle
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_response(ttl_days: int = 30):
    """
    Decorator to cache function responses to disk.
    
    Args:
        ttl_days: Time-to-live in days
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name and arguments
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            cache_file = CACHE_DIR / f"{cache_key}.pkl"
            
            # Check if cached and not expired
            if cache_file.exists():
                cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                
                if cache_age < timedelta(days=ttl_days):
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            return result
        
        return wrapper
    return decorator

def _generate_cache_key(*args) -> str:
    """Generate MD5 hash from arguments."""
    key_string = str(args).encode('utf-8')
    return hashlib.md5(key_string).hexdigest()
```

### 6.3 LLM-Based Indoor/Outdoor Detection

```python
# src/enrichers/indoor_outdoor_analyzer.py

from typing import Optional, List, Dict, Any
from openai import OpenAI
from anthropic import Anthropic
from ..models.facility import Facility
import json

class IndoorOutdoorAnalyzer:
    """
    Analyze facility reviews to determine if courts are indoor, outdoor, or both.
    
    Uses LLM to extract structured information from review text.
    """
    
    def __init__(
        self, 
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None
    ):
        """
        Initialize analyzer.
        
        Args:
            provider: 'openai' or 'anthropic'
            model: Model name (e.g., 'gpt-4o-mini', 'claude-3-5-haiku-20241022')
            api_key: API key (if None, uses environment variable)
        """
        self.provider = provider
        self.model = model
        
        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif provider == "anthropic":
            self.client = Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def analyze_reviews(self, reviews: List[str]) -> Optional[str]:
        """
        Analyze reviews to determine indoor/outdoor status.
        
        Args:
            reviews: List of review texts
            
        Returns:
            'indoor', 'outdoor', 'both', or None if cannot determine
        """
        if not reviews:
            return None
        
        # Combine reviews (limit to avoid token limits)
        combined_text = "\n\n".join(reviews[:20])
        
        prompt = self._build_prompt(combined_text)
        
        try:
            if self.provider == "openai":
                result = self._analyze_with_openai(prompt)
            else:
                result = self._analyze_with_anthropic(prompt)
            
            return result
        except Exception as e:
            print(f"Error analyzing reviews: {e}")
            return None
    
    def _build_prompt(self, review_text: str) -> str:
        """Build analysis prompt."""
        return f"""Analyze the following reviews of a padel facility and determine if the courts are:
- "indoor" (only indoor courts)
- "outdoor" (only outdoor courts)  
- "both" (has both indoor and outdoor courts)
- "unknown" (cannot determine from reviews)

Look for keywords like: indoor, outdoor, covered, open-air, roof, ceiling, weather, rain, sun, etc.

Reviews:
{review_text}

Respond with ONLY a valid JSON object in this exact format:
{{"court_type": "indoor|outdoor|both|unknown", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""
    
    def _analyze_with_openai(self, prompt: str) -> Optional[str]:
        """Analyze using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Only return if confidence is high enough
        if result.get("confidence", 0) >= 0.6:
            court_type = result.get("court_type")
            return court_type if court_type != "unknown" else None
        
        return None
    
    def _analyze_with_anthropic(self, prompt: str) -> Optional[str]:
        """Analyze using Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            temperature=0.0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result = json.loads(response.content[0].text)
        
        # Only return if confidence is high enough
        if result.get("confidence", 0) >= 0.6:
            court_type = result.get("court_type")
            return court_type if court_type != "unknown" else None
        
        return None
    
    def enrich_facility(self, facility: Facility, reviews: List[str]) -> Facility:
        """
        Enrich a facility with indoor/outdoor information.
        
        Args:
            facility: Facility object to enrich
            reviews: List of review texts
            
        Returns:
            Updated facility object
        """
        if not facility.indoor_outdoor:  # Only analyze if not already set
            facility.indoor_outdoor = self.analyze_reviews(reviews)
        
        return facility


# src/collectors/review_collector.py

import googlemaps
from typing import List, Dict, Any
import time

class ReviewCollector:
    """Collect Google reviews for facilities."""
    
    def __init__(self, api_key: str):
        self.client = googlemaps.Client(key=api_key)
        self.rate_limit_delay = 0.2
    
    def get_reviews(self, place_id: str, max_reviews: int = 20) -> List[str]:
        """
        Fetch reviews for a place.
        
        Args:
            place_id: Google Place ID
            max_reviews: Maximum number of reviews to fetch
            
        Returns:
            List of review texts
        """
        try:
            place_details = self.client.place(
                place_id=place_id,
                fields=['reviews']
            )
            
            reviews = place_details.get('result', {}).get('reviews', [])
            
            # Extract only review text
            review_texts = [
                review.get('text', '')
                for review in reviews[:max_reviews]
                if review.get('text')
            ]
            
            time.sleep(self.rate_limit_delay)
            
            return review_texts
        
        except Exception as e:
            print(f"Error fetching reviews for {place_id}: {e}")
            return []
```

## 7. Data Processing Pipeline

### 7.1 Data Cleaning

```python
# src/processors/cleaner.py

import pandas as pd
from typing import List
from ..models.facility import Facility

class DataCleaner:
    """Clean and validate facility data."""
    
    @staticmethod
    def clean_facilities(facilities: List[Facility]) -> List[Facility]:
        """
        Clean and validate facility data.
        
        Operations:
        - Remove invalid coordinates
        - Normalize city names
        - Remove facilities with no city
        - Validate rating ranges
        """
        cleaned = []
        
        for facility in facilities:
            # Skip if no city identified
            if not facility.city:
                continue
            
            # Validate coordinates (Algarve bounds)
            if not (36.96 <= facility.latitude <= 37.42):
                continue
            if not (-9.0 <= facility.longitude <= -7.4):
                continue
            
            # Ensure rating is valid
            if facility.rating and (facility.rating < 0 or facility.rating > 5):
                facility.rating = None
            
            cleaned.append(facility)
        
        return cleaned
    
    @staticmethod
    def to_dataframe(facilities: List[Facility]) -> pd.DataFrame:
        """Convert facilities to DataFrame."""
        return pd.DataFrame([f.to_dict() for f in facilities])
```

### 7.2 Deduplication

```python
# src/processors/deduplicator.py

import pandas as pd
from typing import List
from ..models.facility import Facility

class Deduplicator:
    """Remove duplicate facilities."""
    
    @staticmethod
    def deduplicate(facilities: List[Facility]) -> List[Facility]:
        """
        Remove duplicates based on:
        1. place_id (exact match)
        2. Name + approximate location (fuzzy match)
        """
        # First pass: remove exact place_id duplicates
        seen_ids = set()
        unique = []
        
        for facility in facilities:
            if facility.place_id not in seen_ids:
                seen_ids.add(facility.place_id)
                unique.append(facility)
        
        # Second pass: fuzzy matching on name + location
        df = pd.DataFrame([f.to_dict() for f in unique])
        
        # Group by city and similar names/coordinates
        df['name_lower'] = df['name'].str.lower().str.strip()
        df['lat_round'] = df['latitude'].round(3)
        df['lng_round'] = df['longitude'].round(3)
        
        # Keep first occurrence of each group
        df_dedup = df.drop_duplicates(
            subset=['city', 'name_lower', 'lat_round', 'lng_round'],
            keep='first'
        )
        
        # Convert back to Facility objects
        return [
            Facility(**row)
            for _, row in df_dedup.iterrows()
        ]
```

## 8. Analysis & Scoring

### 8.1 City Aggregator

```python
# src/analyzers/aggregator.py

import pandas as pd
from typing import List, Dict
from ..models.facility import Facility
from ..models.city import CityStats

class CityAggregator:
    """Aggregate facility data by city."""
    
    # Algarve city populations (2021 estimates)
    CITY_POPULATIONS = {
        'Albufeira': 42388,
        'Aljezur': 5347,
        'Castro Marim': 6747,
        'Faro': 64560,
        'Lagoa': 23676,
        'Lagos': 31049,
        'Loulé': 72162,
        'Monchique': 5958,
        'Olhão': 45396,
        'Portimão': 59896,
        'São Brás de Alportel': 11381,
        'Silves': 37126,
        'Tavira': 26167,
        'Vila do Bispo': 5717,
        'Vila Real de Santo António': 19156
    }
    
    def aggregate(self, facilities: List[Facility]) -> List[CityStats]:
        """Aggregate facilities by city."""
        df = pd.DataFrame([f.to_dict() for f in facilities])
        
        city_stats = []
        
        for city, group in df.groupby('city'):
            stats = CityStats(
                city=city,
                total_facilities=len(group),
                avg_rating=group['rating'].mean() if not group['rating'].isna().all() else None,
                median_rating=group['rating'].median() if not group['rating'].isna().all() else None,
                total_reviews=int(group['review_count'].sum()),
                center_lat=group['latitude'].mean(),
                center_lng=group['longitude'].mean(),
                population=self.CITY_POPULATIONS.get(city)
            )
            
            # Calculate per capita if population available
            if stats.population:
                stats.facilities_per_capita = (stats.total_facilities / stats.population) * 10000
            
            city_stats.append(stats)
        
        return city_stats
```

### 8.2 Opportunity Scorer

```python
# src/analyzers/scorer.py

import numpy as np
from typing import List
from ..models.city import CityStats

class OpportunityScorer:
    """Calculate opportunity scores for cities."""
    
    def calculate_scores(self, city_stats: List[CityStats]) -> List[CityStats]:
        """
        Calculate opportunity scores using normalized weights.
        
        Formula:
        Opportunity Score = (Population Weight × 0.2) 
                          + (Low Saturation Weight × 0.3)
                          + (Quality Gap Weight × 0.2)
                          + (Geographic Gap Weight × 0.3)
        """
        # Extract metrics for normalization
        populations = [s.population for s in city_stats if s.population]
        saturations = [s.facilities_per_capita for s in city_stats if s.facilities_per_capita]
        ratings = [s.avg_rating for s in city_stats if s.avg_rating]
        
        # Calculate normalized weights for each city
        for stats in city_stats:
            stats.population_weight = self._normalize_population(
                stats.population, populations
            )
            
            stats.saturation_weight = self._normalize_saturation(
                stats.facilities_per_capita, saturations
            )
            
            stats.quality_gap_weight = self._normalize_quality_gap(
                stats.avg_rating, ratings
            )
            
            stats.geographic_gap_weight = self._normalize_geographic_gap(
                stats.avg_distance_to_nearest
            )
            
            # Calculate final score
            stats.calculate_opportunity_score()
        
        return city_stats
    
    def _normalize_population(self, value: float, all_values: List[float]) -> float:
        """Normalize population (higher is better)."""
        if value is None or not all_values:
            return 0.5
        return (value - min(all_values)) / (max(all_values) - min(all_values) + 1e-6)
    
    def _normalize_saturation(self, value: float, all_values: List[float]) -> float:
        """Normalize saturation (lower is better - inverted)."""
        if value is None or not all_values:
            return 0.5
        normalized = (value - min(all_values)) / (max(all_values) - min(all_values) + 1e-6)
        return 1 - normalized  # Invert: lower saturation = higher score
    
    def _normalize_quality_gap(self, value: float, all_values: List[float]) -> float:
        """Normalize quality gap (lower rating = higher opportunity - inverted)."""
        if value is None or not all_values:
            return 0.5
        normalized = (value - min(all_values)) / (max(all_values) - min(all_values) + 1e-6)
        return 1 - normalized  # Invert: lower rating = higher opportunity
    
    def _normalize_geographic_gap(self, value: float) -> float:
        """Normalize geographic gap (larger distance = higher opportunity)."""
        if value is None:
            return 0.5
        # Simple normalization: cap at 20km
        return min(value / 20.0, 1.0)
```

### 8.3 Distance Calculator

```python
# src/analyzers/distance.py

from geopy.distance import geodesic
from typing import List, Tuple
from ..models.facility import Facility

class DistanceCalculator:
    """Calculate geographic distances between facilities."""
    
    @staticmethod
    def calculate_avg_distance_to_nearest(
        city: str,
        all_facilities: List[Facility]
    ) -> float:
        """
        Calculate average distance to nearest facility for a city.
        Uses center points of neighboring cities.
        """
        city_facilities = [f for f in all_facilities if f.city == city]
        other_facilities = [f for f in all_facilities if f.city != city]
        
        if not city_facilities or not other_facilities:
            return 0.0
        
        # Calculate center of the city
        city_center = (
            sum(f.latitude for f in city_facilities) / len(city_facilities),
            sum(f.longitude for f in city_facilities) / len(city_facilities)
        )
        
        # Find nearest facility from other cities
        min_distance = min(
            geodesic(city_center, (f.latitude, f.longitude)).kilometers
            for f in other_facilities
        )
        
        return min_distance
    
    @staticmethod
    def calculate_travel_willingness_radius(city_population: int) -> float:
        """
        Estimate how far people are willing to travel based on city size.
        
        Assumptions:
        - Larger cities: people travel less (more options)
        - Smaller cities: people travel more (fewer options)
        
        Returns:
            Radius in kilometers
        """
        if city_population > 50000:
            return 5.0  # Urban areas
        elif city_population > 20000:
            return 10.0  # Mid-size towns
        else:
            return 15.0  # Small towns
```

## 9. Streamlit Application

### 9.1 Main App Structure

```python
# app/app.py

import streamlit as st
import pandas as pd
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Algarve Padel Market Research",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_data():
    """Load processed data."""
    facilities_df = pd.read_csv("data/processed/facilities.csv")
    cities_df = pd.read_csv("data/processed/city_stats.csv")
    return facilities_df, cities_df

def main():
    st.title("🎾 Algarve Padel Market Research")
    st.markdown("Identify optimal locations for new padel facilities in Algarve")
    
    # Load data
    try:
        facilities_df, cities_df = load_data()
    except FileNotFoundError:
        st.error("Data not found. Please run data collection first.")
        st.code("python scripts/collect_data.py")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    selected_cities = st.sidebar.multiselect(
        "Select Cities",
        options=cities_df['city'].tolist(),
        default=cities_df['city'].tolist()
    )
    
    min_rating = st.sidebar.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.5
    )
    
    # Filter data
    filtered_facilities = facilities_df[
        (facilities_df['city'].isin(selected_cities)) &
        (facilities_df['rating'] >= min_rating)
    ]
    
    filtered_cities = cities_df[cities_df['city'].isin(selected_cities)]
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Facilities", len(filtered_facilities))
    
    with col2:
        avg_rating = filtered_facilities['rating'].mean()
        st.metric("Avg Rating", f"{avg_rating:.2f}⭐")
    
    with col3:
        total_reviews = filtered_facilities['review_count'].sum()
        st.metric("Total Reviews", f"{total_reviews:,}")
    
    with col4:
        top_city = filtered_cities.nlargest(1, 'opportunity_score')['city'].values[0]
        st.metric("Top Opportunity", top_city)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🗺️ Map", "📈 Analysis"])
    
    with tab1:
        render_overview(filtered_facilities, filtered_cities)
    
    with tab2:
        render_map(filtered_facilities, filtered_cities)
    
    with tab3:
        render_analysis(filtered_cities)

if __name__ == "__main__":
    main()
```

### 9.2 Map Component

```python
# app/components/map_view.py

import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd

def create_map(facilities_df: pd.DataFrame, cities_df: pd.DataFrame) -> folium.Map:
    """Create interactive map with facilities and city markers."""
    
    # Center on Algarve
    center_lat = 37.1
    center_lng = -8.0
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add facility markers
    for _, facility in facilities_df.iterrows():
        # Color based on rating
        if pd.isna(facility['rating']):
            color = 'gray'
        elif facility['rating'] >= 4.5:
            color = 'green'
        elif facility['rating'] >= 4.0:
            color = 'blue'
        elif facility['rating'] >= 3.5:
            color = 'orange'
        else:
            color = 'red'
        
        # Popup content
        popup_html = f"""
        <div style="width: 200px">
            <h4>{facility['name']}</h4>
            <p><b>City:</b> {facility['city']}</p>
            <p><b>Rating:</b> {facility['rating']}⭐ ({facility['review_count']} reviews)</p>
            <p><b>Address:</b> {facility['address']}</p>
            {f'<a href="{facility["google_url"]}" target="_blank">View on Google Maps</a>' if pd.notna(facility.get('google_url')) else ''}
        </div>
        """
        
        folium.CircleMarker(
            location=[facility['latitude'], facility['longitude']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            tooltip=facility['name']
        ).add_to(m)
    
    # Add city centers with opportunity scores
    for _, city in cities_df.iterrows():
        folium.Marker(
            location=[city['center_lat'], city['center_lng']],
            popup=f"""
            <div style="width: 200px">
                <h4>{city['city']}</h4>
                <p><b>Opportunity Score:</b> {city['opportunity_score']:.1f}/100</p>
                <p><b>Facilities:</b> {city['total_facilities']}</p>
                <p><b>Avg Rating:</b> {city['avg_rating']:.2f}⭐</p>
                <p><b>Population:</b> {city['population']:,}</p>
            </div>
            """,
            icon=folium.Icon(color='purple', icon='info-sign'),
            tooltip=f"{city['city']}: {city['opportunity_score']:.0f} score"
        ).add_to(m)
    
    # Add heatmap layer
    heat_data = [
        [row['latitude'], row['longitude']]
        for _, row in facilities_df.iterrows()
    ]
    
    plugins.HeatMap(heat_data, radius=15, blur=25, name='Density Heatmap').add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m
```

## 10. Testing Strategy

### 10.1 Test Structure

```python
# tests/conftest.py

import pytest
from src.models.facility import Facility
from datetime import datetime

@pytest.fixture
def sample_facility():
    """Sample facility for testing."""
    return Facility(
        place_id="ChIJtest123",
        name="Test Padel Club",
        address="Rua Test, 123, Albufeira",
        city="Albufeira",
        latitude=37.0885,
        longitude=-8.2475,
        rating=4.5,
        review_count=150,
        google_url="https://maps.google.com/?cid=test",
        facility_type="club"
    )

@pytest.fixture
def sample_facilities():
    """List of sample facilities for testing."""
    return [
        Facility(
            place_id=f"test_{i}",
            name=f"Club {i}",
            address=f"Address {i}",
            city="Albufeira" if i % 2 == 0 else "Faro",
            latitude=37.0 + i * 0.01,
            longitude=-8.0 + i * 0.01,
            rating=3.5 + (i % 3) * 0.5,
            review_count=100 + i * 10
        )
        for i in range(10)
    ]
```

### 10.2 Unit Tests Example

```python
# tests/test_analyzers/test_scorer.py

import pytest
from src.analyzers.scorer import OpportunityScorer
from src.models.city import CityStats

def test_opportunity_scorer_calculation():
    """Test opportunity score calculation."""
    scorer = OpportunityScorer()
    
    city_stats = [
        CityStats(
            city="Albufeira",
            total_facilities=10,
            avg_rating=4.0,
            median_rating=4.0,
            total_reviews=1000,
            center_lat=37.0,
            center_lng=-8.0,
            population=40000,
            facilities_per_capita=2.5,
            avg_distance_to_nearest=5.0
        ),
        CityStats(
            city="Faro",
            total_facilities=15,
            avg_rating=4.5,
            median_rating=4.5,
            total_reviews=1500,
            center_lat=37.0,
            center_lng=-7.9,
            population=60000,
            facilities_per_capita=2.5,
            avg_distance_to_nearest=3.0
        )
    ]
    
    scored = scorer.calculate_scores(city_stats)
    
    # Assertions
    assert all(0 <= s.opportunity_score <= 100 for s in scored)
    assert all(0 <= s.population_weight <= 1 for s in scored)
    assert all(0 <= s.saturation_weight <= 1 for s in scored)
```

## 11. Configuration Management

```python
# src/config.py

from pydantic import BaseSettings, Field
from pathlib import Path

class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    google_api_key: str = Field(..., env='GOOGLE_API_KEY')
    
    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    cache_dir: Path = data_dir / "cache"
    
    # Data Collection
    search_region: str = "Algarve, Portugal"
    cache_enabled: bool = True
    cache_ttl_days: int = 30
    rate_limit_delay: float = 0.2  # seconds
    
    # Analysis
    min_rating: float = 0.0
    max_rating: float = 5.0
    
    # Scoring weights
    population_weight: float = 0.2
    saturation_weight: float = 0.3
    quality_gap_weight: float = 0.2
    geographic_gap_weight: float = 0.3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = Settings()
```

## 12. CLI Scripts

### 12.1 Data Collection Script

```python
# scripts/collect_data.py

"""
CLI script to collect padel facility data.

Usage:
    python scripts/collect_data.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.collectors.google_places import GooglePlacesCollector
from src.processors.cleaner import DataCleaner
from src.processors.deduplicator import Deduplicator
import pandas as pd

def main():
    print("🎾 Starting Algarve Padel Field Data Collection")
    print("=" * 60)
    
    # Initialize collector
    print("\n1. Initializing Google Places collector...")
    collector = GooglePlacesCollector(
        api_key=settings.google_api_key,
        cache_enabled=settings.cache_enabled
    )
    
    # Collect data
    print(f"\n2. Searching for padel facilities in {settings.search_region}...")
    facilities = collector.search_padel_facilities(settings.search_region)
    print(f"   Found {len(facilities)} facilities")
    
    # Clean data
    print("\n3. Cleaning data...")
    cleaner = DataCleaner()
    facilities = cleaner.clean_facilities(facilities)
    print(f"   {len(facilities)} facilities after cleaning")
    
    # Deduplicate
    print("\n4. Removing duplicates...")
    deduplicator = Deduplicator()
    facilities = deduplicator.deduplicate(facilities)
    print(f"   {len(facilities)} unique facilities")
    
    # Save raw data
    print("\n5. Saving data...")
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame([f.to_dict() for f in facilities])
    output_file = settings.raw_data_dir / "facilities.csv"
    df.to_csv(output_file, index=False)
    
    print(f"   Saved to: {output_file}")
    print(f"\n✅ Data collection complete!")
    print(f"   Total facilities: {len(facilities)}")
    print(f"   Cities covered: {df['city'].nunique()}")
    print(f"\nNext step: python scripts/process_data.py")

if __name__ == "__main__":
    main()
```

### 12.2 Data Processing Script

```python
# scripts/process_data.py

"""
CLI script to process collected data and calculate analytics.

Usage:
    python scripts/process_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.analyzers.aggregator import CityAggregator
from src.analyzers.scorer import OpportunityScorer
from src.analyzers.distance import DistanceCalculator
from src.models.facility import Facility
import pandas as pd

def main():
    print("📊 Starting Data Processing")
    print("=" * 60)
    
    # Load raw data
    print("\n1. Loading raw data...")
    raw_file = settings.raw_data_dir / "facilities.csv"
    
    if not raw_file.exists():
        print("❌ Error: Raw data not found. Run collect_data.py first.")
        return
    
    df = pd.read_csv(raw_file)
    facilities = [Facility(**row.to_dict()) for _, row in df.iterrows()]
    print(f"   Loaded {len(facilities)} facilities")
    
    # Aggregate by city
    print("\n2. Aggregating by city...")
    aggregator = CityAggregator()
    city_stats = aggregator.aggregate(facilities)
    print(f"   {len(city_stats)} cities analyzed")
    
    # Calculate distances
    print("\n3. Calculating geographic metrics...")
    distance_calc = DistanceCalculator()
    for stats in city_stats:
        stats.avg_distance_to_nearest = distance_calc.calculate_avg_distance_to_nearest(
            stats.city, facilities
        )
    
    # Calculate opportunity scores
    print("\n4. Computing opportunity scores...")
    scorer = OpportunityScorer()
    city_stats = scorer.calculate_scores(city_stats)
    
    # Sort by opportunity score
    city_stats.sort(key=lambda x: x.opportunity_score, reverse=True)
    
    # Save processed data
    print("\n5. Saving processed data...")
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save facilities (copy from raw)
    df.to_csv(settings.processed_data_dir / "facilities.csv", index=False)
    
    # Save city stats
    city_df = pd.DataFrame([s.dict() for s in city_stats])
    city_df.to_csv(settings.processed_data_dir / "city_stats.csv", index=False)
    
    print(f"\n✅ Processing complete!")
    print(f"\nTop 5 Cities by Opportunity Score:")
    print("-" * 60)
    for i, stats in enumerate(city_stats[:5], 1):
        print(f"{i}. {stats.city}: {stats.opportunity_score:.1f}/100")
        print(f"   Facilities: {stats.total_facilities}, "
              f"Avg Rating: {stats.avg_rating:.2f}⭐, "
              f"Population: {stats.population:,}")
    
    print(f"\nNext step: streamlit run app/app.py")

if __name__ == "__main__":
    main()
```

## 13. Deployment & Setup

### 13.1 Requirements

```txt
# requirements.txt

# Core
python>=3.10

# Data Processing
pandas==2.1.0
numpy==1.25.0

# Google APIs
googlemaps==4.10.0
pytrends==4.9.0

# HTTP & Caching
requests==2.31.0
requests-cache==1.1.0

# Geospatial
geopy==2.3.0
folium==0.14.0

# Visualization
plotly==5.16.0
streamlit==1.27.0
streamlit-folium==0.15.0

# Data Validation
pydantic==2.3.0

# LLM APIs (optional - for indoor/outdoor analysis)
openai==1.12.0
anthropic==0.18.0

# Environment
python-dotenv==1.0.0

# Development
pytest==7.4.0
pytest-cov==4.1.0
black==23.7.0
mypy==1.5.0
```

### 13.2 Environment Setup

```bash
# .env.example

# Google API Key (required)
GOOGLE_API_KEY=your_api_key_here

# LLM API Keys (optional - for indoor/outdoor analysis)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
LLM_PROVIDER=openai  # or 'anthropic'
LLM_MODEL=gpt-4o-mini  # or 'claude-3-5-haiku-20241022'

# Optional Configuration
SEARCH_REGION=Algarve, Portugal
CACHE_ENABLED=true
CACHE_TTL_DAYS=30
RATE_LIMIT_DELAY=0.2
```

### 13.3 Setup Script

```bash
# setup.sh

#!/bin/bash

echo "🎾 Setting up Algarve Padel Market Research Tool"
echo "================================================"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directory structure
echo "Creating directories..."
mkdir -p data/{raw,processed,cache,exports}
mkdir -p tests

# Copy environment template
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your Google API key"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GOOGLE_API_KEY"
echo "2. Run: python scripts/collect_data.py"
echo "3. Run: python scripts/process_data.py"
echo "4. Run: streamlit run app/app.py"
```

## 14. Development Stories (Parallelizable Tasks)

This project is designed for parallel development by LLM agents. Each story is independent with clear inputs/outputs following an API-like design pattern.

### 🔷 PRE-LAYER: Environment Setup (Build Absolutely First)

#### Story 0.0: Development Setup
**Priority**: P0 (Blocker)  
**Dependencies**: None  
**Estimated Effort**: Small

**Description**: Create foundational development environment setup including directory structure, dependency management, and automated setup scripts.

**Input Contract**: Fresh clone or empty directory  
**Output Contract**: 
- Complete directory structure
- Python virtual environment
- All dependencies installed
- Configuration templates

**Acceptance Criteria**:
- [ ] setup.sh script automates environment creation
- [ ] .gitignore configured for Python projects
- [ ] pyproject.toml with project metadata
- [ ] requirements.txt with all dependencies
- [ ] Works on macOS and Linux

**Files to Create**:
- `setup.sh`
- `.gitignore`
- `pyproject.toml`
- `requirements.txt`
- `README.md` (basic template)

**Note**: This story must be completed FIRST. It blocks all other stories.

---

### 🔷 LAYER 0: Foundation Stories (Build First)

#### Story 0.1: Data Models & Validation
**Priority**: P0 (Blocker)  
**Dependencies**: None  
**Estimated Effort**: Small

**Description**: Create Pydantic models for data validation and type safety.

**Input Contract**: None  
**Output Contract**: 
- `Facility` model with validation
- `CityStats` model with validation
- Exports to dict/JSON/CSV

**Acceptance Criteria**:
- [ ] Facility model with all fields (including `indoor_outdoor`)
- [ ] CityStats model with opportunity score calculation
- [ ] Validators for ratings, coordinates, indoor/outdoor
- [ ] to_dict() methods for serialization
- [ ] 100% test coverage on models

**Files to Create**:
- `src/models/facility.py`
- `src/models/city.py`
- `tests/test_models/test_facility.py`
- `tests/test_models/test_city.py`

---

#### Story 0.2: Configuration Management
**Priority**: P0 (Blocker)  
**Dependencies**: None  
**Estimated Effort**: Small

**Description**: Centralized configuration using environment variables.

**Input Contract**: `.env` file with keys  
**Output Contract**: `Settings` singleton with typed configuration

**Acceptance Criteria**:
- [ ] Settings class with all config parameters
- [ ] Environment variable loading with defaults
- [ ] API key validation
- [ ] Path management for data directories
- [ ] Unit tests for config loading

**Files to Create**:
- `src/config.py`
- `.env.example`
- `tests/test_config.py`

---

#### Story 0.3: Caching Utilities
**Priority**: P0 (Blocker)  
**Dependencies**: None  
**Estimated Effort**: Small

**Description**: Generic caching decorator for API responses.

**Input Contract**: Function to cache  
**Output Contract**: Cached function with TTL support

**Acceptance Criteria**:
- [ ] `@cache_response(ttl_days)` decorator
- [ ] File-based cache in `data/cache/`
- [ ] Cache key generation from function args
- [ ] TTL expiration logic
- [ ] Tests with mock functions

**Files to Create**:
- `src/utils/cache.py`
- `tests/test_utils/test_cache.py`

---

### 🔷 LAYER 1: Data Collection Stories (Can Run in Parallel After Layer 0)

#### Story 1.1: Google Places Collector
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1, 0.2, 0.3  
**Estimated Effort**: Medium

**Description**: Collect padel facilities from Google Places API.

**Input Contract**:
- `api_key: str`
- `region: str` (e.g., "Algarve, Portugal")

**Output Contract**: `List[Facility]` with basic info (no reviews yet)

**API Surface**:
```python
class GooglePlacesCollector:
    def __init__(api_key: str, cache_enabled: bool) -> None
    def search_padel_facilities(region: str) -> List[Facility]
```

**Acceptance Criteria**:
- [ ] Search with multiple query variations
- [ ] Pagination handling
- [ ] Rate limiting (0.2s delay)
- [ ] Caching enabled by default
- [ ] City extraction for Algarve municipalities
- [ ] Returns 90%+ of known facilities
- [ ] Unit tests with mocked API
- [ ] Integration test with real API (optional)

**Files to Create**:
- `src/collectors/google_places.py`
- `tests/test_collectors/test_google_places.py`

---

#### Story 1.2: Review Collector
**Priority**: P1 (Nice to Have)  
**Dependencies**: Story 0.1, 0.2, 0.3  
**Estimated Effort**: Small

**Description**: Fetch Google reviews for facilities.

**Input Contract**: 
- `place_id: str`
- `max_reviews: int = 20`

**Output Contract**: `List[str]` (review texts)

**API Surface**:
```python
class ReviewCollector:
    def __init__(api_key: str) -> None
    def get_reviews(place_id: str, max_reviews: int) -> List[str]
```

**Acceptance Criteria**:
- [ ] Fetch reviews via Google Places API
- [ ] Extract only text content
- [ ] Handle missing reviews gracefully
- [ ] Rate limiting
- [ ] Unit tests with mocked API

**Files to Create**:
- `src/collectors/review_collector.py`
- `tests/test_collectors/test_review_collector.py`

---

#### Story 1.3: Google Trends Collector (Optional)
**Priority**: P2 (Optional)  
**Dependencies**: Story 0.1, 0.2  
**Estimated Effort**: Small

**Description**: Collect Google Trends data for padel interest by region.

**Input Contract**: 
- `keyword: str` (e.g., "padel")
- `regions: List[str]`

**Output Contract**: `Dict[str, float]` (city -> interest score)

**API Surface**:
```python
class GoogleTrendsCollector:
    def __init__() -> None
    def get_regional_interest(keyword: str, regions: List[str]) -> Dict[str, float]
```

**Acceptance Criteria**:
- [ ] pytrends integration
- [ ] Regional interest by city
- [ ] Error handling for missing data
- [ ] Unit tests

**Files to Create**:
- `src/collectors/google_trends.py`
- `tests/test_collectors/test_google_trends.py`

---

### 🔷 LAYER 2: Enrichment Stories (Can Run in Parallel After Layer 1)

#### Story 2.1: LLM Indoor/Outdoor Analyzer
**Priority**: P1 (Nice to Have)  
**Dependencies**: Story 0.1, 1.2  
**Estimated Effort**: Medium

**Description**: Use LLM to extract indoor/outdoor information from reviews.

**Input Contract**: `List[str]` (review texts)  
**Output Contract**: `Optional[str]` ('indoor', 'outdoor', 'both', or None)

**API Surface**:
```python
class IndoorOutdoorAnalyzer:
    def __init__(provider: str, model: str, api_key: str) -> None
    def analyze_reviews(reviews: List[str]) -> Optional[str]
    def enrich_facility(facility: Facility, reviews: List[str]) -> Facility
```

**Acceptance Criteria**:
- [ ] Support OpenAI and Anthropic
- [ ] JSON-structured output
- [ ] Confidence threshold (0.6+)
- [ ] Graceful handling of API errors
- [ ] Only update if `indoor_outdoor` is None
- [ ] Unit tests with mocked LLM responses
- [ ] Cost optimization (use cheap models)

**Files to Create**:
- `src/enrichers/indoor_outdoor_analyzer.py`
- `src/enrichers/base_llm.py`
- `tests/test_enrichers/test_indoor_outdoor_analyzer.py`

---

### 🔷 LAYER 3: Processing Stories (Can Run in Parallel After Layer 1)

#### Story 3.1: Data Cleaner
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1  
**Estimated Effort**: Small

**Description**: Clean and validate facility data.

**Input Contract**: `List[Facility]` (raw)  
**Output Contract**: `List[Facility]` (cleaned)

**API Surface**:
```python
class DataCleaner:
    @staticmethod
    def clean_facilities(facilities: List[Facility]) -> List[Facility]
    @staticmethod
    def to_dataframe(facilities: List[Facility]) -> pd.DataFrame
```

**Acceptance Criteria**:
- [ ] Remove invalid coordinates
- [ ] Filter to Algarve bounds (lat: 36.96-37.42, lng: -9.0 to -7.4)
- [ ] Remove facilities without city
- [ ] Normalize city names
- [ ] Validate rating ranges
- [ ] 100% test coverage

**Files to Create**:
- `src/processors/cleaner.py`
- `tests/test_processors/test_cleaner.py`

---

#### Story 3.2: Deduplicator
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1  
**Estimated Effort**: Small

**Description**: Remove duplicate facilities.

**Input Contract**: `List[Facility]`  
**Output Contract**: `List[Facility]` (deduplicated)

**API Surface**:
```python
class Deduplicator:
    @staticmethod
    def deduplicate(facilities: List[Facility]) -> List[Facility]
```

**Acceptance Criteria**:
- [ ] Remove exact place_id duplicates
- [ ] Fuzzy matching on name + location
- [ ] Keep facility with most complete data
- [ ] Unit tests with duplicate fixtures

**Files to Create**:
- `src/processors/deduplicator.py`
- `tests/test_processors/test_deduplicator.py`

---

### 🔷 LAYER 4: Analysis Stories (Can Run in Parallel After Layer 3)

#### Story 4.1: City Aggregator
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1  
**Estimated Effort**: Medium

**Description**: Aggregate facility data by city.

**Input Contract**: `List[Facility]`  
**Output Contract**: `List[CityStats]`

**API Surface**:
```python
class CityAggregator:
    def aggregate(facilities: List[Facility]) -> List[CityStats]
```

**Acceptance Criteria**:
- [ ] Group by city
- [ ] Calculate avg/median ratings
- [ ] Total review counts
- [ ] Center coordinates
- [ ] Facilities per capita (if population data available)
- [ ] Unit tests with sample data

**Files to Create**:
- `src/analyzers/aggregator.py`
- `tests/test_analyzers/test_aggregator.py`

---

#### Story 4.2: Distance Calculator
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1  
**Estimated Effort**: Small

**Description**: Calculate geographic distances between facilities.

**Input Contract**: 
- `city: str`
- `all_facilities: List[Facility]`

**Output Contract**: `float` (average distance to nearest facility in km)

**API Surface**:
```python
class DistanceCalculator:
    @staticmethod
    def calculate_avg_distance_to_nearest(city: str, facilities: List[Facility]) -> float
    @staticmethod
    def calculate_travel_willingness_radius(population: int) -> float
```

**Acceptance Criteria**:
- [ ] Use geopy for accurate distances
- [ ] Calculate city center from facility coordinates
- [ ] Find nearest neighbor distances
- [ ] Travel willingness by population size
- [ ] Unit tests with known coordinates

**Files to Create**:
- `src/analyzers/distance.py`
- `tests/test_analyzers/test_distance.py`

---

#### Story 4.3: Opportunity Scorer
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 0.1, 4.1, 4.2  
**Estimated Effort**: Medium

**Description**: Calculate opportunity scores for cities.

**Input Contract**: `List[CityStats]` (with distances calculated)  
**Output Contract**: `List[CityStats]` (with scores)

**API Surface**:
```python
class OpportunityScorer:
    def calculate_scores(city_stats: List[CityStats]) -> List[CityStats]
```

**Acceptance Criteria**:
- [ ] Normalize all weights (0-1 range)
- [ ] Population weight (20%)
- [ ] Saturation weight (30%, inverted)
- [ ] Quality gap weight (20%, inverted)
- [ ] Geographic gap weight (30%)
- [ ] Final score 0-100
- [ ] Unit tests validating score calculations

**Files to Create**:
- `src/analyzers/scorer.py`
- `tests/test_analyzers/test_scorer.py`

---

### 🔷 LAYER 5: CLI & Orchestration Stories (Depends on All Previous Layers)

#### Story 5.1: Data Collection CLI
**Priority**: P0 (Critical Path)  
**Dependencies**: Stories 1.1, 1.2, 2.1, 3.1, 3.2  
**Estimated Effort**: Small

**Description**: CLI script to orchestrate data collection.

**Input Contract**: Command line execution  
**Output Contract**: CSV file with facilities

**Script Behavior**:
1. Initialize collectors
2. Search for facilities
3. Clean data
4. Deduplicate
5. (Optional) Fetch reviews
6. (Optional) Enrich with LLM
7. Save to `data/raw/facilities.csv`

**Acceptance Criteria**:
- [ ] Progress logging
- [ ] Error handling
- [ ] Save intermediate results
- [ ] Execution time < 30 minutes
- [ ] Runnable: `python scripts/collect_data.py`

**Files to Create**:
- `scripts/collect_data.py`

---

#### Story 5.2: Data Processing CLI
**Priority**: P0 (Critical Path)  
**Dependencies**: Stories 4.1, 4.2, 4.3  
**Estimated Effort**: Small

**Description**: CLI script to process collected data and calculate analytics.

**Input Contract**: `data/raw/facilities.csv`  
**Output Contract**: 
- `data/processed/facilities.csv`
- `data/processed/city_stats.csv`

**Script Behavior**:
1. Load raw facilities
2. Aggregate by city
3. Calculate distances
4. Calculate opportunity scores
5. Sort by score
6. Save results

**Acceptance Criteria**:
- [ ] Load from CSV
- [ ] Call all analyzers in sequence
- [ ] Display top 5 cities
- [ ] Save processed data
- [ ] Runnable: `python scripts/process_data.py`

**Files to Create**:
- `scripts/process_data.py`

---

### 🔷 LAYER 6: Visualization Stories (Can Build Components in Parallel)

#### Story 6.1: Streamlit Main App Structure
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 5.2  
**Estimated Effort**: Small

**Description**: Main Streamlit app with data loading and layout.

**Input Contract**: CSV files from `data/processed/`  
**Output Contract**: Web app with tabs/pages

**Acceptance Criteria**:
- [ ] Load data with caching
- [ ] Sidebar filters (cities, min rating)
- [ ] Key metrics display (4 columns)
- [ ] Tab navigation (Overview, Map, Analysis)
- [ ] Runnable: `streamlit run app/app.py`

**Files to Create**:
- `app/app.py`

---

#### Story 6.2: Interactive Map Component
**Priority**: P0 (Critical Path)  
**Dependencies**: Story 6.1  
**Estimated Effort**: Medium

**Description**: Folium map with facility markers and city centers.

**Input Contract**: 
- `facilities_df: pd.DataFrame`
- `cities_df: pd.DataFrame`

**Output Contract**: Interactive Folium map

**API Surface**:
```python
def create_map(facilities_df: pd.DataFrame, cities_df: pd.DataFrame) -> folium.Map
```

**Acceptance Criteria**:
- [ ] Color-coded markers by rating
- [ ] Facility popups with details
- [ ] City markers with opportunity scores
- [ ] Heatmap layer
- [ ] Layer control
- [ ] Responsive and performant

**Files to Create**:
- `app/components/map_view.py`

---

#### Story 6.3: Dashboard & Charts
**Priority**: P1 (Nice to Have)  
**Dependencies**: Story 6.1  
**Estimated Effort**: Medium

**Description**: Analytics dashboard with Plotly charts.

**Input Contract**: `city_stats_df: pd.DataFrame`  
**Output Contract**: Rendered charts in Streamlit

**Charts to Create**:
- Bar chart: Facilities per city
- Bar chart: Opportunity scores by city
- Scatter plot: Population vs. saturation
- Pie chart: Rating distribution

**Acceptance Criteria**:
- [ ] Interactive Plotly charts
- [ ] Responsive layout
- [ ] Filter integration
- [ ] Export chart data

**Files to Create**:
- `app/components/dashboard.py`

---

#### Story 6.4: Export Functionality
**Priority**: P1 (Nice to Have)  
**Dependencies**: Story 6.1  
**Estimated Effort**: Small

**Description**: Export filtered data to CSV/Excel.

**Input Contract**: Filtered dataframes  
**Output Contract**: Downloaded file

**Acceptance Criteria**:
- [ ] CSV export button
- [ ] Filtered data only
- [ ] Timestamp in filename
- [ ] Save to `data/exports/`

**Files to Create**:
- `src/utils/exporters.py`

---

### 🔷 LAYER 7: Integration & Testing Stories (Final Phase)

#### Story 7.1: Integration Tests
**Priority**: P0 (Must Have)  
**Dependencies**: All previous stories  
**Estimated Effort**: Medium

**Description**: End-to-end integration tests.

**Acceptance Criteria**:
- [ ] Test full data pipeline (collect → process)
- [ ] Test CSV export/import
- [ ] Test cache behavior
- [ ] Test error handling
- [ ] Achieve 80%+ code coverage

**Files to Create**:
- `tests/test_integration/test_pipeline.py`
- `tests/test_integration/test_cli.py`

---

#### Story 7.2: Documentation
**Priority**: P0 (Must Have)  
**Dependencies**: All implementation stories  
**Estimated Effort**: Small

**Description**: User and developer documentation.

**Deliverables**:
- [ ] README.md with setup instructions
- [ ] API_SETUP.md (Google API key guide)
- [ ] USAGE.md (CLI and Streamlit guide)
- [ ] Code docstrings review

**Files to Create**:
- `README.md`
- `docs/API_SETUP.md`
- `docs/USAGE.md`

---

### 🔷 LAYER 8: Deployment & Packaging (Post-MVP)

#### Story 8.1: Deployment & Packaging
**Priority**: P1 (Nice to Have)  
**Dependencies**: All stories (0.0-7.2)  
**Estimated Effort**: Medium

**Description**: Create deployment strategies and packaging for production use.

**Input Contract**: Completed, tested application  
**Output Contract**: 
- Docker container
- PyPI package (optional)
- Deployment documentation
- Production configuration guide

**Acceptance Criteria**:
- [ ] Dockerfile for containerization
- [ ] docker-compose.yml for easy deployment
- [ ] setup.py for PyPI packaging
- [ ] DEPLOYMENT.md documentation
- [ ] Production environment configuration
- [ ] Cloud deployment guides (Streamlit Cloud, AWS, GCP)

**Files to Create**:
- `Dockerfile`
- `docker-compose.yml`
- `setup.py`
- `.dockerignore`
- `docs/DEPLOYMENT.md`

**Note**: This is a post-MVP story for production readiness. Focus on core features first.

---

### 🔷 Story Dependency Graph

```
Story 0.0 (Dev Setup) ──────> ENABLES ALL OTHER STORIES
                              │
                              ▼
                        Layer 0 (Foundation)
                        ├── Story 0.1 (Models) ────┐
                        ├── Story 0.2 (Config) ────┤
                        └── Story 0.3 (Cache) ─────┤
                                                   ├──> Layer 1 (Collection)
                                                   │    ├── Story 1.1 (Google Places) ────┐
                                                   │    ├── Story 1.2 (Reviews) ──────────┤
                                                   │    └── Story 1.3 (Trends - Optional) ─┤
                                                   │                                        │
                                                   ├──> Layer 2 (Enrichment)               │
                                                   │    └── Story 2.1 (LLM Analyzer) ◄─────┤
                                                   │                                        │
                                                   └──> Layer 3 (Processing)               │
                                                        ├── Story 3.1 (Cleaner) ───────────┤
                                                        └── Story 3.2 (Deduplicator) ──────┤
                                                                                            │
                                                                             Layer 4 (Analysis)
                                                                             ├── Story 4.1 (Aggregator) ─────┐
                                                                             ├── Story 4.2 (Distance) ───────┤
                                                                             └── Story 4.3 (Scorer) ◄────────┤
                                                                                                             │
                                                                                      Layer 5 (CLI)          │
                                                                                      ├── Story 5.1 ◄────────┤
                                                                                      └── Story 5.2 ◄────────┤
                                                                                                             │
                                                                                   Layer 6 (Visualization)   │
                                                                                   ├── Story 6.1 (Main App) ◄┤
                                                                                   ├── Story 6.2 (Map) ◄─────┤
                                                                                   ├── Story 6.3 (Dashboard) ◄┤
                                                                                   └── Story 6.4 (Export) ◄───┤
                                                                                                              │
                                                                                         Layer 7              │
                                                                                         ├── Story 7.1 ◄──────┤
                                                                                         └── Story 7.2 ◄──────┤
                                                                                                              │
                                                                                         Layer 8              │
                                                                                         └── Story 8.1 (Deployment) ◄──┘
```

### 🔷 Parallelization Strategy

**Maximum Parallelism Points**:
1. **Start**: Story 0.0 must be completed first (blocks all others)
2. **After Story 0.0**: Stories 0.1, 0.2, 0.3 can be developed in parallel
3. **After Layer 0**: Stories 1.1, 1.2, 1.3, 3.1, 3.2 can all be developed simultaneously
4. **After Layer 1**: Story 2.1 can start
5. **After Layer 3**: Stories 4.1, 4.2 can be developed in parallel
6. **After Layer 4**: Stories 5.1, 5.2 can be developed in parallel
7. **After Story 6.1**: Stories 6.2, 6.3, 6.4 can be developed in parallel
8. **After Layer 7**: Story 8.1 can start (deployment)

## 15. Testing Checklist

### Unit Tests:
- [ ] Facility model validation
- [ ] CityStats calculations
- [ ] Data cleaning logic
- [ ] Deduplication algorithm
- [ ] Opportunity scoring
- [ ] Distance calculations

### Integration Tests:
- [ ] Google Places API integration
- [ ] End-to-end data pipeline
- [ ] CSV import/export
- [ ] Cache functionality

### Manual Testing:
- [ ] Verify all Algarve cities covered
- [ ] Spot-check facility data accuracy
- [ ] Validate opportunity scores make sense
- [ ] Test map interactivity
- [ ] Export functionality

## 16. Documentation Requirements

### Code Documentation:
- Docstrings for all classes and functions
- Type hints throughout
- Inline comments for complex logic

### User Documentation:
- README with setup instructions
- API setup guide (Google API key)
- Usage guide for CLI scripts
- Streamlit app user guide

### Developer Documentation:
- This TDD
- Architecture diagrams
- Data model references
- Testing guide

## 17. Success Metrics

- **Code Coverage**: >80% test coverage
- **Data Completeness**: ≥90% of known facilities captured
- **Performance**: Data collection completes in <30 minutes
- **Accuracy**: Opportunity scores validated against domain knowledge
- **Usability**: Non-technical user can run analysis independently

