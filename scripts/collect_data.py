#!/usr/bin/env python3
"""
Data Collection CLI Script.

This script orchestrates the entire data collection pipeline for padel facilities,
including:
1. Google Places API data collection
2. Optional review collection
3. Optional LLM-based enrichment (indoor/outdoor analysis)
4. Data cleaning and validation
5. Deduplication
6. CSV export

Exit Codes:
    0: Success - All stages completed successfully
    1: Configuration Error - Missing API key or invalid configuration
    2: Data Collection Failed - Error during Google Places API calls
    3: Data Processing Failed - Error during cleaning or deduplication

Usage:
    python scripts/collect_data.py [OPTIONS]

Examples:
    # Basic collection (no enrichment)
    python scripts/collect_data.py

    # With reviews
    python scripts/collect_data.py --with-reviews

    # Full enrichment (reviews + LLM)
    python scripts/collect_data.py --with-reviews --enrich-indoor-outdoor

    # Custom region and output
    python scripts/collect_data.py --region "Lagos, Portugal" --output data/raw/lagos.csv
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.google_places import GooglePlacesCollector
from src.collectors.review_collector import ReviewCollector
from src.config import settings
from src.enrichers.indoor_outdoor_analyzer import IndoorOutdoorAnalyzer
from src.models.facility import Facility
from src.processors.cleaner import DataCleaner
from src.processors.deduplicator import Deduplicator

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# Exit Codes
# ============================================================================

EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 1
EXIT_COLLECTION_FAILED = 2
EXIT_PROCESSING_FAILED = 3


# ============================================================================
# Argument Parsing
# ============================================================================


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: List of argument strings (None = use sys.argv)

    Returns:
        Parsed arguments namespace

    Example:
        >>> args = parse_arguments(["--region", "Lagos, Portugal"])
        >>> print(args.region)
        Lagos, Portugal
    """
    parser = argparse.ArgumentParser(
        description="Collect padel facility data from Google Places API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/collect_data.py
  python scripts/collect_data.py --with-reviews
  python scripts/collect_data.py --with-reviews --enrich-indoor-outdoor
  python scripts/collect_data.py --region "Lagos, Portugal" --output data/raw/lagos.csv
        """,
    )

    parser.add_argument(
        "--region",
        default="Algarve, Portugal",
        help="Geographic region to search (default: Algarve, Portugal)",
    )

    parser.add_argument(
        "--with-reviews",
        action="store_true",
        help="Fetch reviews for each facility (default: False)",
    )

    parser.add_argument(
        "--enrich-indoor-outdoor",
        action="store_true",
        help="Use LLM to analyze indoor/outdoor status (default: False)",
    )

    parser.add_argument(
        "--llm-provider",
        default="openai",
        choices=["openai", "anthropic"],
        help="LLM provider to use (default: openai)",
    )

    parser.add_argument(
        "--llm-model",
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)",
    )

    parser.add_argument(
        "--output",
        default="data/raw/facilities.csv",
        help="Output file path (default: data/raw/facilities.csv)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (default: False)",
    )

    return parser.parse_args(args)


# ============================================================================
# Configuration & Validation
# ============================================================================


def validate_configuration(args: argparse.Namespace) -> bool:
    """
    Validate configuration and required API keys.

    Checks that GOOGLE_API_KEY is present and valid. Also validates
    that if LLM enrichment is requested, the appropriate LLM API key
    is available.

    Args:
        args: Parsed command-line arguments

    Returns:
        True if configuration is valid, False otherwise

    Side Effects:
        Prints error messages to stderr if validation fails
    """
    # Check Google API key
    try:
        google_api_key = settings.google_api_key
        if not google_api_key or len(google_api_key.strip()) == 0:
            print("❌ Error: GOOGLE_API_KEY environment variable is not set", file=sys.stderr)
            print("\nPlease set your Google API key:", file=sys.stderr)
            print("  export GOOGLE_API_KEY='your-api-key-here'", file=sys.stderr)
            print("\nOr add it to your .env file:", file=sys.stderr)
            print("  GOOGLE_API_KEY=your-api-key-here", file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ Error: Failed to load GOOGLE_API_KEY: {e}", file=sys.stderr)
        print("\nPlease set your Google API key:", file=sys.stderr)
        print("  export GOOGLE_API_KEY='your-api-key-here'", file=sys.stderr)
        print("\nOr add it to your .env file:", file=sys.stderr)
        print("  GOOGLE_API_KEY=your-api-key-here", file=sys.stderr)
        return False

    # Check LLM API key if enrichment is requested
    if args.enrich_indoor_outdoor:
        if args.llm_provider == "openai":
            openai_key = settings.openai_api_key
            if not openai_key or len(openai_key.strip()) == 0:
                print(
                    "❌ Error: OPENAI_API_KEY required for --enrich-indoor-outdoor",
                    file=sys.stderr,
                )
                print("\nPlease set your OpenAI API key:", file=sys.stderr)
                print("  export OPENAI_API_KEY='your-api-key-here'", file=sys.stderr)
                return False
        elif args.llm_provider == "anthropic":
            anthropic_key = settings.anthropic_api_key
            if not anthropic_key or len(anthropic_key.strip()) == 0:
                print(
                    "❌ Error: ANTHROPIC_API_KEY required for --enrich-indoor-outdoor",
                    file=sys.stderr,
                )
                print("\nPlease set your Anthropic API key:", file=sys.stderr)
                print("  export ANTHROPIC_API_KEY='your-api-key-here'", file=sys.stderr)
                return False

    return True


def setup_directories(output_path: Path) -> None:
    """
    Create necessary directories for output and cache.

    Creates:
    - Parent directory of output_path (for CSV file)
    - Cache directory (if cache is enabled)

    Args:
        output_path: Path to output CSV file

    Side Effects:
        Creates directories on filesystem
    """
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create cache directory
    if settings.cache_enabled and settings.cache_dir:
        settings.cache_dir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Progress Logging (DRY)
# ============================================================================


def print_stage(stage_num: int, message: str) -> None:
    """
    Print a formatted stage header.

    Args:
        stage_num: Stage number (1-7)
        message: Stage description message

    Example:
        >>> print_stage(1, "Initializing")
        1. Initializing...
    """
    print(f"\n{stage_num}. {message}...")


def print_banner() -> None:
    """Print opening banner for the script."""
    print("\n" + "=" * 60)
    print("🎾 Starting Algarve Padel Field Data Collection")
    print("=" * 60)


def print_summary(facilities: List[Facility], execution_time: float) -> None:
    """
    Print summary statistics after successful completion.

    Args:
        facilities: List of collected facilities
        execution_time: Total execution time in seconds

    Example:
        >>> print_summary(facilities, 125.5)
        ✅ Data collection complete!
           Total facilities: 48
           Cities covered: 12
           Execution time: 2m 5s
    """
    # Calculate statistics
    total_facilities = len(facilities)
    unique_cities = len(set(f.city for f in facilities))

    # Format execution time
    minutes = int(execution_time // 60)
    seconds = int(execution_time % 60)
    if minutes > 0:
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = f"{seconds}s"

    print("\n" + "=" * 60)
    print("✅ Data collection complete!")
    print(f"   Total facilities: {total_facilities}")
    print(f"   Cities covered: {unique_cities}")
    print(f"   Execution time: {time_str}")
    print("=" * 60)
    print("\nNext step: python scripts/process_data.py")


# ============================================================================
# Pipeline Stages
# ============================================================================


def collect_facilities(
    collector: GooglePlacesCollector, region: str
) -> List[Facility]:
    """
    Stage 2: Collect facilities from Google Places API.

    Args:
        collector: Initialized GooglePlacesCollector
        region: Geographic region to search

    Returns:
        List of collected Facility objects

    Raises:
        Exception: If data collection fails completely
    """
    facilities = collector.search_padel_facilities(region)
    print(f"   ✓ Found {len(facilities)} facilities")
    return facilities


def collect_reviews(
    collector: ReviewCollector, facilities: List[Facility]
) -> Dict[str, List[str]]:
    """
    Stage 3: Collect reviews for each facility (optional).

    Args:
        collector: Initialized ReviewCollector
        facilities: List of facilities to collect reviews for

    Returns:
        Dictionary mapping place_id to list of review texts

    Note:
        Errors for individual facilities are logged but don't stop processing
    """
    reviews_dict: Dict[str, List[str]] = {}
    total = len(facilities)

    for idx, facility in enumerate(facilities, 1):
        try:
            reviews = collector.get_reviews(facility.place_id)
            reviews_dict[facility.place_id] = reviews

            # Progress indicator
            if idx % 10 == 0 or idx == total:
                print(f"   Fetching reviews: {idx}/{total}...", end="\r")

        except Exception as e:
            logger.warning(
                f"Failed to fetch reviews for {facility.place_id}: {e}"
            )
            reviews_dict[facility.place_id] = []

    print(f"   ✓ Collected reviews for {len(reviews_dict)} facilities")
    return reviews_dict


def enrich_with_llm(
    analyzer: IndoorOutdoorAnalyzer,
    facilities: List[Facility],
    reviews_dict: Dict[str, List[str]],
) -> List[Facility]:
    """
    Stage 4: Enrich facilities with LLM analysis (optional).

    Uses LLM to analyze reviews and determine indoor/outdoor status.

    Args:
        analyzer: Initialized IndoorOutdoorAnalyzer
        facilities: List of facilities to enrich
        reviews_dict: Dictionary of reviews keyed by place_id

    Returns:
        List of enriched Facility objects

    Note:
        Errors for individual facilities are logged but don't stop processing
    """
    enriched_facilities: List[Facility] = []
    total = len(facilities)

    for idx, facility in enumerate(facilities, 1):
        try:
            reviews = reviews_dict.get(facility.place_id, [])
            enriched = analyzer.enrich_facility(facility, reviews)
            enriched_facilities.append(enriched)

            # Progress indicator
            if idx % 5 == 0 or idx == total:
                print(f"   Analyzing: {idx}/{total}...", end="\r")

        except Exception as e:
            logger.warning(
                f"Failed to enrich {facility.place_id}: {e}"
            )
            enriched_facilities.append(facility)

    print(f"   ✓ Analyzed {len(enriched_facilities)} facilities")
    return enriched_facilities


def clean_facilities(facilities: List[Facility]) -> List[Facility]:
    """
    Stage 5: Clean and validate facility data.

    Removes facilities with:
    - Invalid coordinates (outside Algarve bounds)
    - Missing city information

    Args:
        facilities: List of raw facilities

    Returns:
        List of cleaned facilities

    Raises:
        Exception: If cleaning process fails
    """
    initial_count = len(facilities)
    cleaned = DataCleaner.clean_facilities(facilities)
    removed = initial_count - len(cleaned)

    print(f"   ✓ {len(cleaned)} facilities after cleaning ({removed} removed)")
    return cleaned


def deduplicate_facilities(facilities: List[Facility]) -> List[Facility]:
    """
    Stage 6: Remove duplicate facilities.

    Uses both exact place_id matching and fuzzy name+location matching.

    Args:
        facilities: List of cleaned facilities

    Returns:
        List of unique facilities

    Raises:
        Exception: If deduplication fails
    """
    initial_count = len(facilities)
    unique = Deduplicator.deduplicate(facilities)
    removed = initial_count - len(unique)

    print(f"   ✓ {len(unique)} unique facilities ({removed} duplicates removed)")
    return unique


def save_to_csv(facilities: List[Facility], output_path: Path) -> None:
    """
    Stage 7: Save facilities to CSV file.

    Converts Facility objects to DataFrame and saves to CSV with proper
    formatting. Ensures the output directory exists.

    Args:
        output_path: Path to output CSV file
        facilities: List of facilities to save

    Raises:
        Exception: If saving fails (permissions, disk space, etc.)
    """
    # Convert to DataFrame
    df = DataCleaner.to_dataframe(facilities)

    # Save to CSV
    df.to_csv(output_path, index=False)

    print(f"   ✓ Saved to: {output_path}")


# ============================================================================
# Main Function
# ============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for data collection CLI.

    Orchestrates the entire data collection pipeline with proper error
    handling and exit codes.

    Args:
        argv: Command-line arguments (None = use sys.argv)

    Returns:
        Exit code:
        - 0: Success
        - 1: Configuration error
        - 2: Data collection failed
        - 3: Data processing failed

    Example:
        >>> exit_code = main(["--region", "Lagos, Portugal"])
        >>> sys.exit(exit_code)
    """
    start_time = time.time()

    # Parse arguments
    args = parse_arguments(argv)

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    # Print banner
    print_banner()

    # Stage 1: Validate configuration
    print_stage(1, "Validating configuration")
    if not validate_configuration(args):
        return EXIT_CONFIG_ERROR

    print("   ✓ API key validated")

    # Setup directories
    output_path = Path(args.output)
    setup_directories(output_path)
    print(f"   ✓ Output directory: {output_path.parent}")

    try:
        # Stage 2: Collect facilities
        print_stage(2, f"Searching for padel facilities in {args.region}")
        collector = GooglePlacesCollector(api_key=settings.google_api_key)

        try:
            facilities = collect_facilities(collector, args.region)
            if len(facilities) == 0:
                print("   ⚠️  No facilities found", file=sys.stderr)
                return EXIT_COLLECTION_FAILED
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            print(f"   ❌ Failed to collect data: {e}", file=sys.stderr)
            return EXIT_COLLECTION_FAILED

        # Stage 3: Collect reviews (optional)
        reviews_dict: Dict[str, List[str]] = {}
        if args.with_reviews:
            print_stage(3, "Fetching reviews")
            review_collector = ReviewCollector(api_key=settings.google_api_key)
            reviews_dict = collect_reviews(review_collector, facilities)

        # Stage 4: LLM enrichment (optional)
        if args.enrich_indoor_outdoor:
            if not args.with_reviews:
                print(
                    "   ⚠️  Warning: --enrich-indoor-outdoor requires --with-reviews, skipping enrichment",
                    file=sys.stderr,
                )
            else:
                print_stage(4, "Analyzing indoor/outdoor status with LLM")
                analyzer = IndoorOutdoorAnalyzer(
                    provider=args.llm_provider,
                    model=args.llm_model,
                )
                facilities = enrich_with_llm(analyzer, facilities, reviews_dict)

        # Stage 5: Clean data
        stage_num = 5 if args.with_reviews else 3
        print_stage(stage_num, "Cleaning data")
        try:
            facilities = clean_facilities(facilities)
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            print(f"   ❌ Failed to clean data: {e}", file=sys.stderr)
            return EXIT_PROCESSING_FAILED

        # Stage 6: Remove duplicates
        stage_num += 1
        print_stage(stage_num, "Removing duplicates")
        try:
            facilities = deduplicate_facilities(facilities)
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            print(f"   ❌ Failed to deduplicate: {e}", file=sys.stderr)
            return EXIT_PROCESSING_FAILED

        # Stage 7: Save results
        stage_num += 1
        print_stage(stage_num, "Saving data")
        try:
            save_to_csv(facilities, output_path)
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            print(f"   ❌ Failed to save data: {e}", file=sys.stderr)
            return EXIT_PROCESSING_FAILED

        # Print summary
        execution_time = time.time() - start_time
        print_summary(facilities, execution_time)

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user", file=sys.stderr)
        return EXIT_PROCESSING_FAILED
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        return EXIT_PROCESSING_FAILED


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())

