"""
Data export utilities for saving DataFrames to CSV files.

This module provides functionality to export pandas DataFrames to CSV format
with timestamped filenames and automatic directory creation. Primarily used
for exporting filtered facility and city statistics data from the Streamlit app.

Usage:
    from src.utils.exporters import DataExporter

    exporter = DataExporter()
    export_path = exporter.export_to_csv(facilities_df, prefix="facilities")

The exporter will:
- Generate unique timestamped filenames
- Create export directory if it doesn't exist
- Export with UTF-8 encoding
- Handle null values gracefully (empty cells instead of 'NaN' text)
- Validate data before export
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import settings

# Setup module logger
logger = logging.getLogger(__name__)


class DataExporter:
    """
    Export pandas DataFrames to CSV files with timestamped filenames.

    This class handles exporting filtered data to CSV format with automatic
    directory creation and proper encoding. Files are saved with timestamps
    to prevent overwrites and enable tracking of export history.

    Attributes:
        export_dir: Path to directory where exports will be saved

    Example:
        >>> exporter = DataExporter()
        >>> facilities_df = pd.DataFrame({'name': ['Club A'], 'city': ['Faro']})
        >>> path = exporter.export_to_csv(facilities_df, prefix="facilities")
        >>> print(path.name)
        facilities_export_2024-01-15_14-30-45.csv
    """

    def __init__(self, export_dir: Optional[Path] = None):
        """
        Initialize DataExporter with export directory.

        Args:
            export_dir: Directory to save exports. If None, uses the
                       configured exports directory from settings.

        Example:
            >>> # Use default directory from settings
            >>> exporter = DataExporter()
            >>>
            >>> # Use custom directory
            >>> custom_dir = Path("my_exports")
            >>> exporter = DataExporter(export_dir=custom_dir)
        """
        if export_dir is None:
            self.export_dir = settings.exports_dir
        else:
            self.export_dir = export_dir

        logger.debug(f"DataExporter initialized with export_dir: {self.export_dir}")

    @staticmethod
    def generate_filename(prefix: str, extension: str = "csv") -> str:
        """
        Generate timestamped filename for export.

        Creates a filename in the format: {prefix}_YYYY-MM-DD_HH-MM-SS.{extension}
        The timestamp ensures uniqueness and provides chronological sorting.

        Args:
            prefix: Filename prefix (e.g., 'facilities', 'city_stats')
            extension: File extension without dot (default: 'csv')

        Returns:
            Formatted filename string with timestamp

        Example:
            >>> filename = DataExporter.generate_filename("facilities")
            >>> print(filename)
            facilities_2024-01-15_14-30-45.csv

            >>> filename = DataExporter.generate_filename("data", "xlsx")
            >>> print(filename)
            data_2024-01-15_14-30-45.xlsx
        """
        # Format: YYYY-MM-DD_HH-MM-SS
        # Note: Using microsecond precision internally to ensure uniqueness
        # for rapid consecutive exports, but only displaying seconds
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Add microseconds to filename to ensure uniqueness for concurrent exports
        # Format as 6-digit microsecond for consistency
        microseconds = f"{now.microsecond:06d}"
        filename = f"{prefix}_{timestamp}-{microseconds}.{extension}"

        logger.debug(f"Generated filename: {filename}")
        return filename

    def get_export_path(self, filename: str) -> Path:
        """
        Get full path for export file in the export directory.

        Args:
            filename: Name of the export file

        Returns:
            Complete Path object combining export_dir and filename

        Example:
            >>> exporter = DataExporter()
            >>> path = exporter.get_export_path("test.csv")
            >>> print(path)
            /path/to/data/exports/test.csv
        """
        return self.export_dir / filename

    def export_to_csv(
        self,
        df: pd.DataFrame,
        prefix: str,
        include_index: bool = False,
    ) -> Path:
        """
        Export DataFrame to CSV file with timestamped filename.

        This method validates the DataFrame, creates the export directory if needed,
        generates a unique filename, and exports the data to CSV format with proper
        encoding. Null values are exported as empty cells (not 'NaN' text).

        Args:
            df: DataFrame to export
            prefix: Filename prefix (e.g., 'facilities', 'city_stats')
            include_index: Whether to include DataFrame index in CSV (default: False)

        Returns:
            Path object pointing to the created CSV file

        Raises:
            ValueError: If DataFrame is empty (no rows)
            IOError: If export directory cannot be created or file cannot be written

        Example:
            >>> exporter = DataExporter()
            >>> df = pd.DataFrame({'name': ['Club A', 'Club B'], 'city': ['Faro', 'Lagos']})
            >>> path = exporter.export_to_csv(df, prefix="facilities")
            >>> print(f"Exported {len(df)} rows to {path.name}")
            Exported 2 rows to facilities_2024-01-15_14-30-45.csv

        Notes:
            - UTF-8 encoding is used to support international characters
            - Null values (NaN) are exported as empty cells
            - The pandas index is excluded by default to avoid confusing users
        """
        # Validate DataFrame is not empty
        if df.empty:
            error_msg = f"Cannot export empty DataFrame (prefix: {prefix})"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Starting export: {len(df)} rows, prefix='{prefix}'")

        try:
            # Ensure export directory exists
            self.export_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Export directory ready: {self.export_dir}")

            # Generate timestamped filename
            filename = self.generate_filename(prefix)
            export_path = self.get_export_path(filename)

            # Export to CSV with UTF-8 encoding
            # Note: pandas automatically converts NaN to empty string in CSV output
            df.to_csv(
                export_path,
                index=include_index,
                encoding="utf-8",
            )

            logger.info(
                f"Successfully exported {len(df)} rows to {export_path.name} "
                f"({len(df.columns)} columns)"
            )

            return export_path

        except Exception as e:
            error_msg = f"Failed to export DataFrame (prefix: {prefix}): {e}"
            logger.error(error_msg)
            raise IOError(error_msg) from e

