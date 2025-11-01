# Story 2.1: LLM Indoor/Outdoor Analyzer

**Priority**: P1 (Nice to Have)  
**Layer**: 2 (Enrichment)  
**Dependencies**: Story 0.1 (Data Models), Story 1.2 (Review Collector)  
**Estimated Effort**: Medium

---

## Description

Use Large Language Models (LLMs) to extract indoor/outdoor court information from facility reviews. This enricher analyzes review text to determine if a padel facility has indoor courts, outdoor courts, or both. Supports both OpenAI and Anthropic providers for flexibility and cost optimization.

---

## Input Contract

- `reviews: List[str]` - List of review texts from Google reviews
- `provider: str` - LLM provider ("openai" or "anthropic")
- `model: str` - Model name (e.g., "gpt-4o-mini", "claude-3-5-haiku-20241022")
- `api_key: Optional[str]` - API key (if None, uses environment variable)

---

## Output Contract

Returns `Optional[str]` with one of the following values:
- `"indoor"` - Only indoor courts
- `"outdoor"` - Only outdoor courts
- `"both"` - Has both indoor and outdoor courts
- `None` - Cannot determine from reviews (low confidence or no relevant information)

---

## API Surface

```python
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
    ) -> None:
        """
        Initialize analyzer.
        
        Args:
            provider: 'openai' or 'anthropic'
            model: Model name (e.g., 'gpt-4o-mini', 'claude-3-5-haiku-20241022')
            api_key: API key (if None, uses environment variable)
        """
        pass
    
    def analyze_reviews(self, reviews: List[str]) -> Optional[str]:
        """
        Analyze reviews to determine indoor/outdoor status.
        
        Args:
            reviews: List of review texts
            
        Returns:
            'indoor', 'outdoor', 'both', or None if cannot determine
        """
        pass
    
    def enrich_facility(self, facility: Facility, reviews: List[str]) -> Facility:
        """
        Enrich a facility with indoor/outdoor information.
        
        Args:
            facility: Facility object to enrich
            reviews: List of review texts
            
        Returns:
            Updated facility object
        """
        pass
```

---

## Technical Requirements

### LLM Provider Support

**OpenAI**:
- Use `openai` Python client
- Default model: `gpt-4o-mini` (cost-effective)
- Enable JSON mode with `response_format={"type": "json_object"}`
- Temperature: 0.0 (deterministic)

**Anthropic**:
- Use `anthropic` Python client
- Default model: `claude-3-5-haiku-20241022` (cost-effective)
- Max tokens: 200
- Temperature: 0.0 (deterministic)

### Prompt Engineering

The prompt should:
1. Clearly define the task (extract indoor/outdoor information)
2. List keywords to look for (indoor, outdoor, covered, open-air, roof, ceiling, weather, rain, sun, etc.)
3. Request structured JSON output with specific schema
4. Ask for confidence score and reasoning

**Expected JSON Schema**:
```json
{
  "court_type": "indoor|outdoor|both|unknown",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

### Review Processing

- Limit to first 20 reviews to avoid token limits
- Combine all reviews into single prompt (newline-separated)
- Skip analysis if no reviews available (return None)

### Confidence Threshold

- Only return result if confidence ≥ 0.6
- If confidence < 0.6, return None
- If court_type is "unknown", return None

### Error Handling

Follow error handling patterns defined in Story 0.2:
- **Data Collection Errors** (Pattern 1): Log errors but don't crash, return None
- **API Rate Limit Errors** (Pattern 3): Retry with exponential backoff (max 3 attempts)
- Gracefully handle API errors (rate limits, network issues, invalid responses)
- Validate JSON response structure
- Return None on any error (fail gracefully)

### Cost Optimization

- Use cheapest models (gpt-4o-mini, claude-3-5-haiku)
- Limit review count to 20
- Only analyze if `facility.indoor_outdoor` is None
- Consider caching results by place_id (optional)

### Cost Tracking

Implement utility for logging LLM API usage:
```python
import logging

logger = logging.getLogger(__name__)

def log_llm_cost(model: str, input_tokens: int, output_tokens: int):
    """
    Log LLM API usage for cost tracking.
    
    Args:
        model: Model name (e.g., 'gpt-4o-mini')
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
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
```

---

## Acceptance Criteria

- [x] Support both OpenAI and Anthropic providers
- [x] JSON-structured output with confidence score
- [x] Confidence threshold of 0.6+ to return result
- [x] Graceful handling of API errors
- [x] Only update facility if `indoor_outdoor` is None
- [x] Skip analysis if no reviews available
- [x] Unit tests with mocked LLM responses
- [x] Test both OpenAI and Anthropic code paths
- [x] Cost optimization (use cheap models, limit reviews)
- [x] **Cost tracking implemented (log API usage with token counts and estimated cost)**
- [x] Type hints throughout
- [x] Docstrings for all public methods
- [x] Integration tests marked as optional

---

## Files to Create

```
src/enrichers/indoor_outdoor_analyzer.py
src/enrichers/base_llm.py (abstract base class)
tests/test_enrichers/__init__.py
tests/test_enrichers/test_indoor_outdoor_analyzer.py
```

---

## Testing Requirements

### Unit Tests (Mocked LLM)

Test the following with mocked LLM responses:

1. **OpenAI Provider - High Confidence Indoor**
   - Mock response: `{"court_type": "indoor", "confidence": 0.9, "reasoning": "..."}`
   - Verify returns "indoor"

2. **OpenAI Provider - Low Confidence**
   - Mock response: `{"court_type": "outdoor", "confidence": 0.4, "reasoning": "..."}`
   - Verify returns None

3. **Anthropic Provider - Both Courts**
   - Mock response: `{"court_type": "both", "confidence": 0.85, "reasoning": "..."}`
   - Verify returns "both"

4. **Unknown Court Type**
   - Mock response: `{"court_type": "unknown", "confidence": 0.9, "reasoning": "..."}`
   - Verify returns None

5. **Empty Reviews**
   - Input: `[]`
   - Verify returns None without API call

6. **API Error Handling**
   - Mock API raises exception
   - Verify returns None gracefully

7. **Enrich Facility - Already Set**
   - Facility already has `indoor_outdoor = "indoor"`
   - Verify facility unchanged (no API call)

8. **Enrich Facility - Not Set**
   - Facility has `indoor_outdoor = None`
   - Verify facility updated with analysis result

9. **Invalid Provider**
   - Initialize with `provider="invalid"`
   - Verify raises ValueError

10. **Review Limit**
    - Input: 30 reviews
    - Verify only first 20 are used

### Integration Tests (Real LLM - Optional)

Mark with `@pytest.mark.integration`:

1. **Real OpenAI API Call**
   - Use real reviews mentioning "indoor courts"
   - Verify correct classification

2. **Real Anthropic API Call**
   - Use real reviews mentioning "outdoor courts"
   - Verify correct classification

---

## Implementation Notes

### Base LLM Enricher (Abstract Class)

Create `src/enrichers/base_llm.py` with abstract base class:

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from ..models.facility import Facility

class BaseLLMEnricher(ABC):
    """Abstract base class for LLM-based enrichers."""
    
    @abstractmethod
    def analyze_reviews(self, reviews: List[str]) -> Optional[str]:
        """Analyze reviews and return result."""
        pass
    
    @abstractmethod
    def enrich_facility(self, facility: Facility, reviews: List[str]) -> Facility:
        """Enrich facility with analysis result."""
        pass
```

### Prompt Template

```python
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
```

### Environment Variables

Add to `.env.example`:
```bash
# LLM API Keys (optional - for indoor/outdoor analysis)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
LLM_PROVIDER=openai  # or 'anthropic'
LLM_MODEL=gpt-4o-mini  # or 'claude-3-5-haiku-20241022'
```

### Configuration Settings

Add to `src/config.py`:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # LLM Configuration (optional)
    openai_api_key: Optional[str] = Field(None, env='OPENAI_API_KEY')
    anthropic_api_key: Optional[str] = Field(None, env='ANTHROPIC_API_KEY')
    llm_provider: str = Field("openai", env='LLM_PROVIDER')
    llm_model: str = Field("gpt-4o-mini", env='LLM_MODEL')
```

### Cost Estimation

Approximate costs per facility (20 reviews):
- **OpenAI gpt-4o-mini**: ~$0.0001-0.0003 per facility
- **Anthropic claude-3-5-haiku**: ~$0.0001-0.0003 per facility

For 100 facilities: ~$0.01-0.03 total

---

## Dependencies

This story depends on the following being completed first:

- **Story 0.1**: `Facility` model must exist with `indoor_outdoor` field
- **Story 1.2**: `ReviewCollector` must be able to fetch reviews

---

## Success Criteria

✅ Analyzer can be instantiated with both OpenAI and Anthropic providers  
✅ Returns correct court type with high confidence (≥0.6)  
✅ Returns None for low confidence or unknown  
✅ Only enriches facilities that don't already have `indoor_outdoor` set  
✅ Gracefully handles API errors without crashing  
✅ Tests pass with 100% coverage for analyzer logic  
✅ Cost per facility is < $0.001  
✅ Code is type-safe and well-documented

---

## Optional Enhancements (Future)

- Cache results by place_id to avoid re-analyzing
- Support additional providers (Google Gemini, etc.)
- Multi-field enrichment (e.g., number of courts, amenities)
- Batch processing for cost optimization
- Fallback to keyword matching if LLM unavailable


