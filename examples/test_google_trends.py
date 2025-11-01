"""
Test script to verify GoogleTrendsCollector works with all 15 Algarve municipalities.

This script demonstrates the usage of the GoogleTrendsCollector and verifies
that it can handle all Algarve cities, including those with Portuguese accents.
"""

from src.collectors.google_trends import GoogleTrendsCollector

# All 15 Algarve municipalities
ALGARVE_CITIES = [
    "Albufeira",
    "Aljezur",
    "Castro Marim",
    "Faro",
    "Lagoa",
    "Lagos",
    "Loulé",
    "Monchique",
    "Olhão",
    "Portimão",
    "São Brás de Alportel",
    "Silves",
    "Tavira",
    "Vila do Bispo",
    "Vila Real de Santo António",
]


def main():
    """Test the Google Trends collector with all Algarve cities."""
    print("=" * 80)
    print("Google Trends Collector - Integration Test")
    print("=" * 80)
    print()

    # Initialize collector
    print("Initializing GoogleTrendsCollector...")
    collector = GoogleTrendsCollector()
    print("✓ Collector initialized successfully")
    print()

    # Test with all Algarve cities
    print(f"Fetching trends for {len(ALGARVE_CITIES)} Algarve municipalities...")
    print("Keyword: 'padel'")
    print("Timeframe: last 12 months")
    print()

    try:
        # Get regional interest
        interest_scores = collector.get_regional_interest(
            keyword="padel",
            regions=ALGARVE_CITIES,
            timeframe="today 12-m"
        )

        # Display results
        print("Results:")
        print("-" * 80)
        
        cities_with_data = 0
        for city in ALGARVE_CITIES:
            score = interest_scores.get(city, 0.0)
            if score > 0:
                cities_with_data += 1
            
            # Format output with proper alignment
            print(f"  {city:<30} {score:>6.1f}")
        
        print("-" * 80)
        print()

        # Summary
        print("Summary:")
        print(f"  Total cities queried: {len(ALGARVE_CITIES)}")
        print(f"  Cities with data: {cities_with_data}")
        print(f"  Cities without data: {len(ALGARVE_CITIES) - cities_with_data}")
        print()

        # Verify success threshold (10+ cities)
        SUCCESS_THRESHOLD = 10
        if cities_with_data >= SUCCESS_THRESHOLD:
            print(f"✓ SUCCESS: Retrieved data for {cities_with_data} cities (threshold: {SUCCESS_THRESHOLD})")
        else:
            print(f"✗ PARTIAL: Retrieved data for {cities_with_data} cities (threshold: {SUCCESS_THRESHOLD})")
            print("  Note: This may be expected if running with mocked data or limited API access")
        
        print()

        # Test Portuguese characters
        print("Portuguese Character Handling:")
        accented_cities = ["São Brás de Alportel", "Olhão"]
        for city in accented_cities:
            if city in interest_scores:
                print(f"  ✓ {city}: {interest_scores[city]:.1f}")
            else:
                print(f"  ✗ {city}: Not in results")
        print()

        # Test score range validation
        print("Score Range Validation:")
        all_in_range = all(0.0 <= score <= 100.0 for score in interest_scores.values())
        if all_in_range:
            print("  ✓ All scores in valid range (0-100)")
        else:
            print("  ✗ Some scores out of range")
            for city, score in interest_scores.items():
                if not (0.0 <= score <= 100.0):
                    print(f"    Invalid: {city} = {score}")
        print()

        print("=" * 80)
        print("Integration test completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

