"""
Example usage of the IndoorOutdoorAnalyzer.

This script demonstrates how to use the LLM-based indoor/outdoor analyzer
to enrich facility data with court type information.
"""

from src.enrichers import IndoorOutdoorAnalyzer
from src.models import Facility
from src.config import settings


def example_with_openai():
    """Example using OpenAI provider."""
    print("\n=== OpenAI Example ===")
    
    # Initialize analyzer with OpenAI (uses settings from .env by default)
    analyzer = IndoorOutdoorAnalyzer(provider="openai", model="gpt-4o-mini")
    
    # Sample reviews mentioning indoor courts
    reviews = [
        "Love the indoor courts! Perfect for playing in any weather.",
        "Climate controlled facility is amazing, never too hot or cold.",
        "The covered courts allow us to play year-round."
    ]
    
    # Analyze reviews
    result = analyzer.analyze_reviews(reviews)
    print(f"Analysis result: {result}")
    
    # Enrich a facility
    facility = Facility(
        place_id="example_123",
        name="Padel Club Example",
        address="Example Street 123",
        city="Lisbon",
        latitude=38.7223,
        longitude=-9.1393,
        rating=4.5,
        review_count=150
    )
    
    enriched_facility = analyzer.enrich_facility(facility, reviews)
    print(f"Facility indoor_outdoor: {enriched_facility.indoor_outdoor}")


def example_with_anthropic():
    """Example using Anthropic provider."""
    print("\n=== Anthropic Example ===")
    
    # Initialize analyzer with Anthropic
    analyzer = IndoorOutdoorAnalyzer(
        provider="anthropic",
        model="claude-3-5-haiku-20241022"
    )
    
    # Sample reviews mentioning both court types
    reviews = [
        "Great facility with both indoor and outdoor courts.",
        "Play inside when it rains, outside when sunny.",
        "Love having the option between covered and open-air courts."
    ]
    
    # Analyze reviews
    result = analyzer.analyze_reviews(reviews)
    print(f"Analysis result: {result}")


def example_cost_efficient():
    """Example demonstrating cost optimization features."""
    print("\n=== Cost Optimization Example ===")
    
    analyzer = IndoorOutdoorAnalyzer()
    
    # With many reviews, only first 20 are used
    many_reviews = [f"Review {i} about outdoor courts" for i in range(30)]
    print(f"Input: {len(many_reviews)} reviews")
    
    result = analyzer.analyze_reviews(many_reviews)
    print(f"Analysis result: {result}")
    print("Note: Only first 20 reviews were analyzed (check logs for cost)")
    
    # Skip analysis if facility already has indoor_outdoor set
    facility = Facility(
        place_id="example_456",
        name="Existing Facility",
        address="Test Address",
        city="Porto",
        latitude=41.1579,
        longitude=-8.6291,
        indoor_outdoor="outdoor"  # Already set
    )
    
    enriched = analyzer.enrich_facility(facility, many_reviews)
    print(f"Facility unchanged: {enriched.indoor_outdoor}")
    print("Note: No API call was made (already set)")


def main():
    """Run all examples."""
    print("IndoorOutdoorAnalyzer Examples")
    print("=" * 50)
    
    # Check if API keys are available
    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("\nWARNING: No API keys found in environment.")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env to run examples.")
        print("\nShowing example code structure only...\n")
        return
    
    try:
        if settings.openai_api_key:
            example_with_openai()
        
        if settings.anthropic_api_key:
            example_with_anthropic()
        
        if settings.openai_api_key or settings.anthropic_api_key:
            example_cost_efficient()
            
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure your API keys are valid and you have network access.")


if __name__ == "__main__":
    main()

